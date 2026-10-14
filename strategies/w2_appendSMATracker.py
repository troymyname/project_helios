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


def w2_appendSMATracker(
        timeseries_df,
        calculation_column_name_str = 'close',
        window_int = 21,
        new_column_name_str = 'sma'
    ):
    """
    Append a simple moving average (SMA) column to the time series DataFrame.

    Parameters:
        timeseries_df (pd.DataFrame): Input DataFrame containing the source series.
        calculation_column_name_str (str): Column name to compute the SMA from.
        window_int (int): Window length for the rolling mean.
        new_column_name_str (str): Name of the SMA column to append.

    Returns:
        pd.DataFrame: The input DataFrame with the new SMA column added.
    """
    # calculate exponentially weighted moving averages
    timeseries_df[new_column_name_str] = timeseries_df[calculation_column_name_str].rolling(window = window_int).mean()

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

    print(w2_appendSMATracker(
        timeseries_df = timeseries_df,
        calculation_column_name_str = 'close',
        window_int = 21,
        new_column_name_str = 'sma'
        )
    )