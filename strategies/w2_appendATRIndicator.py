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
import pandas as pd


def w2_appendATRIndicator(
        timeseries_df,
        period_int = 14
    ):
    """
    Append the Average True Range (ATR) indicator to the time series DataFrame.

    ATR is calculated as the rolling mean of the true range over the provided
    period. The true range is the maximum of:
        - high - low
        - abs(high - previous close)
        - abs(low - previous close)

    Parameters:
        timeseries_df (pd.DataFrame): Time series data containing 'high', 'low', and 'close' columns.
        period_int (int): Rolling window period for ATR calculation. Defaults to 14.

    Returns:
        pd.DataFrame: The input DataFrame with a new 'atr' column appended.
    """
    # calculate Average True Range indicator
    high_low_df = timeseries_df['high'] - timeseries_df['low']
    high_close_df = np.abs(timeseries_df['high'] - timeseries_df['close'].shift())
    low_close_df = np.abs(timeseries_df['low'] - timeseries_df['close'].shift())

    tr_df = pd.concat([high_low_df, high_close_df, low_close_df], axis = 1).max(axis = 1)
    timeseries_df['atr'] = tr_df.rolling(window = period_int).mean()

    return timeseries_df


if __name__ == '__main__':
    # specify ticker symbol
    ticker_str = 'AAPL'

    # import dependencies
    from data.w1_if_getHistoricalData import w1_if_getHistoricalData_M
    from utils.w2_performDataFrameOps import w2_setColumnAsIndex

    # download data
    timeseries_df = w2_setColumnAsIndex(
        df = w1_if_getHistoricalData_M(
            ticker_str = ticker_str,
            in_loop_on = False,
            simulated_on = True
        ),
        column_to_index_name_str = 'date',
        drop_column = True
    )

    print(w2_appendATRIndicator(timeseries_df = timeseries_df))