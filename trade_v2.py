# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import os
import random
import time

# import custom configs and utils
from accounts.w1_if_getAccountInformation import w1_if_getAccountInformation
from config import (
    IBKR_ORDER_QUANTITY_LIMIT,
    PROGRAM_VERSION,
    QUANTITY,
    ROOT_PATH,
    TRADE_ACQUISITION_DIVERSITY,
    TRADE_ACQUISITION_PORT_OPT_MIN_COUNT,
    TRADE_LIMIT_ORDER_GAP,
    TRADE_RECENT_DATA_CHUNK_RL_INFERENCE,
    TRADE_RL_EVALUATION_SAMPLE_FACTOR,
    TRADE_STRATEGY_COMP_WEIGHTS,
    TRADE_STRATEGY_COMP_THRESHOLD,
    WAIT_TIME_TEN
)
from config_enums import ActionSignal, OperationPhase
from data.w1_if_getHistoricalData import w1_if_getHistoricalDataInThreadsMain
from data.w1_if_getLiveData import w1_if_getLiveData
from data.w1_if_getTickers import w1_if_getTickers
from data.w1_refineTickers_FavourableBuyCondition import w1_refineTickers_FavourableBuyCondition
from evaluate import inferLastActionToTrade
from orders.w1_if_placeOrder import w1_if_placeOrder
from reports.w1_generateAnalysisReport import w1_generateAnalysisReport
from strategies.w1_generateTradeSignal import w1_generateTradeSignal_Strategy_Comprehensive
from utils.w2_calculatePositionSize import w2_calculatePositionSize
from utils.w2_clearPreviousSessionData import w2_clearPreviousSessionData, w2_stashAway
from utils.w2_generateDateStringYYYYMMDD import w2_generateDateStringYYYYMMDD
from utils.w2_log import CustomLogger
from utils.w2_manageTrade import w2_manageTrade
from utils.w2_optimizePortfolio import w2_optimizePortfolio
from utils.w2_performHDF5Ops import w2_readDataFromHDF5
from utils.w2_refreshTransactionMemories import w2_refreshTransactionMemories
from utils.w2_updateLedgerEntries import w2_updateLedgerEntries


def trade(
    debug_override_on = False,
    limit_orders_on = False,
    end_at_market_close_on = True,
    simulated_on = True,
    scanned_tickers_dir_str = 'data/scans/',
    scanned_file_name_str = 'favourable_buy_scan_list.h5'
):
    """
        description:
            Executes the main trading loop for the Helios strategy. The function manages
            the day-to-day execution lifecycle of the trading bot, including initializing
            logging and session state, determining active and passive trading pools,
            evaluating market conditions, and submitting or adjusting orders as the
            strategy transitions through operational phases.
        args:
            debug_override_on: bool, default False
                Enables a debug-only override path for testing or forcing a specific
                execution flow without relying on the normal trading logic.
            limit_orders_on: bool, default False
                When True, instructs the system to place limit orders rather than market
                orders where applicable.
            end_at_market_close_on: bool, default True
                If True, the strategy will prepare to unwind or exit positions near the
                end of the trading session.
            simulated_on: bool, default True
                Determines whether the function operates in simulated/paper-trading mode
                or in a live-trading environment.
            scanned_tickers_dir_str: str, default 'data/scans/'
                Directory containing precomputed scan outputs used to identify candidate
                tickers for acquisition.
            scanned_file_name_str: str, default 'favourable_buy_scan_list.h5'
                File name of the scan artifact that contains the filtered ticker list.
        returns:
            None
                The function runs an ongoing trading loop and manages execution state
                internally rather than returning a result object.
        references:
            None
    """
    # initialize logger
    logger_obj = None

    # initialize lock booleans
    lock_logger_init_on = False
    lock_passive_pool_determination_on = False

    # initialize sets
    active_pool_str_set = set()
    intermediate_pool_str_set = set()
    passive_pool_str_set = set()
    acquire_set = set()
    dispose_set = set()

    # initialize counts
    count_ibkr_faults = 0
    debug_override_cycle_count_int = 0

    # start infinite loop
    while True:
        # invoke trade manager
        phase_enum, immediate_liquidate_on, acquisition_preference_list, disposal_preference_list, debug_override_cycle_count_int = w2_manageTrade(
            debug_override_on = debug_override_on,
            debug_override_cycle_count_int = debug_override_cycle_count_int
        )

        if phase_enum != OperationPhase.PHASE_WAIT:

            # ==== ==== ==== ==== ==== ==== ==== ==== INITIALIZE
            # initialize logger for a new session nor a new day, enable/disable locks
            if not lock_logger_init_on or not os.path.exists(
                os.path.join(
                    ROOT_PATH, 'logs', w2_generateDateStringYYYYMMDD() + '.log'
                )
            ):
                # initialize logger object again (necessary for continuous run)
                logger_obj = None

                # initialize custom logger
                logger_cls = CustomLogger(debug_on = False)
                logger_obj = logger_cls.w2_generateCustomLogger()
                logger_obj.info(f'Started Helios v{PROGRAM_VERSION}...')

                # clear previous day session data
                w2_clearPreviousSessionData(
                    remove_daily_on = True,
                    remove_hourly_on = True,
                    remove_minutely_on = True,
                    remove_features_on = True,
                    remove_plots_on = True
                )

                # adjust locks
                lock_next_day_preparation_on = False
                lock_passive_pool_determination_on = False

                # turn lock on for execution once a day
                lock_logger_init_on = True

            # ==== ==== ==== ==== ==== ==== ==== ==== INITIALIZE

            # ==== ==== ==== ==== ==== ==== ==== ==== DEBUG LOG
            if debug_override_on:
                # log
                logger_obj.info(
                    f'[DEBUG] Started attempt #{debug_override_cycle_count_int} in debug mode...'
                )
            # ==== ==== ==== ==== ==== ==== ==== ==== DEBUG LOG

            # ==== ==== ==== ==== ==== ==== ==== ==== LIQUIDATE
            if immediate_liquidate_on:
                # derive update portfolio information
                portfolio_information_dict = {}
                while not portfolio_information_dict:
                    try:
                        _, portfolio_information_dict = w1_if_getAccountInformation(
                            simulated_on = simulated_on
                        )
                    except KeyError:
                        # log
                        logger_obj.warning(
                            'Handled a KeyError exception while requesting account/portfolio information, retrying...'
                        )
                        count_ibkr_faults += 1

                # liquidate all securities
                for security_name_str in list(portfolio_information_dict.keys()):
                    if int(portfolio_information_dict[security_name_str]['quantity_int']) != 0:
                        # transmit sell request
                        _ = w1_if_placeOrder(
                            ticker_str = security_name_str,
                            primary_exchange_str = '',
                            action_type_str = 'SELL',
                            quantity_int = int(portfolio_information_dict[security_name_str]['quantity_int']),
                            order_type_str = 'MKT',
                            limit_order_price_flt = 0.0,
                            tif_str = 'DAY',
                            simulated_on = simulated_on
                        )

                # generate temporary dictionary and update ledger
                temp_dict = {
                    'entry_date_str': [w2_generateDateStringYYYYMMDD()],
                    'transaction_str': [''],
                    'security_str': [''],
                    'quantity_int': [''],
                    'acquisition_price_flt': [''],
                    'disposal_price_flt': [''],
                    'buying_power_flt': [''],
                    'portfolio_value_flt': ['']
                }
                w2_updateLedgerEntries(
                    data_dict = temp_dict,
                    erase_on = True,
                    simulated_on = simulated_on
                )

            # ==== ==== ==== ==== ==== ==== ==== ==== LIQUIDATE

            # ==== ==== ==== ==== ==== ==== ==== ==== EXTRACT ACCOUNT/PORTFOLIO INFO
            # derive updated account and portfolio information right before sell order
            account_information_dict = None
            portfolio_information_dict = None
            while not account_information_dict:
                try:
                    account_information_dict, portfolio_information_dict = w1_if_getAccountInformation(
                        simulated_on = simulated_on
                    )
                except KeyError:
                    # log
                    logger_obj.warning(
                        'Handled a KeyError exception while requesting account/portfolio information, retrying...'
                    )
                    count_ibkr_faults += 1

            # ==== ==== ==== ==== ==== ==== ==== ==== EXTRACT ACCOUNT/PORTFOLIO INFO

            # ==== ==== ==== ==== ==== ==== ==== ==== STRATEGIZE
            if phase_enum == OperationPhase.PHASE_STRATEGIZE:

                # passive pool set update - append potential securities to passive pool set
                if not lock_passive_pool_determination_on:
                    # extract passive tickers queue from previously-completed market scan
                    for security_name_str in w2_readDataFromHDF5(
                            save_path_str = ROOT_PATH + scanned_tickers_dir_str + scanned_file_name_str
                    ):
                        passive_pool_str_set.add(security_name_str)

                    # filter out tickers based on price and whether they can be bought based on desired diversity
                    temp_list = []
                    acquisition_price_threshold_flt = account_information_dict["buying_power_flt"]/TRADE_ACQUISITION_DIVERSITY
                    
                    for security_name_str in passive_pool_str_set:
                        # NOTE: This exceptions handling was included since it was observed that an exception in thread is encountered randomly in IBKR interface.
                        try:
                            last_known_price_flt, _ = w1_if_getLiveData(
                                ticker_str = security_name_str,
                                simulated_on = simulated_on
                            )
                        except TypeError:
                            # log
                            logger_obj.warning(
                                f'Handled a TypeError exception while requesting live data for {security_name_str}...'
                            )
                            count_ibkr_faults += 1
                            continue
                        if last_known_price_flt > acquisition_price_threshold_flt:
                            continue
                        temp_list.append(security_name_str)
                    
                    # update passive pool set
                    passive_pool_str_set = set(temp_list)

                    # log
                    logger_obj.info(
                        f'Determined a preliminary list of {len(passive_pool_str_set)} tickers in passive pool...'
                    )
            
                # ==== ==== ==== ====

                # passive pool set update - put portfolio securities to passive pool set, append to dispose list
                if len(portfolio_information_dict.keys()) > 0:
                    # update passive pool set and dispose set
                    for security_name_str in list(portfolio_information_dict.keys()):
                        if int(portfolio_information_dict[security_name_str]['quantity_int']) != 0:
                            # append to dispose set & passive pool set
                            # NOTE: The below step was added in the event that Helios is turned off.
                            # NOTE: This step is necessary for immediate consideration of owned securities for disposition.
                            if security_name_str not in dispose_set:
                                dispose_set.add(security_name_str)
                                passive_pool_str_set.add(security_name_str)

                    # update dispose set (per portfolio)
                    # NOTE: This extra step was added to ensure dispose set is consistent with securities in portfolio.
                    # NOTE: It is possible that they may go out of sync if orders are not honored instantly.
                    temp_list = list(dispose_set)
                    for security_name_str in dispose_set:
                        if security_name_str in list(portfolio_information_dict.keys()) and portfolio_information_dict[security_name_str]['quantity_int'] != 0:
                            continue
                        else:
                            temp_list.remove(security_name_str)
                    dispose_set = set(temp_list)

                # intermediate pool set update - append sampled tickers from previous iteration
                if len(active_pool_str_set):
                    intermediate_pool_str_set = active_pool_str_set.copy()

                # log
                logger_obj.info(
                    f'Determined a final set of {len(passive_pool_str_set)} tickers in passive pool...'
                )
                logger_obj.info(
                    f'Stored a processed set of {len(intermediate_pool_str_set)} tickers in intermediate pool...'
                )

                # ==== ==== ==== ====

                # sample by TRADE_RL_EVALUATION_SAMPLE_FACTOR * QUANTITY
                # NOTE: This is needed to provide the RL agent with more options for selection during evaluation.
                # NOTE: Since securities dispose_set (from portfolio) are also added to passive_pool_set, the length needs to be subtracted.
                if (len(passive_pool_str_set) - len(dispose_set)) > TRADE_RL_EVALUATION_SAMPLE_FACTOR*QUANTITY:
                    temp_list = list(passive_pool_str_set)
                    random.shuffle(temp_list)
                    active_pool_str_set = set(temp_list[:TRADE_RL_EVALUATION_SAMPLE_FACTOR*QUANTITY])
                    passive_pool_str_set = {item for item in passive_pool_str_set if item not in active_pool_str_set}

                    # ==== ====

                    # infer with RL agent based on historical daily data (based on last 252 days)
                    logger_obj.info(f'Started inferencing with {TRADE_RL_EVALUATION_SAMPLE_FACTOR * QUANTITY} tickers, first few samples are: {list(active_pool_str_set)[:QUANTITY]}...')
                    # NOTE: This exceptions handling was included since it was observed that an exception in data download is encountered randomly in IBKR interface.
                    # NOTE: Following error happens as manifestation of the exception: 'ValueError: Sample larger than population or is negative'.
                    last_action_dict = {}
                    try:
                        last_action_dict = inferLastActionToTrade(
                            sampled_tickers_list = list(active_pool_str_set),
                            recent_data_chunk_int = TRADE_RECENT_DATA_CHUNK_RL_INFERENCE
                        )
                    except ValueError:
                        # log
                        logger_obj.warning(
                            f'Handled a ValueError exception while inferencing with active tickers list...'
                        )
                    if last_action_dict:
                        for key in list(last_action_dict.keys()):
                            if int(last_action_dict[key]) > 0:
                                logger_obj.info(f'RL model derived BUY action on {key}...')
                            elif int(last_action_dict[key]) < 0:
                                logger_obj.info(f'RL model derived SELL action on {key}...')
                            else:
                                pass

                    # ==== ====

                    # derive inference results
                    if last_action_dict:
                        infer_security_name_str = str(list(last_action_dict.keys())[0])
                        if int(list(last_action_dict.values())[0]) != 0:
                            infer_action_enum = ActionSignal.IMMEDIATE_BUY if int(list(last_action_dict.values())[0]) > 0 else ActionSignal.IMMEDIATE_SELL
                        else:
                            infer_action_enum = ActionSignal.HOLD_OR_IGNORE
                        
                        if infer_action_enum == ActionSignal.IMMEDIATE_BUY:
                            if infer_security_name_str not in acquire_set and infer_security_name_str not in list(portfolio_information_dict.keys()):
                                # add to acquire list
                                acquire_set.add(infer_security_name_str)
                                # log
                                logger_obj.info(f'Added {infer_security_name_str} to acquire list...')

                        elif infer_action_enum == ActionSignal.IMMEDIATE_SELL:
                            if infer_security_name_str not in dispose_set and infer_security_name_str in list(portfolio_information_dict.keys()):
                                # add to dispose list
                                dispose_set.add(infer_security_name_str)
                                # log
                                logger_obj.info(f'Added {infer_security_name_str} to dispose list...')
                
                else:
                    # move elements from intermediate pool set back to passive pool set
                    passive_pool_str_set = passive_pool_str_set.union(intermediate_pool_str_set)
                    intermediate_pool_str_set = set()

                # ==== ==== ==== ====

                # log
                if acquire_set:
                    logger_obj.info(
                        f'Confirmed {len(acquire_set)} items in acquire list, first few samples are: {list(acquire_set)[:4]}'
                    )
                if dispose_set:
                    logger_obj.info(
                        f'Confirmed {len(dispose_set)} items in dispose list, first few samples are: {list(dispose_set)[:4]}'
                    )

            # ==== ==== ==== ==== ==== ==== ==== ==== STRATEGIZE

            # ==== ==== ==== ==== ==== ==== ==== ==== ACT

            if phase_enum == OperationPhase.PHASE_ACT:

                # keep continuing if strategize step was not completed until the right time
                if not acquire_set and not dispose_set:
                    # wait
                    time.sleep(WAIT_TIME_TEN)
                    # NOTE: The 'continue' statement is needed to bypass later steps and start next iteration of forever loop.
                    continue

                # sample loop start time
                loop_start_time_flt = time.time()

                # get account information
                account_information_dict = None
                while not account_information_dict:
                    try:
                        account_information_dict, _ = w1_if_getAccountInformation(
                            simulated_on = simulated_on
                        )
                    except KeyError:
                        # log
                        logger_obj.warning(
                            'Handled a KeyError exception while requesting account/portfolio information, retrying...'
                        )
                        count_ibkr_faults += 1

                # log
                logger_obj.info(
                    f'==== Cash Val.            : ${account_information_dict["buying_power_flt"]}'
                )
                logger_obj.info(
                    f'==== Portfolio Val.       : ${account_information_dict["portfolio_value_flt"]}'
                )
                logger_obj.info(
                    f'==== Un. Day P/L Val.     : ${account_information_dict["unrealized_pnl_flt"]}'
                )
                logger_obj.info(
                    f'==== Un. Overall P/L Perc.: {account_information_dict["unrealized_overall_pnl_perc_flt"]}%'
                )

                # ==== ==== ==== ==== ACT ON INFERRED SELL ACTION

                # execute disposal actions
                if dispose_set:
                    for security_name_str in dispose_set:
                        if security_name_str not in acquisition_preference_list:
                            # generate trade signal
                            # NOTE: This exception takes care of events when IBKR interface randomly fails to provide data for a security, which is a known issue with IBKR API.
                            try:
                                action_signal_enum, live_price_flt = w1_generateTradeSignal_Strategy_Comprehensive(
                                    ticker_str = security_name_str,
                                    simulated_on = simulated_on
                                )
                            except KeyError:
                                # log
                                logger_obj.warning(
                                    f'Handled a KeyError exception while deriving action signal for {security_name_str} within dispose list, sleeping 10 seconds...'
                                )
                                # take a short break
                                time.sleep(WAIT_TIME_TEN)
                                count_ibkr_faults += 1
                                continue

                            # transmit sell request
                            if debug_override_on:
                                action_signal_enum = ActionSignal.HOLD_OR_IGNORE
                                # log
                                logger_obj.info(
                                    f'[DEBUG] Sell action logic reached for {security_name_str} within dispose set in debug mode...'
                                )
                            if action_signal_enum == ActionSignal.IMMEDIATE_SELL:
                                # derive updated account and portfolio information right before sell order
                                account_information_dict = None
                                portfolio_information_dict = None
                                while not account_information_dict:
                                    try:
                                        account_information_dict, portfolio_information_dict = w1_if_getAccountInformation(
                                            simulated_on = simulated_on
                                        )
                                    except KeyError:
                                        # log
                                        logger_obj.warning(
                                            'Handled a KeyError exception while requesting account/portfolio information, retrying...'
                                        )
                                        count_ibkr_faults += 1

                                # place sell order
                                if limit_orders_on:
                                    # generate order price
                                    limit_order_price_flt = live_price_flt + TRADE_LIMIT_ORDER_GAP
                                    _ = w1_if_placeOrder(
                                        ticker_str = security_name_str,
                                        primary_exchange_str = '',
                                        action_type_str = 'SELL',
                                        quantity_int = int(portfolio_information_dict[security_name_str]['quantity_int']),
                                        order_type_str = 'LMT',
                                        limit_order_price_flt = limit_order_price_flt,
                                        tif_str = 'DAY',
                                        simulated_on = simulated_on
                                    )
                                else:
                                    _ = w1_if_placeOrder(
                                        ticker_str = security_name_str,
                                        primary_exchange_str = '',
                                        action_type_str = 'SELL',
                                        quantity_int = int(portfolio_information_dict[security_name_str]['quantity_int']),
                                        order_type_str = 'MKT',
                                        limit_order_price_flt = 0.0,
                                        tif_str = 'DAY',
                                        simulated_on = simulated_on
                                    )

                                if not limit_orders_on:
                                    # update dispose set
                                    dispose_set.discard(security_name_str)

                                    # generate temporary dictionary and update ledger
                                    temp_dict = {
                                        'entry_date_str': [w2_generateDateStringYYYYMMDD()],
                                        'transaction_str': ['limit sell' if limit_orders_on else 'sell'],
                                        'security_str': [security_name_str],
                                        'quantity_int': [portfolio_information_dict[security_name_str]['quantity_int']],
                                        'acquisition_price_flt': [0.0],
                                        'disposal_price_flt': [limit_order_price_flt if limit_orders_on else live_price_flt],
                                        'buying_power_flt': [account_information_dict["buying_power_flt"]],
                                        'portfolio_value_flt': [account_information_dict["portfolio_value_flt"]]
                                    }
                                    # make ledger entry
                                    w2_updateLedgerEntries(
                                        data_dict = temp_dict,
                                        simulated_on = simulated_on
                                    )

                                    # log
                                    logger_obj.info(
                                        f'Security {security_name_str} of quantity {temp_dict["quantity_int"][0]} SOLD at {live_price_flt} per share...'
                                    )

                # ==== ==== ==== ==== DERIVE ACQUISITION QUANTITIES

                # derive acquisition quantities
                # NOTE: A minimum count of TRADE_ACQUISITION_PORT_OPT_MIN_COUNT is needed for portfolio optimization.

                combined_pool_set = acquire_set.union(dispose_set)
                acquisition_quantities_dict = {}
                optimized_portfolio_weights_dict = {}
                if len(combined_pool_set) >= TRADE_ACQUISITION_PORT_OPT_MIN_COUNT:
                    # download all daily data once
                    # for security_name_str in combined_pool_set:
                    #     _ = w1_if_getHistoricalData_D(
                    #         ticker_str = security_name_str,
                    #         in_loop_on = True,
                    #         simulated_on = simulated_on
                    #     )
                    _ = w1_if_getHistoricalDataInThreadsMain(
                        ticker_str_list = list(combined_pool_set),
                        data_path_str = 'data/daily/',
                        resolution_str = 'daily',
                        results_dict = {},
                        no_stale_on = True,
                        simulated_on = simulated_on
                    )
                    
                    # derive portfolio weights
                    optimized_portfolio_weights_dict = w2_optimizePortfolio(
                        picked_tickers_list = list(combined_pool_set)
                    )['MV']

                if acquire_set:
                    for security_name_str in acquire_set:
                        position_size_int = w2_calculatePositionSize(
                            account_size_flt = account_information_dict["buying_power_flt"],
                            security_name_str = security_name_str,
                            risk_per_trade_percentage_flt = 0.05,
                            simulated_on = simulated_on
                        )
                        optimized_weight = optimized_portfolio_weights_dict.get(security_name_str)
                        if optimized_weight is None:
                            acquisition_quantities_dict[security_name_str] = int(position_size_int)
                        else:
                            acquisition_quantities_dict[security_name_str] = int(position_size_int * optimized_weight)

                # ==== ==== ==== ==== ACT ON INFERRED BUY ACTION

                # execute acquisition actions
                if acquire_set:
                    for security_name_str in acquire_set:
                        if security_name_str not in disposal_preference_list:
                            # generate trade signal enumeration
                            # NOTE: This exception takes care of events when IBKR interface randomly fails to provide data for a security, which is a known issue with IBKR API.
                            try:
                                action_signal_enum, live_price_flt = w1_generateTradeSignal_Strategy_Comprehensive(
                                    ticker_str = security_name_str,
                                    weights_dict = TRADE_STRATEGY_COMP_WEIGHTS,
                                    thresold_flt = TRADE_STRATEGY_COMP_THRESHOLD,
                                    simulated_on = simulated_on
                                )
                            except KeyError:
                                # log
                                logger_obj.warning(
                                    f'Handled a KeyError exception while deriving action signal for {security_name_str} within acquire list, sleeping 10 seconds...'
                                )
                                # take a short break
                                time.sleep(WAIT_TIME_TEN)
                                count_ibkr_faults += 1
                                continue
                
                            # transmit buy request (if quantity is not equal to zero)
                            if debug_override_on:
                                action_signal_enum = ActionSignal.HOLD_OR_IGNORE
                                # log
                                logger_obj.info(
                                    f'[DEBUG] Buy action logic reached for {security_name_str} within acquire set in debug mode...'
                                )

                            quantity_int = 0
                            if action_signal_enum == ActionSignal.IMMEDIATE_BUY:
                                quantity_int = acquisition_quantities_dict.get(security_name_str, 0)
                                if quantity_int > IBKR_ORDER_QUANTITY_LIMIT:
                                    quantity_int = IBKR_ORDER_QUANTITY_LIMIT

                            # place buy order
                            if action_signal_enum == ActionSignal.IMMEDIATE_BUY and quantity_int > 0:
                                if limit_orders_on:
                                    # generate order price
                                    limit_order_price_flt = live_price_flt - TRADE_LIMIT_ORDER_GAP
                                    _ = w1_if_placeOrder(
                                        ticker_str = security_name_str,
                                        primary_exchange_str = '',
                                        action_type_str = 'BUY',
                                        quantity_int = quantity_int,
                                        order_type_str = 'LMT',
                                        limit_order_price_flt = limit_order_price_flt,
                                        tif_str = 'DAY',
                                        simulated_on = simulated_on
                                    )
                                else:
                                    _ = w1_if_placeOrder(
                                        ticker_str = security_name_str,
                                        primary_exchange_str = '',
                                        action_type_str = 'BUY',
                                        quantity_int = quantity_int,
                                        order_type_str = 'MKT',
                                        limit_order_price_flt = 0.0,
                                        tif_str = 'DAY',
                                        simulated_on = simulated_on
                                    )

                                account_information_dict = None
                                while not account_information_dict:
                                    try:
                                        # derive updated account information right after acquisition order
                                        account_information_dict, _ = w1_if_getAccountInformation(
                                            simulated_on = simulated_on
                                        )
                                    except KeyError:
                                        # log
                                        logger_obj.warning(
                                            'Handled a KeyError exception while requesting account/portfolio information, retrying...'
                                        )
                                        count_ibkr_faults += 1

                                if not limit_orders_on:
                                    # update acquire set
                                    acquire_set.discard(security_name_str)

                                    # generate temporary dictionary and update ledger
                                    temp_dict = {
                                        'entry_date_str': [w2_generateDateStringYYYYMMDD()],
                                        'transaction_str': ['limit buy' if limit_orders_on else 'buy'],
                                        'security_str': [security_name_str],
                                        'quantity_int': [quantity_int],
                                        'acquisition_price_flt': [limit_order_price_flt if limit_orders_on else live_price_flt],
                                        'disposal_price_flt': [0.0],
                                        'buying_power_flt': [account_information_dict['buying_power_flt']],
                                        'portfolio_value_flt': [account_information_dict['portfolio_value_flt']]
                                    }
                                    # make ledger entry
                                    w2_updateLedgerEntries(
                                        data_dict = temp_dict,
                                        simulated_on = simulated_on
                                    )

                                    # log
                                    logger_obj.info(
                                        f'Security {security_name_str} of quantity {temp_dict["quantity_int"][0]} BOUGHT at {live_price_flt} per share...'
                                    )
                                
                # ==== ==== ==== ====

                # derive latest account and portfolio information
                account_information_dict = None
                portfolio_information_dict = None
                while not account_information_dict:
                    try:
                        # derive updated account information right after acquisition order
                        account_information_dict, portfolio_information_dict = w1_if_getAccountInformation(
                            simulated_on = simulated_on
                        )
                    except KeyError:
                        # log
                        logger_obj.warning(
                            'Handled a KeyError exception while requesting account/portfolio information, retrying...'
                        )
                        count_ibkr_faults += 1
                
                # record details if limit sell was successful
                if limit_orders_on and dispose_set:
                    for security_name_str in dispose_set:
                        if security_name_str in portfolio_information_dict.keys() and int(portfolio_information_dict[security_name_str]['quantity_int']) == 0:
                            # get live price
                            # NOTE: This exceptions handling was included since it was observed that an exception in thread is encountered randomly in IBKR interface.
                            try:
                                last_known_price_flt, _ = w1_if_getLiveData(
                                    ticker_str = security_name_str,
                                    simulated_on = simulated_on
                                )
                            except TypeError:
                                # log
                                logger_obj.warning(
                                    f'Handled a TypeError exception while requesting live data for {security_name_str}...'
                                )
                                count_ibkr_faults += 1
                                continue
                            
                            # update dispose set
                            dispose_set.discard(security_name_str)

                            # generate temporary dictionary and update ledger
                            temp_dict = {
                                'entry_date_str': [w2_generateDateStringYYYYMMDD()],
                                'transaction_str': ['limit sell' if limit_orders_on else 'sell'],
                                'security_str': [security_name_str],
                                'quantity_int': [portfolio_information_dict[security_name_str]['quantity_int']],
                                'acquisition_price_flt': [0.0],
                                'disposal_price_flt': [last_known_price_flt],
                                'buying_power_flt': [account_information_dict["buying_power_flt"]],
                                'portfolio_value_flt': [account_information_dict["portfolio_value_flt"]]
                            }
                            # make ledger entry
                            w2_updateLedgerEntries(
                                data_dict = temp_dict,
                                simulated_on = simulated_on
                            )

                            # log
                            logger_obj.info(
                                f'Security {security_name_str} of quantity {temp_dict["quantity_int"][0]} LIMIT-SOLD at {last_known_price_flt} per share...'
                            )

                # record details if limit buy was successful
                if limit_orders_on and acquire_set:
                    for security_name_str in acquire_set:
                        if security_name_str in portfolio_information_dict.keys() and int(portfolio_information_dict[security_name_str]['quantity_int']) != 0:
                            # get live price
                            # NOTE: This exceptions handling was included since it was observed that an exception in thread is encountered randomly in IBKR interface.
                            try:
                                last_known_price_flt, _ = w1_if_getLiveData(
                                    ticker_str = security_name_str,
                                    simulated_on = simulated_on
                                )
                            except TypeError:
                                # log
                                logger_obj.warning(
                                    f'Handled a TypeError exception while requesting live data for {security_name_str}...'
                                )
                                count_ibkr_faults += 1
                                continue
                            
                            # update acquire set
                            acquire_set.discard(security_name_str)

                            # generate temporary dictionary and update ledger
                            temp_dict = {
                                'entry_date_str': [w2_generateDateStringYYYYMMDD()],
                                'transaction_str': ['limit buy' if limit_orders_on else 'buy'],
                                'security_str': [security_name_str],
                                'quantity_int': [portfolio_information_dict[security_name_str]['quantity_int']],
                                'acquisition_price_flt': [last_known_price_flt],
                                'disposal_price_flt': [0.0],
                                'buying_power_flt': [account_information_dict['buying_power_flt']],
                                'portfolio_value_flt': [account_information_dict['portfolio_value_flt']]
                            }
                            # make ledger entry
                            w2_updateLedgerEntries(
                                data_dict = temp_dict,
                                simulated_on = simulated_on
                            )

                            # log
                            logger_obj.info(
                                f'Security {security_name_str} of quantity {temp_dict["quantity_int"][0]} BOUGHT at {last_known_price_flt} per share...'
                            )
                
                # ==== ==== ==== ====

                if debug_override_on:
                    # log
                    logger_obj.info(
                        f'[DEBUG] Detected {count_ibkr_faults} instances of faults from IBKR...'
                    )

                # perform cleanup at every loop
                # NOTE: The following must not be added:
                # active_pool_str_set, intermediate_pool_str_set, passive_pool_str_set, acquire_set, dispose_set
                quantity_int = None
                acquisition_price_threshold_flt = None
                temp_list = None
                security_name_str = None
                infer_security_name_str = None
                account_information_dict = None
                portfolio_information_dict = None
                last_action_dict = None
                acquisition_quantities_dict = None
                temp_dict = None
                infer_action_enum = None
                action_signal_enum = None

                # ==== ==== ==== ====

                exec_time_flt = time.time() - loop_start_time_flt
                if exec_time_flt <= 60.0:
                    logger_obj.info(
                        f'Trade loop executed in {exec_time_flt:.1f} s...'
                    )
                    logger_obj.info(
                        f'Total number of trade interface errors encountered: {count_ibkr_faults}...'
                    )
                else:
                    logger_obj.warning(
                        f'Trade loop execution exceeded 1 minute, executed in {exec_time_flt:.1f} s...'
                    )
                    logger_obj.info(
                        f'Total number of trade interface errors encountered: {count_ibkr_faults}...'
                    )
                
            # ==== ==== ==== ==== ==== ==== ==== ==== ACT

            # ==== ==== ==== ==== ==== ==== ==== ==== REFLECT

            if phase_enum == OperationPhase.PHASE_REFLECT:
                if not lock_next_day_preparation_on:
                    # generate analysis reports on securities that are owned
                    for security_name_str in dispose_set:
                        w1_generateAnalysisReport(
                            ticker_str = security_name_str,
                            simulated_on = simulated_on
                        )
                    # generate analyis report on SPY (which tracks S&P500 Index)
                    w1_generateAnalysisReport(
                        ticker_str = 'SPY',
                        simulated_on = simulated_on
                    )
                    # stash away reports
                    w2_stashAway(
                        location_str = 'reports/analyses/', 
                        stash_folder_name_str = None
                    )

                    # refresh transaction memories
                    w2_refreshTransactionMemories(
                        simulated_on = simulated_on
                    )

                    # check if end at market close flag is turned on
                    if end_at_market_close_on:
                        logger_obj.info(
                            f'Generated analysis reports and terminated Helios...'
                        )
                        sys.exit()

                    # clear previous session data
                    w2_clearPreviousSessionData(
                        remove_tickers_on = True,
                        remove_scans = True,
                        remove_daily_on = True,
                        remove_hourly_on = True,
                        remove_minutely_on = True,
                        remove_features_on = True,
                        remove_fundamentals_on = True,
                        remove_returns_on = True,
                        remove_logs_on = False,
                        remove_plots_on = True,
                        remove_results_on = True,
                        remove_temps = True
                    )

                    # refresh ticker data
                    logger_obj.info(
                        'Initiated download of fresh ticker data for next day...'
                    )
                    w1_if_getTickers(test_on = False)
                    w1_refineTickers_FavourableBuyCondition(simulated_on = simulated_on)

                    # turn lock on for execution once a day
                    lock_next_day_preparation_on = True

                # wait
                time.sleep(WAIT_TIME_TEN)

            # ==== ==== ==== ==== ==== ==== ==== ==== REFLECT

        else:
            # wait
            time.sleep(WAIT_TIME_TEN)


if __name__ == '__main__':
    trade(
        debug_override_on = False,
        limit_orders_on = True,
        end_at_market_close_on = True,
        simulated_on = True
    )