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

from progiter.manager import ProgressManager

# import custom configs and utils
from config import (
    ROOT_PATH,
    TRADE_PRICE_LOWER_LIMIT,
    TRADE_PRICE_UPPER_LIMIT,
    TRADE_VOLUME_LOWER_LIMIT,
    TRADE_RECENT_DATA_CHUNK_RL_INFERENCE
)

from data.w1_if_getHistoricalData import w1_if_getHistoricalData_D
from data.w2_filterTickerSelection import w2_filterTickerSelection
from utils.w2_performDataFrameOps import w2_readJSONToDataFrame, w2_writeDataFrameToCSV
from utils.w2_performHDF5Ops import w2_readDataFromHDF5, w2_writeDataToHDF5


def w1_refineTickers_PriceThreshold(
        tickers_dir_str = 'data/tickers/',
        save_refined_tickers_on = True,
        scanned_tickers_dir_str = 'data/scans/',
        price_upper_limit_flt = TRADE_PRICE_UPPER_LIMIT,
        price_lower_limit_flt = TRADE_PRICE_LOWER_LIMIT,
        volume_lower_limit_flt = TRADE_VOLUME_LOWER_LIMIT,
        simulated_on = True
):
    """
        description:
            A function that refines the ticker symbols first selected using w1_if_getTickers.py, and also calls
            w2_filterTickerSelection.py to filter based on last sale price, market capitalization, country and industry

            NOTE: This function refines the ticker symbols based on price limits set by the arguments and whether
            appropriate amount of daily data can be accessed for the ticker symbol.

        args:
            tickers_dir_str
            save_refined_tickers_on
            scanned_tickers_dir_str
            price_upper_limit_flt
            price_lower_limit_flt
            simulated_on

        returns:
            n/a
    """
    # check contents of the ticker directory
    contents_list = os.listdir(ROOT_PATH + tickers_dir_str)
    if contents_list:
        # remove existing scan file
        for file_name_str in contents_list:
            if file_name_str == 'price_threshold_scan_list.h5':
                os.remove(ROOT_PATH + scanned_tickers_dir_str + file_name_str)
                
        # generate new scan file
        for file_name_str in contents_list:
            if file_name_str == 'tickers.json':
                try:
                    # initialize progress manager
                    prog_manager_obj = ProgressManager()

                    # ====
                    # filter as required
                    refined_tickers_df = w2_filterTickerSelection(
                        data_df = w2_readJSONToDataFrame(ROOT_PATH + tickers_dir_str + 'tickers.json')
                    )

                    # ====
                    # save refined tickers information
                    if save_refined_tickers_on:
                        w2_writeDataFrameToCSV(df = refined_tickers_df, file_path = ROOT_PATH + scanned_tickers_dir_str + 'refined_tickers.csv')

                    # ====
                    # [in loop] extract prices
                    print()
                    refined_tickers_cnt_int = 0
                    with prog_manager_obj:
                        for index_int in prog_manager_obj.progiter(range(len(refined_tickers_df))):
                            try:
                                if price_lower_limit_flt <= float(str(refined_tickers_df['lastsale'].iloc[index_int]).replace('$', '')) <= price_upper_limit_flt:
                                    # get ticker symbol
                                    ticker_str = str(refined_tickers_df['symbol'].iloc[index_int])

                                    # check if prices can be downloaded
                                    data_df = w1_if_getHistoricalData_D(
                                        ticker_str = ticker_str,
                                        in_loop_on = True,
                                        simulated_on = simulated_on
                                    )

                                    # check if data length is sufficient and traded volume is above volume lower limit for any given day
                                    if len(data_df) > TRADE_RECENT_DATA_CHUNK_RL_INFERENCE:
                                        if all(x > volume_lower_limit_flt for x in list(data_df['volume'].values)):
                                            # increment refined tickers count
                                            refined_tickers_cnt_int += 1

                                            # read stored data
                                            refined_tickers_list = w2_readDataFromHDF5(
                                                save_path_str = ROOT_PATH + scanned_tickers_dir_str + 'price_threshold_scan_list.h5'
                                            )

                                            # write data
                                            if ticker_str not in refined_tickers_list:
                                                refined_tickers_list.append(ticker_str)
                                                w2_writeDataToHDF5(
                                                    save_path_str = ROOT_PATH + scanned_tickers_dir_str + 'price_threshold_scan_list.h5',
                                                    data_shape_tpl = (refined_tickers_cnt_int,),
                                                    data_list = refined_tickers_list
                                                )

                                            # print statement
                                            # print()
                                            # print('INFO: Selection conditions were met for {}...'.format(ticker_str))
                                            # print()

                            except KeyError:
                                # print statement
                                # print()
                                # print('WARNING: Exception detected for {}...'.format(ticker_str))
                                # print()
                                continue

                except KeyboardInterrupt:
                    print('INFO: Session interrupted...')


if __name__ == '__main__':
    w1_refineTickers_PriceThreshold(
        price_upper_limit_flt = TRADE_PRICE_UPPER_LIMIT,
        price_lower_limit_flt = TRADE_PRICE_LOWER_LIMIT,
        volume_lower_limit_flt = TRADE_VOLUME_LOWER_LIMIT,
        simulated_on = True
    )