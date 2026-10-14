# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] Inspired by chat model Haiku 4.5 with Reasoning
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
    TRADE_RECENT_DATA_CHUNK_SCAN
)

from data.w1_if_getHistoricalData import w1_if_getHistoricalDataInThreadsMain
from data.w2_filterTickerSelection import w2_filterTickerSelection
from strategies.w2_appendRSIIndicator import w2_appendRSIIndicator
from strategies.w2_appendSMATracker import w2_appendSMATracker
from utils.w2_performDataFrameOps import w2_readJSONToDataFrame, w2_writeDataFrameToCSV
from utils.w2_performHDF5Ops import w2_readDataFromHDF5, w2_writeDataToHDF5
from utils.w2_preprocessIBKRResponse import w2_preprocessIBKRResponseDataFrame


def w1_refineTickers_FavourableBuyCondition(
        tickers_dir_str = 'data/tickers/',
        save_refined_tickers_on = True,
        scanned_tickers_dir_str = 'data/scans/',
        price_upper_limit_flt = TRADE_PRICE_UPPER_LIMIT,
        price_lower_limit_flt = TRADE_PRICE_LOWER_LIMIT,
        volume_lower_limit_flt = TRADE_VOLUME_LOWER_LIMIT,
        recent_data_chunk_int = TRADE_RECENT_DATA_CHUNK_SCAN,
        simulated_on = True
):
    """
        description:
            A function that refines the ticker symbols first selected using w1_if_getTickers.py
            This function also calls w2_filterTickerSelection.py to filter based on favourable buy conditions
            generated when security history shows long-term growth and short-term pull-back.

        args:
            tickers_dir_str
            save_refined_tickers_on
            scanned_tickers_dir_str
            price_upper_limit_flt
            price_lower_limit_flt
            volume_lower_limit_flt
            recent_data_chunk_flt
            simulated_on

        returns:
            n/a
    """
    # check contents of the ticker directory
    contents_list = os.listdir(ROOT_PATH + tickers_dir_str)
    if contents_list:
        # remove existing scan file
        for file_name_str in contents_list:
            if file_name_str == 'favourable_buy_scan_list.h5':
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
                    # [in threads]
                    print()
                    ticker_str_list = []
                    with prog_manager_obj:
                        for index_int in prog_manager_obj.progiter(range(len(refined_tickers_df))):
                            try:
                                if price_lower_limit_flt <= float(str(refined_tickers_df['lastsale'].iloc[index_int]).replace('$', '')) <= price_upper_limit_flt:
                                    # get ticker symbol
                                    ticker_str = str(refined_tickers_df['symbol'].iloc[index_int])
                                    ticker_str_list.append(ticker_str)

                            except KeyError:
                                continue
                            
                    print()
                    # get historical data in multiple threads (without saving)
                    # NOTE: Using threads, a maximum limit of 251 data rows are provided.
                    data_dict = w1_if_getHistoricalDataInThreadsMain(
                        ticker_str_list = ticker_str_list,
                        data_path_str = 'data/daily/',
                        resolution_str = 'daily',
                        simulated_on = simulated_on
                    )
                    
                    # ====
                    # [in loop]
                    print()
                    refined_tickers_cnt_int = 0
                    with prog_manager_obj:
                        for index_int in prog_manager_obj.progiter(range(len(refined_tickers_df))):
                            try:
                                if price_lower_limit_flt <= float(str(refined_tickers_df['lastsale'].iloc[index_int]).replace('$', '')) <= price_upper_limit_flt:
                                    # get ticker symbol
                                    ticker_str = str(refined_tickers_df['symbol'].iloc[index_int])

                                    # extract dataframe based on ticker symbol if data was downloaded
                                    data_df = data_dict[ticker_str]

                                    # pre-process IBKR response dataframe
                                    data_df = w2_preprocessIBKRResponseDataFrame(
                                        df = data_df
                                    )

                                    # check if data length is sufficient, and if so, proceed
                                    if len(data_df) > recent_data_chunk_int:
                                        # check for liquidity (average of last 20-day volume greater than some threshold)
                                        avg_volume_flt = data_df['volume'].tail(20).mean()
                                        liquidity_ok = avg_volume_flt > volume_lower_limit_flt

                                        # check for integrity or "bullishness" (current price greater than 20-day SMA)
                                        data_df = w2_appendSMATracker(
                                            timeseries_df = data_df,
                                            window_int = 20
                                        )
                                        latest_close_flt = data_df['close'].iloc[-1].item()
                                        latest_sma_200_flt = data_df['sma'].iloc[-1].item()
                                        integrity_ok = latest_close_flt > latest_sma_200_flt

                                        # check for favourability (14-day RSI for last n days less than 35)
                                        data_df = w2_appendRSIIndicator(
                                            timeseries_df = data_df,
                                            rsi_period_int = 14
                                        )
                                        latest_5_rsi_list = list(data_df['rsi'].iloc[-10:])
                                        favourability_ok = any(x < 35.0 for x in latest_5_rsi_list)

                                        if liquidity_ok and integrity_ok and favourability_ok:
                                            # increment refined tickers count
                                            refined_tickers_cnt_int += 1

                                            # read stored data
                                            refined_tickers_list = w2_readDataFromHDF5(
                                                save_path_str = ROOT_PATH + scanned_tickers_dir_str + 'favourable_buy_scan_list.h5'
                                            )

                                            # write data
                                            if ticker_str not in refined_tickers_list:
                                                refined_tickers_list.append(ticker_str)
                                                w2_writeDataToHDF5(
                                                    save_path_str = ROOT_PATH + scanned_tickers_dir_str + 'favourable_buy_scan_list.h5',
                                                    data_shape_tpl = (refined_tickers_cnt_int,),
                                                    data_list = refined_tickers_list
                                                )

                            except KeyError:
                                continue

                except KeyboardInterrupt:
                    print('INFO: Session interrupted...')

        print(f'INFO: {refined_tickers_cnt_int} tickers stored in file "favourable_buy_scan_list.h5"...')


if __name__ == '__main__':
    w1_refineTickers_FavourableBuyCondition(
        simulated_on = True
    )