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

 
def w2_appendKMATracker(
        timeseries_df,
        calculation_column_name_str = 'close',
        iterations_int = -1,
        new_column_name_str = 'kma'
    ):
    """
    Append a Kalman moving average tracker to a time series DataFrame.

    This function applies a simple Kalman filter to the specified input series,
    using fixed process and measurement variance parameters. The computed state
    estimates are appended as a new column to the input DataFrame.

    Parameters:
        timeseries_df (pd.DataFrame): Input DataFrame containing price data.
        calculation_column_name_str (str): Column name used as the observed series.
        iterations_int (int): Number of most recent observations to process. If -1,
            the full series is processed.
        new_column_name_str (str): Name of the output column for the Kalman estimate.

    Returns:
        pd.DataFrame: The input DataFrame with the Kalman moving average column appended.

    References:
        [1] https://scipy-cookbook.readthedocs.io/items/KalmanFiltering.html
        [2] https://www.cs.unc.edu/~welch/media/pdf/kalman_intro.pdf
    """
    # derive observations
    if iterations_int == -1:
        z_narr = np.array(list(timeseries_df[calculation_column_name_str]))
    else:
        z_narr = np.array(list(timeseries_df[calculation_column_name_str].iloc[-iterations_int:]))

    # derive required variables
    if iterations_int == -1:
        iterations_int = len(timeseries_df)
        array_size_tpl = (iterations_int,)
    else:
        array_size_tpl = (iterations_int,)

    # initialize required parameters
    # NOTE: 'Q_flt' and 'R_flt' are matched with backtests/w2_KalmanMovingAverage.py/KalmanMovingAverage.
    Q_flt = 0.05                                    # process/transition variance
    R_flt = 1.0                                     # measurement/observation variance estimate (can be tuned to achieve desired level of tracking)
    x_hat_narr = np.zeros(array_size_tpl)           # a-posteriori estimate of x
    P_narr = np.zeros(array_size_tpl)               # a-posteriori error estimate
    x_hat_neg_narr = np.zeros(array_size_tpl)       # a-priori estimate of x
    P_neg_narr = np.zeros(array_size_tpl)           # a-priori error estimate
    K_narr = np.zeros(array_size_tpl)               # Kalman gain

    # set initial values
    x_hat_narr[0] = z_narr[0]
    P_narr[0] = 0.0

    # run in loop
    for i in range(1, iterations_int):
        # perform time update
        x_hat_neg_narr[i] = x_hat_narr[i-1]
        P_neg_narr[i] = P_narr[i-1] + Q_flt

        # perform measurement update
        K_narr[i] = P_neg_narr[i] / (P_neg_narr[i] + R_flt)
        x_hat_narr[i] = x_hat_neg_narr[i] + (K_narr[i] * (z_narr[i] - x_hat_neg_narr[i]))
        P_narr[i] = (1 - K_narr[i]) * P_neg_narr[i]

    # append estimates to timeseries dataframe
    timeseries_df[new_column_name_str] = x_hat_narr

    return timeseries_df


if __name__ == '__main__':
    # specify ticker symbol
    ticker_str = 'AAPL'

    # import dependencies
    from config import ROOT_PATH
    from data.w1_if_getHistoricalData import w1_if_getHistoricalData_M
    from utils.w2_performDataFrameOps import w2_resetIndex, w2_setColumnAsIndex
    from utils.w2_plot import w2_plotInOneScale

    # download data
    timeseries_df = w2_resetIndex(
        w2_setColumnAsIndex(
            df = w1_if_getHistoricalData_M(
                ticker_str = ticker_str,
                in_loop_on = False,
                simulated_on = True
            ),
            column_to_index_name_str = 'date',
            drop_column = True
        )
    )

    print(w2_appendKMATracker(
        timeseries_df = timeseries_df
        )
    )

    # plot data
    w2_plotInOneScale(
        x_data_df = timeseries_df['date'],
        x_axis_label_str = 'Time',
        y_data_df_list = [timeseries_df['close'], timeseries_df['kma']],
        y_data_label_str_list = ['Close', 'Kalman Moving Average'],
        y_axis_label_str = 'Price (USD)',
        plot_title_str = f'Minutely Price Data for {ticker_str}',
        recent_data_chunk_int = 1000,
        save_on = True,
        save_file_name_str = 'DailyPriceData_KO',
        save_path_str = ROOT_PATH + 'reports/plots/',
        show_on = True
    )
