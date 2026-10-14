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


def w2_appendEWMATracker(
        timeseries_df,
        calculation_column_name_str = 'close',
        span_int = 21,
        new_column_name_str = 'ewma'
    ):
    """
    Append an exponentially weighted moving average (EWMA) column to the DataFrame.

    Parameters:
        timeseries_df (pd.DataFrame): Input time series DataFrame containing the source column.
        calculation_column_name_str (str): Name of the column to compute the EWMA on.
        span_int (int): Span parameter for the EWMA calculation.
        new_column_name_str (str): Name of the new column to store the EWMA values.

    Returns:
        pd.DataFrame: The same DataFrame with the new EWMA column appended.
    """
    # calculate exponentially weighted moving averages
    timeseries_df[new_column_name_str] = timeseries_df[calculation_column_name_str].ewm(span = span_int, adjust = False).mean()

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

    print(w2_appendEWMATracker(
        timeseries_df = timeseries_df,
        calculation_column_name_str = 'close',
        span_int = 21,
        new_column_name_str = 'ewma'
        )
    )