# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] w2_Strategy_EMA_KMA_MACD_RSI
# [2] Inspired by Haiku 4.5 with Reasoning
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import os

# import custom configs and utils
from config import (
    IBKR_COMMISSION, 
    ROOT_PATH, 
    TRADE_PRICE_CHANGE_SAFETY_THRESHOLD
)
from config_enums import ActionSignal
from data.w1_if_getHistoricalData import w1_if_getHistoricalData_M
from data.w1_if_getHistoricalData import w1_if_getHistoricalData_H
from data.w1_if_getLiveData import w1_if_getLiveData
from strategies.w2_appendATRIndicator import w2_appendATRIndicator
from strategies.w2_appendBBIndicator import w2_appendBBIndicator
from strategies.w2_appendEWMATracker import w2_appendEWMATracker
from strategies.w2_appendKFTracker import w2_appendKMATracker
from strategies.w2_appendMACDIndicator import w2_appendMACDIndicator
from strategies.w2_appendRSIIndicator import w2_appendRSIIndicator
from strategies.w2_appendZScoreIndicator import w2_appendZScoreIndicator
from utils.w2_generateDateStringYYYYMMDD import w2_generateDateStringYYYYMMDD
from utils.w2_performDataFrameOps import w2_roundByDecimals
from utils.w2_performJSONOps import w2_readJSON, w2_writeToJSON
from utils.w2_plot import w2_plotInSubplots


def w1_generateTradeSignal_Strategy_EMA_KMA_MACD_RSI(
        ticker_str,
        memories_path_str = 'strategies/memories/',
        rsi_lower_bound_flt = 15.0,
        rsi_upper_bound_flt = 85.0,
        min_comparison_gap_flt = 0.02,
        plot_on = False,
        multi_security_simulation_on = False,
        no_stale_on = False,
        simulated_on = True
):
    """
    Generate a trade signal using EMA, KMA, MACD, and RSI indicators.

    This strategy pulls intraday historical data for a ticker, enriches it with
    technical indicators, and then decides whether to buy, sell, or hold based on
    momentum, trend, and volatility guardrails. It supports live execution,
    cached decision memory, and backtest simulation modes.

    Parameters:
        ticker_str (str): Ticker symbol to analyze.
        memories_path_str (str): Relative path for storing decision memory JSON.
        rsi_lower_bound_flt (float): RSI threshold below which a sell lock is enabled.
        rsi_upper_bound_flt (float): RSI threshold above which the lock is released.
        min_comparison_gap_flt (float): Minimum signal gap required for entry/exit decisions.
        plot_on (bool): If True, run the function in backtest mode and plot results.
        multi_security_simulation_on (bool): If True, suppress verbose printing during backtest loops.
        no_stale_on (bool): If True, bypass stale-data protection for historical data fetch.
        simulated_on (bool): If True, use simulated data sources rather than live trade feeds.

    Returns:
        tuple[ActionSignal, float]: A tuple containing the generated action signal and the latest live price.
    """
    # get intraday data, add information, and round to 2 decimals
    data_df = w2_roundByDecimals(
        df = w2_appendEWMATracker(
            timeseries_df = w2_appendKMATracker(
                timeseries_df = w2_appendMACDIndicator(
                    timeseries_df = w2_appendRSIIndicator(
                        timeseries_df = w1_if_getHistoricalData_M(
                            ticker_str = ticker_str,
                            duration_str = '1 W',
                            bar_size_str = '1 min',
                            in_loop_on = True,
                            no_stale_on = no_stale_on,
                            simulated_on = simulated_on
                        )
                    )
                )
            )
        ),
        decimals_int = 2
    )
    
    if not plot_on:
        # generate/read decision memory dictionary
        if os.path.exists(ROOT_PATH + memories_path_str + 'memories.json'):
            # read memory file
            decision_memory_dict = w2_readJSON(
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )
        else:
            decision_memory_dict = {}
            w2_writeToJSON(
                data_dict = decision_memory_dict,
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )
        
        # check if key for ticker exists, else initialize
        if ticker_str in list(decision_memory_dict.keys()):
            pass
        else:
            # initialize decision memory dict
            decision_memory_dict.update(
                {
                    ticker_str: {
                        'date': w2_generateDateStringYYYYMMDD(),
                        'lock_on': False,
                        'position': -1.0,
                        'prev_price_at_buy': 0.0,
                        'prev_kma_at_buy': 0.0,
                        'realized_pnl': 0.0
                    }
                }
            )

        # initialize default trade signal enumeration
        trade_signal_enum = ActionSignal.HOLD_OR_IGNORE

        # get current live price data (and dynamically adjust wait time as needed)
        live_price_flt, _ = w1_if_getLiveData(
            ticker_str = ticker_str,
            simulated_on = simulated_on
        )

        # check Relative Strength Index conditions
        if data_df['rsi'].iloc[-1] > rsi_upper_bound_flt:
            decision_memory_dict[ticker_str]['lock_on'] = False
        elif data_df['rsi'].iloc[-1] <= rsi_lower_bound_flt:
            # NOTE: This condition was introduced to exit the market when early signs of sharp sell-off are detected, and never enter again for *some* time.
            decision_memory_dict[ticker_str]['lock_on'] = True
        else:
            pass

        # derive acquisition conditions
        acquisition_condition1 = (
                (data_df['signal'].iloc[-1] + min_comparison_gap_flt < data_df['macd'].iloc[-1]) and
                (data_df['kma'].iloc[-1] > data_df['ewma'].iloc[-1] + min_comparison_gap_flt)
        )
        acquisition_condition2 = (decision_memory_dict[ticker_str]['lock_on'] == False)

        # derive disposal conditions
        # NOTE: Commission fees for both buying and selling are accounted for.
        disposal_condition1 = (
                (data_df['signal'].iloc[-1] > data_df['macd'].iloc[-1] + min_comparison_gap_flt) and
                (data_df['kma'].iloc[-1] + min_comparison_gap_flt < data_df['ewma'].iloc[-1]) and
                (data_df['kma'].iloc[-1] > decision_memory_dict[ticker_str]['prev_kma_at_buy'] + min_comparison_gap_flt) and
                (live_price_flt > (decision_memory_dict[ticker_str]['prev_price_at_buy'] + (IBKR_COMMISSION*2) + TRADE_PRICE_CHANGE_SAFETY_THRESHOLD))
        )
        disposal_condition2 = (decision_memory_dict[ticker_str]['lock_on'] == True)

        # generate trade signal enumeration and decision memory entries
        if (decision_memory_dict[ticker_str]['position'] == -1.0) and acquisition_condition1 and acquisition_condition2:
            # generate trade signal and populate results
            trade_signal_enum = ActionSignal.IMMEDIATE_BUY
            decision_memory_dict[ticker_str]['position'] = 1.0
            decision_memory_dict[ticker_str]['realized_pnl'] = 0.0
            decision_memory_dict[ticker_str]['prev_price_at_buy'] = live_price_flt
            decision_memory_dict[ticker_str]['prev_kma_at_buy'] = data_df['kma'].iloc[-1]

            # remove previous and save new decision memory dictionary json file
            os.remove(path = ROOT_PATH + memories_path_str + 'memories.json')
            w2_writeToJSON(
                data_dict = decision_memory_dict,
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )

        elif (decision_memory_dict[ticker_str]['position'] == 1.0) and (disposal_condition1 or disposal_condition2):
            # generate trade signal
            trade_signal_enum = ActionSignal.IMMEDIATE_SELL

            # remove entry of ticker from memory
            del decision_memory_dict[ticker_str]

            # remove previous and save new decision memory dictionary json file
            os.remove(path = ROOT_PATH + memories_path_str + 'memories.json')
            w2_writeToJSON(
                data_dict = decision_memory_dict,
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )

        else:
            # generate trade signal and reset results
            trade_signal_enum = ActionSignal.HOLD_OR_IGNORE

        return trade_signal_enum, live_price_flt

    else:
        # print opening statement
        if not multi_security_simulation_on:
            print('INFO: Backtesting is about to start...')
            print()

        # initialize decision memory dict
        decision_memory_dict = {
            ticker_str: {
                'lock_on': False,
                'position': -1.0,
                'prev_price_at_buy': 0.0,
                'prev_kma_at_buy': 0.0,
                'realized_pnl': 0.0
            }
        }

        # initialize parameter to keep track of p/l
        realized_pnl_flt = 0.0

        # generate columns for trade signal and profit/loss
        data_df['trade_signal'] = 0.0

        for index_int in range(len(data_df)):
            # check Relative Strength Index conditions
            if data_df['rsi'].iloc[index_int] > rsi_upper_bound_flt:
                decision_memory_dict[ticker_str]['lock_on'] = False
            elif data_df['rsi'].iloc[index_int] <= rsi_lower_bound_flt:
                # NOTE: This condition was introduced to exit the market when early signs of sharp sell-off are detected, and never enter again for *some* time.
                decision_memory_dict[ticker_str]['lock_on'] = True
            else:
                pass

            # derive acquisition conditions
            acquisition_condition1 = (
                    (data_df['signal'].iloc[index_int] + min_comparison_gap_flt < data_df['macd'].iloc[index_int]) and
                    (data_df['kma'].iloc[index_int] > data_df['ewma'].iloc[index_int] + min_comparison_gap_flt)
            )
            acquisition_condition2 = (decision_memory_dict[ticker_str]['lock_on'] == False)

            # derive disposal conditions
            # NOTE: Commission fees for both buying and selling are accounted for.
            disposal_condition1 = (
                    (data_df['signal'].iloc[index_int] > data_df['macd'].iloc[index_int] + min_comparison_gap_flt) and
                    (data_df['kma'].iloc[index_int] + min_comparison_gap_flt < data_df['ewma'].iloc[index_int]) and
                    (data_df['kma'].iloc[index_int] > decision_memory_dict[ticker_str]['prev_kma_at_buy'] + min_comparison_gap_flt) and
                    (data_df['close'].iloc[index_int] > (decision_memory_dict[ticker_str]['prev_price_at_buy'] + (IBKR_COMMISSION*2) + TRADE_PRICE_CHANGE_SAFETY_THRESHOLD))
            )
            disposal_condition2 = (decision_memory_dict[ticker_str]['lock_on'] == True)

            # generate trade signal
            if (decision_memory_dict[ticker_str]['position'] == -1.0) and acquisition_condition1 and acquisition_condition2:
                # generate trade signal and populate results
                data_df.loc[index_int, 'trade_signal'] = 1.0
                decision_memory_dict[ticker_str]['position'] = 1.0
                decision_memory_dict[ticker_str]['realized_pnl'] = 0.0
                decision_memory_dict[ticker_str]['prev_price_at_buy'] = data_df['close'].iloc[index_int]
                decision_memory_dict[ticker_str]['prev_kma_at_buy'] = data_df['kma'].iloc[index_int]
                # print out details
                if not multi_security_simulation_on:
                    print(f"-- {str(data_df['date'].iloc[index_int])}, BOUGHT, ${data_df['close'].iloc[index_int]}")
                    print(f"-- {str(data_df['date'].iloc[index_int])}, MACD Signal/Line: {data_df['signal'].iloc[index_int]}/{data_df['macd'].iloc[index_int]}, KMA: {data_df['kma'].iloc[index_int]}, EWMA: {data_df['ewma'].iloc[index_int]}")
                    print()

            elif (decision_memory_dict[ticker_str]['position'] == 1.0) and (disposal_condition1 or disposal_condition2):
                # generate trade signal and reset results
                data_df.loc[index_int, 'trade_signal'] = -1.0
                decision_memory_dict[ticker_str]['position'] = -1.0
                decision_memory_dict[ticker_str]['realized_pnl'] = round(float(data_df['close'].iloc[index_int]) - float(decision_memory_dict[ticker_str]['prev_price_at_buy']), 2)
                decision_memory_dict[ticker_str]['prev_price_at_buy'] = 0.0
                decision_memory_dict[ticker_str]['prev_kma_at_buy'] = 0.0
                # print out details
                if not multi_security_simulation_on:
                    print(f"-- {str(data_df['date'].iloc[index_int])}, SOLD, ${data_df['close'].iloc[index_int]} | Realized P/L: {decision_memory_dict[ticker_str]['realized_pnl']}")
                    print(f"-- {str(data_df['date'].iloc[index_int])}, MACD Signal/Line: {data_df['signal'].iloc[index_int]}/{data_df['macd'].iloc[index_int]}, KMA: {data_df['kma'].iloc[index_int]}, EWMA: {data_df['ewma'].iloc[index_int]}")
                    print()
                # updated realized p/l
                realized_pnl_flt += decision_memory_dict[ticker_str]['realized_pnl'] - (IBKR_COMMISSION*2)

            else:
                data_df.loc[index_int, 'trade_signal'] = 0.0

        # print closing statement
        if not multi_security_simulation_on:
            print('INFO: Backtesting is completed!')

        # print summary
        if not multi_security_simulation_on:
            print()
            print(f'Backtest Results: {ticker_str}')
            print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
            print(f"Start Time                  | {data_df['date'].iloc[0]}")
            print(f"End Time                    | {data_df['date'].iloc[-1]}")
            print(f'Commission Per Trade        | ${IBKR_COMMISSION}')
            if realized_pnl_flt >= 0.0:
                print(f'Returns Per Unit            | ${round(realized_pnl_flt, 2)}')
            else:
                print(f'Returns Per Unit            | -${round(abs(realized_pnl_flt), 2)}')
            print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
            print()

        # generate a time steps column for plotting
        if not multi_security_simulation_on:
            data_df['timesteps'] = data_df.index

        # plot data
        if not multi_security_simulation_on:
            w2_plotInSubplots(
                x_data_df = data_df['timesteps'],
                x_axis_label_str = 'Time Steps',
                y_data_df_list = [[data_df['close'], data_df['kma'], data_df['ewma'], data_df['trade_signal']], [data_df['macd'], data_df['signal']], data_df['rsi']],
                y_data_label_str_list = [['Close', 'KMA', 'EWMA', 'Trade Signal'], ['MACD', 'MACD Signal'], 'RSI'],
                y_axes_label_str_list = ['Close with KMA and EWMA, USD', 'MACD with Signal', 'RSI'],
                custom_heights_on = True,
                custom_heights_ratios_list = [3, 1, 1],
                plot_title_str = f'Trade Signal / Strategy Plot for {ticker_str}',
                recent_data_chunk_int = None,
                save_on = False,
                save_file_name_str = f'TradeSignal_Strategy_Plot_{ticker_str}',
                save_path_str = ROOT_PATH + 'reports/plots/',
                show_on = True
            )

        if not multi_security_simulation_on:
            return 0.0
        else:
            return realized_pnl_flt
        


# ------------------------------------------------------------------------------
        


def _calculate_sma(data_df, period_int, column_str = 'close'):
    """
    Calculate Simple Moving Average (SMA) for a time series column.

    Parameters:
        data_df (pd.DataFrame): DataFrame containing the time series.
        period_int (int): Window length for the SMA calculation.
        column_str (str): Column name to compute the moving average on.

    Returns:
        pd.Series: Rolling mean values for the specified column.
    """
    return data_df[column_str].rolling(window = period_int).mean()
    

# def _calculate_ema(data_df, period_int, column_str = 'close'):
#     """
#         Calculate Exponential Moving Average
#     """
#     return data_df[column_str].ewm(span = period_int, adjust = False).mean()


def _calculate_ma_crossover_signals(data_df, short_window_int = 20, long_window_int = 50):
    """
    Calculate moving average crossover buy and sell signals.

    This helper computes short- and long-window simple moving averages and
    identifies crossover events as entry/exit signals.

    Parameters:
        data_df (pd.DataFrame): DataFrame containing price data.
        short_window_int (int): Window length for the short SMA.
        long_window_int (int): Window length for the long SMA.

    Returns:
        dict: A dictionary with boolean Series for 'buy' and 'sell' signals.
    """
    data_df['sma_short'] = _calculate_sma(
        data_df = data_df,
        period_int = short_window_int
    )
    data_df['sma_long'] = _calculate_sma(
        data_df = data_df,
        period_int = long_window_int
    )
    buy_signal = (data_df['sma_short'] > data_df['sma_long']) & (data_df['sma_short'].shift(1) <= data_df['sma_long'].shift(1))
    sell_signal = (data_df['sma_short'] < data_df['sma_long']) & (data_df['sma_short'].shift(1) >= data_df['sma_long'].shift(1))
    
    return {'buy': buy_signal, 'sell': sell_signal}


def _calculate_rsi_signals(data_df, overbought_rsi_flt = 30.0, oversold_rsi_flt = 70.0):
    """
    Calculate RSI-based buy and sell signals.

    This helper flags buy signals when RSI moves back above the oversold level and
    sell signals when RSI moves back below the overbought level.

    Parameters:
        data_df (pd.DataFrame): DataFrame containing an 'rsi' column.
        overbought_rsi_flt (float): RSI threshold above which sell pressure is expected.
        oversold_rsi_flt (float): RSI threshold below which buy pressure is expected.

    Returns:
        dict: A dictionary containing boolean Series for 'buy' and 'sell' signals.
    """
    buy_signal = (data_df['rsi'] < oversold_rsi_flt) & (data_df['rsi'].shift(1) >= oversold_rsi_flt)
    sell_signal = (data_df['rsi'] > overbought_rsi_flt) & (data_df['rsi'].shift(1) <= overbought_rsi_flt)
    
    return {'buy': buy_signal, 'sell': sell_signal}


def _calculate_macd_signals(data_df):
    """
    Calculate MACD-based buy and sell signals.

    Signals are generated when the MACD line crosses the signal line in the
    bullish or bearish direction.

    Parameters:
        data_df (pd.DataFrame): DataFrame containing 'macd' and 'signal' columns.

    Returns:
        dict: A dictionary containing boolean Series for 'buy' and 'sell' signals.
    """
    buy_signal = (data_df['macd'] > data_df['signal']) & (data_df['macd'].shift(1) <= data_df['signal'].shift(1))
    sell_signal = (data_df['macd'] < data_df['signal']) & (data_df['macd'].shift(1) >= data_df['signal'].shift(1))
    
    return {'buy': buy_signal, 'sell': sell_signal}


def _calculate_bb_signals(data_df):
    """
    Calculate Bollinger Band buy and sell signals.

    This helper identifies mean-reversion opportunities by buying when price
    touches the lower band and selling when price touches the upper band.

    Parameters:
        data_df (pd.DataFrame): DataFrame containing 'close', 'bb_lower', and 'bb_upper' columns.

    Returns:
        dict: A dictionary containing boolean Series for 'buy' and 'sell' signals.
    """
    buy_signal = (data_df['close'] < data_df['bb_lower']) & (data_df['close'].shift(1) >= data_df['bb_lower'].shift(1))
    sell_signal = (data_df['close'] > data_df['bb_upper']) & (data_df['close'].shift(1) <= data_df['bb_upper'].shift(1))
    
    return {'buy': buy_signal, 'sell': sell_signal}


def _calculate_zscore_signals(data_df, threshold_flt = 2.0):
    """
    Calculate Z-score mean reversion buy and sell signals.

    This helper triggers buy signals when the z-score crosses upward from an
    extreme negative level and sell signals when it crosses downward from an
    extreme positive level.

    Parameters:
        data_df (pd.DataFrame): DataFrame containing a 'zscore' column.
        threshold_flt (float): Threshold for extreme z-score values.

    Returns:
        dict: A dictionary containing boolean Series for 'buy' and 'sell' signals.
    """
    buy_signal = (data_df['zscore'] < -threshold_flt) & (data_df['zscore'].shift(1) >= -threshold_flt)
    sell_signal = (data_df['zscore'] > threshold_flt) & (data_df['zscore'].shift(1) <= threshold_flt)
    
    return {'buy': buy_signal, 'sell': sell_signal}


def _calculate_composite_signal(
        data_df, 
        weights_dict = None, 
        threshold_flt = 0.5, 
        recent_entires_bool = False, 
        recent_entries_int = 16
    ):
    """
    Calculate a composite buy/sell signal by combining weighted indicator signals.

    This helper aggregates signals from moving averages, MACD, RSI, Bollinger
    Bands, and z-score into a composite score and thresholds it to generate a
    higher-confidence trade signal.

    Parameters:
        data_df (pd.DataFrame): DataFrame containing required indicator columns.
        weights_dict (dict | None): Optional custom weights for each indicator.
        threshold_flt (float): Minimum score required to trigger a buy or sell signal.
        recent_entires_bool (bool): If True, compute scores only over the most recent entries.
        recent_entries_int (int): Number of most recent entries to include when recent_entires_bool is True.

    Returns:
        dict: A dictionary containing boolean Series for 'buy' and 'sell' signals plus numeric 'buy_score' and 'sell_score' Series.
    """
    if weights_dict is None:
        weights_dict = {
            'ma': 0.30,
            'macd': 0.25,
            'rsi': 0.20,
            'bb': 0.15,
            'zscore': 0.10
        }

    ma_signals = _calculate_ma_crossover_signals(data_df = data_df)
    macd_signals = _calculate_macd_signals(data_df = data_df)
    rsi_signals = _calculate_rsi_signals(data_df = data_df)
    bb_signals = _calculate_bb_signals(data_df = data_df)
    zscore_signals = _calculate_zscore_signals(data_df = data_df)

    # aggregate buy signals with weights
    buy_score = (
        ma_signals['buy'].astype(int) * weights_dict['ma'] +
        macd_signals['buy'].astype(int) * weights_dict['macd'] +
        rsi_signals['buy'].astype(int) * weights_dict['rsi'] +
        bb_signals['buy'].astype(int) * weights_dict['bb'] +
        zscore_signals['buy'].astype(int) * weights_dict['zscore']
    )
    
    sell_score = (
        ma_signals['sell'].astype(int) * weights_dict['ma'] +
        macd_signals['sell'].astype(int) * weights_dict['macd'] +
        rsi_signals['sell'].astype(int) * weights_dict['rsi'] +
        bb_signals['sell'].astype(int) * weights_dict['bb'] +
        zscore_signals['sell'].astype(int) * weights_dict['zscore']
    )

    # get recent entries
    if recent_entires_bool:
        buy_score = buy_score[-recent_entries_int:]
        sell_score = sell_score[-recent_entries_int:]

    # generate signals when composite score exceeds threshold
    buy_signal = buy_score >= threshold_flt
    sell_signal = sell_score >= threshold_flt
    
    return {
        'buy': buy_signal,
        'sell': sell_signal,
        'buy_score': buy_score,
        'sell_score': sell_score
    }
    

def w1_generateTradeSignal_Strategy_Comprehensive(
        ticker_str,
        memories_path_str = 'strategies/memories/',
        weights_dict = None,
        thresold_flt = 0.5,
        recent_entries_bool = False,
        recent_entries_int = 16,
        plot_on = False,
        multi_security_simulation_on = False,
        no_stale_on = False,
        simulated_on = True
):
    """
    Generate a trade signal using a composite strategy across multiple indicators.

    This comprehensive strategy combines ATR, Bollinger Bands, MACD, RSI, and
    z-score indicators into a weighted composite signal. It supports live trading
    decision output as well as backtesting visualization and performance summary.

    Parameters:
        ticker_str (str): Ticker symbol to analyze.
        memories_path_str (str): Relative path for storing decision memory JSON.
        weights_dict (dict | None): Custom indicator weights for the composite score.
        thresold_flt (float): Score threshold that triggers buy or sell signals.
        recent_entries_bool (bool): If True, restrict composite scoring to recent data.
        recent_entries_int (int): Number of recent rows to use when recent_entries_bool is True.
        plot_on (bool): If True, run backtest mode and plot results.
        multi_security_simulation_on (bool): If True, suppress verbose printing during backtest loops.
        no_stale_on (bool): If True, bypass stale-data protection for historical data fetch.
        simulated_on (bool): If True, use simulated data sources rather than live feeds.

    Returns:
        tuple[ActionSignal, float] | tuple[float, int]: In live mode, returns an action signal and latest price. In backtest mode, returns realized P/L and number of transactions.
    """
    # get intraday data, add information, and round to 2 decimals
    data_df = w2_roundByDecimals(
        df = w2_appendATRIndicator(
            timeseries_df = w2_appendBBIndicator(
                timeseries_df = w2_appendMACDIndicator(
                    timeseries_df = w2_appendRSIIndicator(
                        timeseries_df = w2_appendZScoreIndicator(
                            timeseries_df = w1_if_getHistoricalData_H(
                                ticker_str = ticker_str,
                                duration_str = '1 Y',
                                bar_size_str = '1 hour',
                                in_loop_on = True,
                                no_stale_on = no_stale_on,
                                simulated_on = simulated_on
                            )
                        )
                    )
                )
            )
        ),
        decimals_int = 2
    )

    # calculate composite signal
    composite_signal_dict = _calculate_composite_signal(
        data_df = data_df,
        weights_dict = weights_dict,
        threshold_flt = thresold_flt,
        recent_entires_bool = recent_entries_bool,
        recent_entries_int = recent_entries_int
    )

    if not plot_on:
        # generate/read decision memory dictionary
        if os.path.exists(ROOT_PATH + memories_path_str + 'memories.json'):
            # read memory file
            decision_memory_dict = w2_readJSON(
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )
        else:
            decision_memory_dict = {}
            w2_writeToJSON(
                data_dict = decision_memory_dict,
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )
        
        # check if key for ticker exists, else initialize
        if ticker_str in list(decision_memory_dict.keys()):
            pass
        else:
            # initialize decision memory dict
            decision_memory_dict.update(
                {
                    ticker_str: {
                        'date': w2_generateDateStringYYYYMMDD(),
                        'lock_on': False,
                        'position': -1.0,
                        'prev_price_at_buy': 0.0,
                        'prev_kma_at_buy': 0.0,
                        'realized_pnl': 0.0
                    }
                }
            )

        # initialize default trade signal enumeration
        trade_signal_enum = ActionSignal.HOLD_OR_IGNORE

        # get current live price data (and dynamically adjust wait time as needed)
        live_price_flt, _ = w1_if_getLiveData(
            ticker_str = ticker_str,
            simulated_on = simulated_on
        )

        # generate trade signal enumeration and decision memory entries
        if (composite_signal_dict['buy'].iloc[-1]):
            # generate trade signal enumeration and populate results
            trade_signal_enum = ActionSignal.IMMEDIATE_BUY
            decision_memory_dict[ticker_str]['position'] = 1.0
            decision_memory_dict[ticker_str]['realized_pnl'] = 0.0
            decision_memory_dict[ticker_str]['prev_price_at_buy'] = live_price_flt

            # remove previous and save new decision memory dictionary json file
            os.remove(path = ROOT_PATH + memories_path_str + 'memories.json')
            w2_writeToJSON(
                data_dict = decision_memory_dict,
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )

        elif (composite_signal_dict['sell'].iloc[-1]):
            # generate trade signal enumeration
            trade_signal_enum = ActionSignal.IMMEDIATE_SELL

            # remove entry of ticker from memory
            del decision_memory_dict[ticker_str]

            # remove previous and save new decision memory dictionary json file
            os.remove(path = ROOT_PATH + memories_path_str + 'memories.json')
            w2_writeToJSON(
                data_dict = decision_memory_dict,
                json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
            )

        else:
            # generate trade signal and reset results
            trade_signal_enum = ActionSignal.HOLD_OR_IGNORE

        return trade_signal_enum, live_price_flt

    else:
        # print opening statement
        if not multi_security_simulation_on:
            print('INFO: Backtesting is about to start...')
            print()

        # initialize decision memory dict
        decision_memory_dict = {
            ticker_str: {
                'lock_on': False,
                'position': -1.0,
                'realized_pnl': 0.0,
                'prev_price_at_buy': 0.0
            }
        }

        # initialize parameter to keep track of p/l
        num_transactions_int = 0
        realized_pnl_flt = 0.0

        # initialize parameters to keep track of last buy & sell prices
        last_buy_price_flt = 0.0
        last_sell_price_flt = 0.0

        # generate columns for trade signal and profit/loss
        data_df['trade_signal'] = 0.0

        # initialize booleans
        in_possession = False

        for index_int in range(len(data_df)):
            # generate trade signal
            if (decision_memory_dict[ticker_str]['position'] == -1.0) and composite_signal_dict['buy'].iloc[index_int]:
                # generate trade signal and populate results
                data_df.loc[index_int, 'trade_signal'] = 1.0
                decision_memory_dict[ticker_str]['position'] = 1.0
                decision_memory_dict[ticker_str]['realized_pnl'] = 0.0
                decision_memory_dict[ticker_str]['prev_price_at_buy'] = data_df['close'].iloc[index_int]
                # print out details
                if not multi_security_simulation_on:
                    print(f"-- {str(data_df['date'].iloc[index_int])}, BOUGHT, ${data_df['close'].iloc[index_int]}")
                    print(f"-- {str(data_df['date'].iloc[index_int])}, Buy Score / Sell Score: {composite_signal_dict['buy_score'].iloc[index_int]} / {composite_signal_dict['sell_score'].iloc[index_int]}")
                    print()
                # update number of transactions
                num_transactions_int += 1
                # update last buy & sell prices
                last_buy_price_flt = float(data_df['close'].iloc[index_int])
                last_sell_price_flt = 0.0
                in_possession = True

            elif (decision_memory_dict[ticker_str]['position'] == 1.0) and composite_signal_dict['sell'].iloc[index_int]:
                # generate trade signal and reset results
                data_df.loc[index_int, 'trade_signal'] = -1.0
                decision_memory_dict[ticker_str]['position'] = -1.0
                decision_memory_dict[ticker_str]['realized_pnl'] = round(float(data_df['close'].iloc[index_int]) - float(decision_memory_dict[ticker_str]['prev_price_at_buy']), 2)
                decision_memory_dict[ticker_str]['prev_price_at_buy'] = 0.0
                # print out details
                if not multi_security_simulation_on:
                    print(f"-- {str(data_df['date'].iloc[index_int])}, SOLD, ${data_df['close'].iloc[index_int]} | Realized P/L: {decision_memory_dict[ticker_str]['realized_pnl']}")
                    print(f"-- {str(data_df['date'].iloc[index_int])}, Buy Score / Sell Score: {composite_signal_dict['buy_score'].iloc[index_int]} / {composite_signal_dict['sell_score'].iloc[index_int]}")
                    print()
                # update number of transactions and realized p/l
                num_transactions_int += 1
                realized_pnl_flt += decision_memory_dict[ticker_str]['realized_pnl'] - (IBKR_COMMISSION*2)
                # update last buy & sell prices
                last_buy_price_flt = 0.0
                last_sell_price_flt = float(data_df['close'].iloc[index_int])
                in_possession = False

            else:
                data_df.loc[index_int, 'trade_signal'] = 0.0

        # print closing statement
        if not multi_security_simulation_on:
            print('INFO: Backtesting is completed!')

        # print summary
        if not multi_security_simulation_on:
            print()
            print(f'Backtest Results: {ticker_str}')
            print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
            print(f"Start Time                  | {data_df['date'].iloc[0]}")
            print(f"End Time                    | {data_df['date'].iloc[-1]}")
            print(f'Commission Per Trade        | ${IBKR_COMMISSION}')
            if in_possession:
                if float(data_df['close'].iloc[-1]) - float(last_buy_price_flt)> 0.0:
                    print(f'Unrealized Growth/Unit      | ${round(float(data_df['close'].iloc[-1]) - float(last_buy_price_flt), 2)}')
                else:
                    print(f'Unrealized Growth/Unit      | -${round(abs(float(data_df['close'].iloc[-1]) - float(last_buy_price_flt)), 2)}')
            if realized_pnl_flt >= 0.0:
                print(f'Realized Returns/Unit       | ${round(realized_pnl_flt, 2)}')
            else:
                print(f'Realized Returns/Unit       | -${round(abs(realized_pnl_flt), 2)}')
            print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
            print()

        # generate a time steps column for plotting
        if not multi_security_simulation_on:
            data_df['timesteps'] = data_df.index

        # plot data
        if not multi_security_simulation_on:
            w2_plotInSubplots(
                x_data_df = data_df['timesteps'],
                x_axis_label_str = 'Time Steps',
                y_data_df_list = [[data_df['close'], data_df['trade_signal']], [data_df['low'], data_df['high']]],
                y_data_label_str_list = [['Close', 'Trade Signal'], ['Low', 'High']],
                y_axes_label_str_list = ['Close Price, USD', 'Low, High Price, USD'],
                custom_heights_on = True,
                custom_heights_ratios_list = [3, 1],
                plot_title_str = f'Trade Signal / Strategy Plot for {ticker_str}',
                recent_data_chunk_int = None,
                save_on = False,
                save_file_name_str = f'TradeSignal_Strategy_Plot_{ticker_str}',
                save_path_str = ROOT_PATH + 'reports/plots/',
                show_on = True
            )

        if not multi_security_simulation_on:
            return 0.0
        else:
            return realized_pnl_flt, num_transactions_int


if __name__ == '__main__':
    # specify ticker symbol
    symbol_str = 'FLNG'

    # w1_generateTradeSignal_Strategy_EMA_KMA_MACD_RSI(
    #     ticker_str = symbol_str,
    #     plot_on = True,
    #     simulated_on = True
    # )

    # sepcify weights and threshold
    weights_dict = {
        'ma': 0.30,
        'macd': 0.25,
        'rsi': 0.20,
        'bb': 0.15,
        'zscore': 0.10
    }
    threshold_flt = 0.5

    w1_generateTradeSignal_Strategy_Comprehensive(
        ticker_str = symbol_str,
        weights_dict = weights_dict,
        thresold_flt = threshold_flt,
        recent_entries_bool = False,
        recent_entries_int = 16,
        plot_on = True,
        multi_security_simulation_on = False,
        no_stale_on = False,
        simulated_on = True
    )