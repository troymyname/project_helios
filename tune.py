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

import os
os.environ['TUNE_DISABLE_STRICT_METRIC_CHECKING'] = '1'

import random

# import custom configs and utils
from config import TUNE_INITIAL_BALANCE, QUANTITY, ROOT_PATH
from config import RAY_ALGO_TYPE, RAY_REWARD_SELECTOR, RAY_REWARD_WEIGHTS
from config import RAY_TUNE_CHECKPOINT_FREQUENCY, RAY_TUNE_PARAM_SPACE, RAY_TUNE_RECENT_DATA_CHUNK, RAY_TUNE_SEED, RAY_TUNE_TICKER_SAMPLES
from config_enums import ActionSignal, OperationMode
from data.w1_if_getTickers import w1_if_getTickers
from data.w2_filterTickerSelection import w2_filterTickerSelection
from strategies.w1_RLStrategy import RLStrategy
from utils.w2_clearPreviousSessionData import w2_clearPreviousSessionData
from utils.w2_performHDF5Ops import w2_readDataFromHDF5


def tune(
        tune_ticker_samples_int,
        scanned_tickers_selection = False, # NOTE: With this option, the w1_if_refineTickers_##.py needs to be run first.
        scanned_tickers_dir_str = 'data/scans/',
        simulated_on = True
):
    """
        description:
            Orchestrates a Ray Tune hyperparameter search for the reinforcement-learning
            trading strategy. The function clears prior session artifacts, builds a ticker
            universe for the run, samples a subset of symbols, instantiates an RLStrategy
            in training mode, and launches tuning with the configured seed, checkpoint
            cadence, and parameter search space.
        args:
            tune_ticker_samples_int: int
                Number of tickers to sample from the filtered universe for this tuning run.
            scanned_tickers_selection: bool, default False
                When True, uses a precomputed ticker list from a scan output directory
                instead of re-running the standard ticker-selection pipeline.
            scanned_tickers_dir_str: str, default 'data/scans/'
                Directory containing the precomputed scan list when
                `scanned_tickers_selection` is True.
            simulated_on: bool, default True
                Determines whether the strategy runs in simulated or live-trading mode
                during tuning.
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
    assert tune_ticker_samples_int <= len(tickers_str_list)
    sampled_tickers_list = random.sample(
        population = tickers_str_list,
        k = tune_ticker_samples_int
    )

    # tune hyperparameters ('seed_int = 0' means no seed set)
    strategy_object = RLStrategy(
        operation_enum = OperationMode.TRAIN,
        algorithm_type_str = RAY_ALGO_TYPE,
        sampled_tickers_list = sampled_tickers_list,
        initial_balance_flt = TUNE_INITIAL_BALANCE,
        recent_data_chunk_int = RAY_TUNE_RECENT_DATA_CHUNK,
        reward_config_arr = RAY_REWARD_SELECTOR,
        reward_config_weights_arr = RAY_REWARD_WEIGHTS,
        quantity_int = QUANTITY,
        num_actions_int = len(ActionSignal),
        tick_interval_str = 'daily',
        simulated_on = simulated_on
    )
    strategy_object.tune(
        seed_int = RAY_TUNE_SEED,
        checkpoint_frequency_int = RAY_TUNE_CHECKPOINT_FREQUENCY,
        param_space_dict = RAY_TUNE_PARAM_SPACE
    )


if __name__ == '__main__':
    tune(
        tune_ticker_samples_int = RAY_TUNE_TICKER_SAMPLES,
        simulated_on = True
    )