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
import pandas as pd
import riskfolio as rp

from copy import deepcopy
from datetime import datetime

# import custom configs and utils
from config import DATA_LENGTH_MIN, ROOT_PATH
from utils.w2_performDataFrameOps import (
    w2_calculatePercentageChange,
    w2_concatenateDataFramesInColumns,
    w2_dropRowsWithNANResetIndex,
    w2_generateDataFrame,
    w2_mergeDataFrames,
    w2_readCSVToDataFrame,
    w2_writeDataFrameToCSV
)


def w2_optimizePortfolio(picked_tickers_list, data_path = 'data/returns/', risk_measure_selection_str = 'MV'):
    """
        description:
            Builds a return series for the selected tickers, constructs a hierarchical
            risk-parity portfolio object, and optimizes portfolio weights using the
            requested risk metric.
        args:
            picked_tickers_list: list
                Tickers to include in the portfolio optimization.
            data_path: str, default 'data/returns/'
                Directory used to store return data artifacts.
            risk_measure_selection_str: str, default 'MV'
                Risk metric to optimize against, such as variance or drawdown.
        returns:
            dict
                Portfolio weights keyed by ticker symbol.
        details:
            Risk Measure Definitions:
            MV: Variance
            MAD: Mean Absolute Deviation
            GMD: Gini Mean Difference
            MSV: Semi Standard Deviation
            FLPM: First Lower Partial Moment (Omega Ratio)
            SLPM: Second Lower Partial Moment (Sortino Ratio)
            VaR: Conditional Value at Risk
            CVaR: Conditional Value at Risk
            TG: Tail Gini
            EVaR: Entropic Value at Risk
            WR: Worst Realization (Minimax)
            RG: Range of returns
            CVRG: CVaR Range of returns
            TGRG: Tail Gini Range of returns
            MDD: Maximum Drawdown of uncompounded cumulative returns (Calmar Ratio)
            ADD: Average Drawdown of uncompounded cumulative returns
            DaR: Drawdown at Risk of uncompounded cumulative returns
            CDaR: Conditional Drawdown at Risk of uncompounded cumulative returns
            EDaR: Entropic Drawdown at Risk of uncompounded cumulative returns
            UCI: Ulcer Index of uncompounded cumulative returns
            MDD_Rel: Maximum Drawdown of compounded cumulative returns (Calmar Ratio)
            ADD_Rel: Average Drawdown of compounded cumulative returns
            DaR_Rel: Drawdown at Risk of compounded cumulative returns
            CDaR_Rel: Conditional Drawdown at Risk of compounded cumulative returns
            EDaR_Rel: Entropic Drawdown at Risk of compounded cumulative returns
            UCI_Rel: Ulcer Index of compounded cumulative returns
    """
    temp_column_names_list = []
    temp_df = w2_generateDataFrame(data = {})
    data_df = w2_generateDataFrame(data = {})
    for ticker_str in picked_tickers_list:
        # access data file from directory if data file exists and file was modified the same day
        file_path_str = ROOT_PATH + 'data/daily/' + ticker_str + '.csv'
        if os.path.isfile(file_path_str) and (datetime.fromtimestamp(os.path.getmtime(file_path_str)) - datetime.now()).days <= 0:
            temp_df = w2_readCSVToDataFrame(
                file_path = file_path_str,
                index_col_str = 'date'
            )
        # generate and append column names
        temp_column_names_list.append(ticker_str)
        # pick and merge 'close' columns by 'date' column, rename column names each time (to avoid duplicates in column names)
        data_df = w2_mergeDataFrames(df1 = data_df, df2 = temp_df['close'][-DATA_LENGTH_MIN:], merge_column_str = 'date')
        data_df.columns = temp_column_names_list

    # calculate percentage change, drop rows with NAN values (do not reset index) and convert to dataframe with specific column names
    returns_df = w2_generateDataFrame(
        data = w2_dropRowsWithNANResetIndex(
            df = w2_calculatePercentageChange(
                df = w2_dropRowsWithNANResetIndex(
                    df = data_df
                )
            )
        ),
        columns_list = picked_tickers_list
    )

    # save returns data
    # NOTE: Below lines can be uncommented for debugging. This will only save the last returns_df.
    # w2_writeDataFrameToCSV(
    #     df = returns_df,
    #     file_path = ROOT_PATH + data_path + 'returns.csv'
    # )

    # build portfolio object
    portfolio_object = rp.HCPortfolio(returns = returns_df)

    # calculate weights based on risk measure(s) selection
    weights_df = pd.DataFrame([])
    if risk_measure_selection_str != 'all':
        risk_measure_weights_df = portfolio_object.optimization(
            model = 'HRP',
            codependence = 'pearson',
            obj = 'Sharpe',
            rm = risk_measure_selection_str,
            rf = 0,
            l = 2,
            linkage = 'single',
            max_k = 10,
            leaf_order = True
        )
        weights_df = deepcopy(risk_measure_weights_df)
        weights_df.columns = [risk_measure_selection_str]

    else:
        # specify list of all risk measures
        risk_measures_list = [
            'MV', 'MAD', 'GMD', 'MSV', 'FLPM', 'SLPM', 'VaR',
            'CVaR', 'TG', 'EVaR', 'WR', 'RG', 'CVRG', 'TGRG',
            'MDD', 'ADD', 'DaR', 'CDaR', 'EDaR', 'UCI', 'MDD_Rel',
            'ADD_Rel', 'DaR_Rel', 'CDaR_Rel', 'EDaR_Rel', 'UCI_Rel'
        ]

        for risk_measure_str in risk_measures_list:
            risk_measure_weights_df = portfolio_object.optimization(
                model = 'HRP',
                codependence = 'pearson',
                obj = 'Sharpe',
                rm = risk_measure_str,
                rf = 0,
                l = 2,
                linkage = 'single',
                max_k = 10,
                leaf_order = True
            )
            weights_df = w2_concatenateDataFramesInColumns(df1 = weights_df, df2 = risk_measure_weights_df)
        weights_df.columns = risk_measures_list

    # return weights in dictionary format
    return weights_df.to_dict()


if __name__ == '__main__':
    weights_dict = w2_optimizePortfolio(
        picked_tickers_list = ['ABCL', 'ACRE', 'AIM', 'AMS'],
        # risk_measure_selection_str = 'all'
    )
    print(weights_dict)