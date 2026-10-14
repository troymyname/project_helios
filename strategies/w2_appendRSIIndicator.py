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

import talib


def w2_appendRSIIndicator(
        timeseries_df,
        calculation_column_name_str = 'close',
        rsi_period_int = 14,
        new_column_name_str = 'rsi'
):
    """
    Append a Relative Strength Index (RSI) column to the time series DataFrame.

    The RSI is calculated using the TA-Lib implementation based on price
    momentum over the specified period.

    Parameters:
        timeseries_df (pd.DataFrame): Input DataFrame containing the source series.
        calculation_column_name_str (str): Name of the column used for RSI calculation.
        rsi_period_int (int): Lookback period for the RSI calculation.
        new_column_name_str (str): Name of the RSI column to append.

    Returns:
        pd.DataFrame: The input DataFrame with a new RSI column appended.
    """
    # add relative strength index to dataframe
    timeseries_df[new_column_name_str] = talib.RSI(
        real = np.array(timeseries_df[calculation_column_name_str].values),
        timeperiod = rsi_period_int
    )

    return timeseries_df


if __name__ == '__main__':
    # specify ticker symbol
    ticker_str = 'VALE'

    # import dependencies
    from data.w1_if_getHistoricalData import w1_if_getHistoricalData_M

    # download data
    timeseries_df = w1_if_getHistoricalData_M(
        ticker_str = ticker_str,
        in_loop_on = False,
        simulated_on = True
    )

    print(w2_appendRSIIndicator(timeseries_df = timeseries_df))