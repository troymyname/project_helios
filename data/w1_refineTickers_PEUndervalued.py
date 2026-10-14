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

from datetime import datetime
from progiter.manager import ProgressManager

# import custom configs and utils
from config import ROOT_PATH, PE_RATIO_PROXIMITY_RANGE_PERCENTAGE
from utils.w2_performDataFrameOps import w2_dropRowsWithNANResetIndex, w2_keepOnlySelectedColumns, w2_readJSONToDataFrame, w2_writeDataFrameToCSV
from utils.w2_performDivision import w2_performDivision
from utils.w2_performHDF5Ops import w2_readDataFromHDF5, w2_writeDataToHDF5
from w1_if_getHistoricalData import w1_if_getHistoricalData_D
from w1_if_getFundamentals import w1_if_getFundamentals
from w2_filterTickerSelection import w2_filterTickerSelection


def w1_refineTickers_PEUndervalued(
        tickers_dir_str = 'data/tickers/',
        save_refined_tickers_on = True,
        scanned_tickers_dir_str = 'data/scans/',
        simulated_on = True
):
    """
        description:
            A function that refines the ticker symbols first selected using w1_if_getTickers.py, and also calls
            w2_filterTickerSelection to filter based on last sale price, market capitalization, country and industry

            NOTE: This function refines the ticker symbols based on P/E ratio.

        args:
            tickers_dir_str
            save_refined_tickers_on
            scanned_tickers_dir_str
            simulated_on

        returns:
            n/a

        references:
            [1] https://www.schwab.com/learn/story/stock-analysis-using-pe-ratio
    """
    # check contents of the ticker directory
    contents_list = os.listdir(ROOT_PATH + tickers_dir_str)
    if contents_list:
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
                    # shuffle refined tickers
                    refined_tickers_shuffled_list = list(refined_tickers_df['symbol'])
                    random.shuffle(refined_tickers_shuffled_list)

                    # ====
                    # [in loop] extract fundamentals and prices
                    print()
                    refined_tickers_cnt_int = 0
                    with prog_manager_obj:
                        for ticker_str in prog_manager_obj.progiter(refined_tickers_shuffled_list):
                            # get fundamentals (earnings per share)
                            fundamentals_data_dict = w1_if_getFundamentals(
                                    ticker_str = ticker_str,
                                    variable_name_str_list = ['EarningsPerShareBasic']
                            )
                            # get prices
                            prices_data_df = w1_if_getHistoricalData_D(
                                ticker_str = ticker_str,
                                in_loop_on = True,
                                simulated_on = simulated_on
                            )

                            if len(prices_data_df) != 0 and fundamentals_data_dict:
                                if len(fundamentals_data_dict[ticker_str]['EarningsPerShareBasic']) != 0:
                                    # format dataset 1 as needed and insert 2 additional columns
                                    try:
                                        prices_data_df = w2_dropRowsWithNANResetIndex(
                                            w2_keepOnlySelectedColumns(
                                                df = prices_data_df,
                                                selected_columns_str_list = ['date', 'close']
                                            )
                                        )
                                    except AssertionError:
                                        # NOTE: This is meant to catch the AssertionError triggered by w2_keepOnlySelectedColumns when required columns are missing.
                                        continue
                                    prices_data_df.insert(2, 'eps', 0.0)
                                    prices_data_df.insert(3, 'pe', 0.0)

                                    # format dataset 2 as needed
                                    try:
                                        fundamentals_data_df = w2_dropRowsWithNANResetIndex(
                                            w2_keepOnlySelectedColumns(
                                                df = fundamentals_data_dict[ticker_str]['EarningsPerShareBasic'],
                                                selected_columns_str_list = ['start', 'end', 'val']
                                            )
                                        )
                                    except AssertionError:
                                        # NOTE: This is meant to catch the AssertionError triggered by w2_keepOnlySelectedColumns when required columns are missing.
                                        continue

                                    # calculate price-to-earnings-ratio (closing price per share / earnings per share)
                                    pe_values_list = []
                                    for j in range(len(fundamentals_data_df)):
                                        start_dt = fundamentals_data_df.loc[j, 'start']
                                        end_dt = fundamentals_data_df.loc[j, 'end']
                                        for i in range(len(prices_data_df)):
                                            # operate between start date and end date
                                            try:
                                                if str(start_dt) <= str(datetime.strptime(str(prices_data_df.loc[i, 'date']), '%Y-%m-%d %H:%M:%S')) <= str(end_dt):
                                                    prices_data_df.loc[i, 'eps'] = fundamentals_data_df.loc[j, 'val']
                                                    prices_data_df.loc[i, 'pe'] = w2_performDivision(
                                                        numerator = prices_data_df.loc[i, 'close'],
                                                        denominator = prices_data_df.loc[i, 'eps']
                                                    )
                                                    if prices_data_df.loc[i, 'pe'] != 0.0:
                                                        pe_values_list.append(prices_data_df.loc[i, 'pe'])

                                                # break out of loop if end is reached
                                                if str(datetime.strptime(str(prices_data_df.loc[i, 'date']), '%Y-%m-%d %H:%M:%S')) == str(end_dt):
                                                    break

                                            # NOTE: Below exception was included because it was observed that data from IBAPI can contain a different format of date.
                                            # TODO: This type of discrepancy in date can be resolved upstream.
                                            except ValueError:
                                                if str(start_dt) <= str(datetime.strptime(str(prices_data_df.loc[i, 'date']), '%Y%m%d')) <= str(end_dt):
                                                    prices_data_df.loc[i, 'eps'] = fundamentals_data_df.loc[j, 'val']
                                                    prices_data_df.loc[i, 'pe'] = w2_performDivision(
                                                        numerator = prices_data_df.loc[i, 'close'],
                                                        denominator = prices_data_df.loc[i, 'eps']
                                                    )
                                                    if prices_data_df.loc[i, 'pe'] != 0.0:
                                                        pe_values_list.append(prices_data_df.loc[i, 'pe'])

                                                # break out of loop if end is reached
                                                if str(datetime.strptime(str(prices_data_df.loc[i, 'date']), '%Y%m%d')) == str(end_dt):
                                                    break

                                    """
                                    Theory for Selection Based on P/E Ratio: 
                                    'In general, if the company's current P/E is at the lower end of it's historical P/E
                                    range or below the average P/E of similar companies, it may be a sign that the stock is 
                                    undervalued - regardless of recent business performance.' - schwab.com
                                    """
                                    # check if undervalued
                                    if len(pe_values_list) > 0:
                                        # set condition of P/E value to be at lower end of its historical P/E
                                        condition1_bool = pe_values_list[-1] < (min(pe_values_list) + (max(pe_values_list) - min(pe_values_list))*PE_RATIO_PROXIMITY_RANGE_PERCENTAGE)
                                        # set condition of mean of n recent P/E values to be positive
                                        condition2_bool = np.mean(pe_values_list[-5:]) > 0.0

                                        if condition1_bool and condition2_bool:
                                            # increment refined tickers count
                                            refined_tickers_cnt_int += 1
                                            # read stored data
                                            refined_tickers_list = w2_readDataFromHDF5(
                                                save_path_str = ROOT_PATH + scanned_tickers_dir_str + 'pe_undervalued_scan_list.h5'
                                            )
                                            # write data
                                            if ticker_str not in refined_tickers_list:
                                                refined_tickers_list.append(ticker_str)
                                                w2_writeDataToHDF5(
                                                    save_path_str = ROOT_PATH + scanned_tickers_dir_str + 'pe_undervalued_scan_list.h5',
                                                    data_shape_tpl = (refined_tickers_cnt_int,),
                                                    data_list = refined_tickers_list
                                                )
                                            # print statement
                                            print()
                                            print()
                                            print('INFO: Selection conditions were met for {}...'.format(ticker_str))
                                            print()

                except KeyboardInterrupt:
                    print('INFO: Session interrupted...')


if __name__ == '__main__':
    w1_refineTickers_PEUndervalued(
        simulated_on = True
    )