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

import numpy as np
import os
import random

from progiter.manager import ProgressManager

# import custom configs and utils
from config import RNG_SEED, ROOT_PATH
from strategies.w1_generateTradeSignal import w1_generateTradeSignal_Strategy_Comprehensive
from utils.w2_performHDF5Ops import w2_readDataFromHDF5


def main(
        num_simulations_int,
        scanned_tickers_dir_str = 'data/scans/',
        scanned_file_name_str = 'favourable_buy_scan_list.h5',
        verbose_on = True,
        seed_int = RNG_SEED
):
    """
    Run multiple backtest simulations across a list of scanned tickers.

    This function loads a precomputed list of favourable tickers from an HDF5
    file, then performs a sequence of randomized backtest simulations by
    sampling weight allocations and threshold values. It aggregates P/L and
    transaction results, optionally printing progress and best-performing
    parameter settings.

    Parameters:
        num_simulations_int (int): Number of randomized backtest simulations to run.
        scanned_tickers_dir_str (str): Directory path containing the scanned ticker HDF5 file.
        scanned_file_name_str (str): Filename of the scanned ticker HDF5 dataset.
        verbose_on (bool): Whether to print progress and summary output.
        seed_int (int): Random seed for reproducibility.
    """
    # ====
    # ====
    # ====
    # initialize tunable parameters
    weights_dict_to_tune = {
        'ma': 0.00,
        'macd': 0.00,
        'rsi': 0.00,
        'bb': 0.00,
        'zscore': 0.00
    }
    threshold_flt_to_tune = 0.00
    # ====
    # ====
    # ====

    # set seed
    os.environ['PYTHONHASHSEED'] = str(seed_int)
    random.seed(seed_int)
    np.random.seed(seed_int)

    # initialize best cumulative realized p/l, best weights
    best_cumulative_realized_pnl = 0.0
    best_weights = {}

    for instance_int in range(1, num_simulations_int + 1):
        # determine random weights (np.ones(#) ensures equal weights)
        random_weights_narr = np.round(
            a = np.random.dirichlet(
                alpha = np.ones(5)
            ), 
            decimals = 2
        )

        # update weights
        for index, key in enumerate(weights_dict_to_tune.keys()):
            weights_dict_to_tune[key] = round(float(random_weights_narr[index]), 2)

        # determine random threshold
        threshold_flt_to_tune = round(random.uniform(a = 0.25, b = 0.5), 2)

        # initialize progress manager
        prog_manager_obj = ProgressManager()

        # print opening statement
        if verbose_on:
            print()
            print(f'INFO: Simulation: {instance_int}')
            print(f'INFO: Backtesting started with weights: {weights_dict_to_tune}...')
            print()

        # start the backtest
        transactions_sum = 0
        pnl_sum = 0.0
        count_int = 0
        with prog_manager_obj:
            for ticker_str in prog_manager_obj.progiter(
                w2_readDataFromHDF5(
                    save_path_str = ROOT_PATH + scanned_tickers_dir_str + scanned_file_name_str
                    )
            ):
                try:
                    pnl_flt, transactions_int = w1_generateTradeSignal_Strategy_Comprehensive(
                        ticker_str = ticker_str,
                        weights_dict = weights_dict_to_tune,
                        thresold_flt = threshold_flt_to_tune,
                        plot_on = True,
                        multi_security_simulation_on = True,
                        no_stale_on = True,
                        simulated_on = True
                    )
                    pnl_sum += pnl_flt
                    transactions_sum += transactions_int
                    count_int += 1
                except KeyError:
                    continue

        # print closing statement
        if verbose_on:
            print()
            print('INFO: Backtesting completed...')

            print()
            print(f'== Backtest Results for {count_int} tickers')
            print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
            print(f'== Total Number of Transactions: {transactions_sum}')
            if pnl_sum >= 0.0:
                print(f'== Cumulative Realized P/L: ${round(pnl_sum, 2)}')
            else:
                print(f'== Cumulative Realized P/L: -${round(abs(pnl_sum), 2)}')
            print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
            print()

        # update best cumulative realized p/l, best weights
        if not verbose_on:
            if pnl_sum > best_cumulative_realized_pnl:
                best_cumulative_realized_pnl = round(pnl_sum, 2)
                best_weights = weights_dict_to_tune
                best_threshold = threshold_flt_to_tune

    # print closing statement
    if not verbose_on:
        print()
        print('INFO: Backtesting completed...')
        print()
        print(f'== Best Cumulative Realized P/L: ${best_cumulative_realized_pnl}')
        print(f'== Best Weights: {best_weights}')
        print(f'== Best Threshold: {best_threshold}')
        print()


if __name__ == '__main__':
    # specify number of simulations
    num_simulations_int = 10000

    main(
        num_simulations_int = num_simulations_int,
        verbose_on = False
    )