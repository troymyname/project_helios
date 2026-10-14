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

# import custom configs and utils
from strategies.w2_appendSMATracker import w2_appendSMATracker


def w2_appendBBIndicator(
        timeseries_df,
        calculation_column_name_str = 'close',
        period_int = 20,
        std_dev_flt = 2.0
    ):
    """
    Append Bollinger Band indicator columns to the time series DataFrame.

    The function computes a simple moving average over the specified period and
    then derives the upper and lower bands using the rolling standard deviation
    multiplied by the provided standard deviation factor.

    Parameters:
        timeseries_df (pd.DataFrame): Input DataFrame containing price data.
        calculation_column_name_str (str): Column name used for band calculation.
        period_int (int): Window length for the moving average and standard deviation.
        std_dev_flt (float): Number of standard deviations away from the middle band.

    Returns:
        pd.DataFrame: DataFrame with 'bb_middle', 'bb_upper', and 'bb_lower' columns added.
    """
    # calculate Bollinger Bands indicator
    timeseries_df = w2_appendSMATracker(
        timeseries_df = timeseries_df,
        calculation_column_name_str = calculation_column_name_str,
        window_int = period_int
    )
    timeseries_df['bb_middle'] = timeseries_df['sma']
    std_df = timeseries_df['close'].rolling(window = period_int).std()
    timeseries_df['bb_upper'] = timeseries_df['bb_middle'] + (std_dev_flt * std_df)
    timeseries_df['bb_lower'] = timeseries_df['bb_middle'] - (std_dev_flt * std_df)

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

    print(w2_appendBBIndicator(timeseries_df = timeseries_df))