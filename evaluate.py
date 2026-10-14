# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1]
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import ast
import random

# import custom configs and utils
from config import EVAL_INITIAL_BALANCE, QUANTITY, ROOT_PATH
from config import RAY_ALGO_TYPE, RAY_EVAL_RECENT_DATA_CHUNK, RAY_EVAL_SEED, RAY_EVAL_TICKER_SAMPLES, RAY_REWARD_SELECTOR, RAY_REWARD_WEIGHTS
from config_enums import ActionSignal, OperationMode
from data.w1_if_getTickers import w1_if_getTickers
from strategies.w1_RLStrategy import RLStrategy
from data.w2_filterTickerSelection import w2_filterTickerSelection
from utils.w2_clearPreviousSessionData import w2_clearPreviousSessionData
from utils.w2_performHDF5Ops import w2_readDataFromHDF5


def evaluate(
        eval_ticker_samples_int,
        scanned_tickers_selection = True, # NOTE: With this option, the w1_if_refineTickers_##.py needs to be run first.
        scanned_tickers_dir_str = 'data/scans/',
        simulated_on = True
):
    """
        description:
            Runs an evaluation pass for the reinforcement-learning trading strategy.
            The function clears prior session artifacts, builds a ticker universe,
            samples a subset of symbols, instantiates an RLStrategy in evaluation mode,
            and uses the configured checkpoint settings to assess the strategy's
            performance on the selected market data.
        args:
            eval_ticker_samples_int: int
                Number of tickers to sample from the filtered universe for this evaluation run.
            scanned_tickers_selection: bool, default True
                When True, uses a precomputed ticker list from a scan output directory
                instead of re-running the standard ticker-selection pipeline.
            scanned_tickers_dir_str: str, default 'data/scans/'
                Directory containing the precomputed scan list when
                `scanned_tickers_selection` is True.
            simulated_on: bool, default True
                Determines whether the strategy is evaluated in simulated or live-trading mode.
        returns:
            None
        references:
            [1] https://docs.ray.io/en/latest/tune/api/env.html
    """
    # clear previous session data
    w2_clearPreviousSessionData(
        remove_tickers_on = False,
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

    # generate a list of randomly sampled tickers
    if scanned_tickers_selection:
        # get pre-selected tickers filtered based on fundamentals (else step is included)
        tickers_str_list = w2_readDataFromHDF5(
            save_path_str = ROOT_PATH + scanned_tickers_dir_str + 'price_threshold_scan_list.h5'
        )
    else:
        # get tickers, filter by based on specific criteria (currently, market cap., country, industry)
        tickers_str_list = list(w2_filterTickerSelection(data_df = w1_if_getTickers())['symbol'])

    # check if samples number is less than or equal to length of filtered tickers list, then randomly sample
    assert eval_ticker_samples_int <= len(tickers_str_list)
    sampled_tickers_list = random.sample(
        population = tickers_str_list,
        k = eval_ticker_samples_int
    )

    # evaluate using checkpoint ('seed_int = 0' means no seed set)
    strategy_object = RLStrategy(
        operation_enum = OperationMode.EVALUATE,
        algorithm_type_str = RAY_ALGO_TYPE,
        sampled_tickers_list = sampled_tickers_list,
        initial_balance_flt = EVAL_INITIAL_BALANCE,
        recent_data_chunk_int = RAY_EVAL_RECENT_DATA_CHUNK,
        reward_config_arr = RAY_REWARD_SELECTOR,
        reward_config_weights_arr = RAY_REWARD_WEIGHTS,
        quantity_int = QUANTITY,
        num_actions_int = len(ActionSignal),
        tick_interval_str = 'daily',
        simulated_on = simulated_on
    )
    _ = strategy_object.evaluate(
        seed_int = RAY_EVAL_SEED,
        num_episodes_during_inference_int = 1,
        explore_during_inference = True,
        data_save_on = True,
        plot_recent_data_chunk_int = 1000,
        plot_save_on = True,
        plot_save_file_name_str = 'last_eval_session',
        plot_save_path_str = ROOT_PATH + 'reports/plots/',
        plot_show_on = True
    )


def inferLastActionToTrade(
        sampled_tickers_list,
        recent_data_chunk_int,
        simulated_on = True
):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
        references:
            [1] https://docs.ray.io/en/latest/tune/api/env.html
    """
    # check length of sampled tickers list and ensure that it's equal to QUANTITY parameters
    assert len(sampled_tickers_list) >= QUANTITY
    # evaluate using checkpoint ('seed_int = 0' means no seed set)
    strategy_object = RLStrategy(
        operation_enum = OperationMode.EVALUATE,
        algorithm_type_str = RAY_ALGO_TYPE,
        sampled_tickers_list = sampled_tickers_list,
        initial_balance_flt = EVAL_INITIAL_BALANCE,
        recent_data_chunk_int = recent_data_chunk_int,
        reward_config_arr = RAY_REWARD_SELECTOR,
        reward_config_weights_arr = RAY_REWARD_WEIGHTS,
        quantity_int = QUANTITY,
        num_actions_int = len(ActionSignal),
        tick_interval_str = 'daily',
        simulated_on = simulated_on
    )
    inference_history_df = strategy_object.evaluate(
        seed_int = RAY_EVAL_SEED,
        num_episodes_during_inference_int = 1,
        explore_during_inference = True # TODO: It needs to be checked why setting this to False generates an error.
    )

    # derive last action dictionary
    last_action_dict = ast.literal_eval(inference_history_df['transactions'].iloc[-1])

    return last_action_dict


if __name__ == '__main__':
    evaluate(
        eval_ticker_samples_int = RAY_EVAL_TICKER_SAMPLES,
        simulated_on = True
    )