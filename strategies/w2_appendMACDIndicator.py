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


def w2_appendMACDIndicator(
        timeseries_df,
        calculation_column_name_str = 'close',
        slow_span_int = 26,
        fast_span_int = 12,
        signal_span_int = 9
    ):
    """
    Append MACD and signal line columns to the input time series DataFrame.

    The function computes the MACD line as the difference between fast and slow
    exponential moving averages, and derives the signal line as the EMA of the
    MACD line over the specified signal span.

    Parameters:
        timeseries_df (pd.DataFrame): Input DataFrame containing the source column.
        calculation_column_name_str (str): Column name to calculate the MACD from.
        slow_span_int (int): Span parameter for the slow EMA.
        fast_span_int (int): Span parameter for the fast EMA.
        signal_span_int (int): Span parameter for the signal line EMA.

    Returns:
        pd.DataFrame: The same DataFrame with 'macd' and 'signal' columns appended.
    """
    # calculate Moving Average Convergence Divergence indicator
    slow_ewma_df = timeseries_df[calculation_column_name_str].ewm(span = slow_span_int, adjust = False).mean()
    fast_ewma_df = timeseries_df[calculation_column_name_str].ewm(span = fast_span_int, adjust = False).mean()
    timeseries_df['macd'] = fast_ewma_df - slow_ewma_df
    timeseries_df['signal'] = timeseries_df['macd'].ewm(span = signal_span_int, adjust = False).mean()

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

    print(w2_appendMACDIndicator(timeseries_df = timeseries_df))