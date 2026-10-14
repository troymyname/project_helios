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


def w2_appendZScoreIndicator(
        timeseries_df,
        calculation_column_name_str = 'close',
        period_int = 20
    ):
    """
    Append a Z-score indicator column for mean-reversion analysis.

    The Z-score is computed as the difference between the current value and
    its simple moving average, divided by the rolling standard deviation over
    the same period.

    Parameters:
        timeseries_df (pd.DataFrame): Input DataFrame containing the source series.
        calculation_column_name_str (str): Name of the column to compute the Z-score from.
        period_int (int): Rolling window length used for moving average and standard deviation.

    Returns:
        pd.DataFrame: The input DataFrame with a new 'zscore' column appended.

    Notes:
        - Z-score > 2.0 is typically interpreted as overvalued.
        - Z-score < -2.0 is typically interpreted as undervalued.
    """
    # calculate Z-Score
    timeseries_df = w2_appendSMATracker(
        timeseries_df = timeseries_df,
        calculation_column_name_str = calculation_column_name_str,
        window_int = period_int
    )
    std_df = timeseries_df[calculation_column_name_str].rolling(window = period_int).std()
    timeseries_df['zscore'] = (timeseries_df[calculation_column_name_str] - timeseries_df['sma'])/std_df

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

    print(w2_appendZScoreIndicator(timeseries_df = timeseries_df))