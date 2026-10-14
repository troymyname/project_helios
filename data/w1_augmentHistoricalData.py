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

# ignore warnings
import warnings
from config import WARNING_IGNORE_CLASS_FUTURE
warnings.simplefilter(action = 'ignore', category = WARNING_IGNORE_CLASS_FUTURE)

import numpy as np
import random

from datetime import datetime

# import custom configs and utils
from data.w1_if_getHistoricalData import w1_if_getHistoricalData_D, w1_if_getHistoricalData_M
from utils.w2_performDataFrameOps import (
    w2_customFillForward,
    w2_dropRowsWithNANResetIndex,
    w2_renameColumns,
    w2_resetIndex
)
from utils.w2_simulateBrownianMotion import w2_simulatePriceInBrownianMotion


def w1_augmentHistoricalData_M(
        ticker_str,
        daily_data_chunk_int = 10,
        mu_flt = 0.01,
        sigma_flt = 0.01,
        simulated_on = True
    ):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # derive minutely data
    minutely_data_df = w2_dropRowsWithNANResetIndex(
        df = w1_if_getHistoricalData_M(
            ticker_str = ticker_str,
            in_loop_on = False,
            simulated_on = simulated_on
        )
    )

    # convert date column from pandas._libs.tslibs.timestamps.Timestamp to datetime.datetime
    # NOTE: The output of datetime.strptime is a datetime object.
    minutely_data_df['date_dt'] = ''
    for indx in range(len(minutely_data_df)):
        minutely_data_df.loc[indx, 'date_dt'] = datetime.strptime(str(minutely_data_df.loc[indx, 'date'])[:19], '%Y-%m-%d %H:%M:%S')
    minutely_data_df = minutely_data_df[
        [
            'date_dt', 'open', 'high', 'low', 'close'
        ]
    ]
    minutely_data_df = w2_renameColumns(
        df = minutely_data_df,
        column_mapping_dict = {'date_dt': 'date'}
    )

    # ====

    # derive daily data
    daily_data_df = w2_dropRowsWithNANResetIndex(
        df = w1_if_getHistoricalData_D(
            ticker_str = ticker_str,
            in_loop_on = False,
            simulated_on = simulated_on
        )[-daily_data_chunk_int:]
    )

    # convert date column from pandas._libs.tslibs.timestamps.Timestamp to datetime.datetime
    # NOTE: The output of datetime.strptime is a datetime object.
    daily_data_df['date_dt'] = ''
    daily_data_df['augmented_price'] = 0.0
    for indx in range(len(daily_data_df)):
        daily_data_df.loc[indx, 'date_dt'] = datetime.strptime(str(daily_data_df.loc[indx, 'date'])[:10], '%Y-%m-%d')
        daily_data_df.loc[indx, 'augmented_price'] = round(
            np.average(
                [
                    daily_data_df.loc[indx, 'open'],
                    daily_data_df.loc[indx, 'high'],
                    daily_data_df.loc[indx, 'low'],
                    daily_data_df.loc[indx, 'close']
                ]
            ),
            2
        )
    daily_data_df = daily_data_df[
        [
            'date_dt', 'open', 'high', 'low', 'close', 'augmented_price'
        ]
    ]
    daily_data_df = w2_renameColumns(
        df = daily_data_df,
        column_mapping_dict = {'date_dt': 'date'}
    )

    # ====

    # generate augmented minutely data
    augmented_minutely_df = w2_resetIndex(
        w2_customFillForward(
            df = daily_data_df,
            interval_str = '1m'
        ).between_time('09:30:00', '15:59:00') # Total Steps = 390
    )
    for indx in range(len(augmented_minutely_df)):
        if str(augmented_minutely_df.loc[indx, 'date'])[11:] == '15:59:00':
            _, simulated_values_arr = w2_simulatePriceInBrownianMotion(
                initial_value_flt = augmented_minutely_df.loc[indx - 390 + 1, 'augmented_price'],
                samples_int = 390 - 2,
                timespan_int = 1,
                mu_flt = mu_flt if augmented_minutely_df.loc[indx, 'close'] > augmented_minutely_df.loc[indx, 'open'] else -mu_flt,
                sigma_flt = sigma_flt
            )
            # replace forward-filled section of augmented data with simulated values
            augmented_minutely_df.loc[indx - 390 + 1:indx - 1, 'augmented_price'] = simulated_values_arr
            # implant open, high, low, close prices
            augmented_minutely_df.loc[indx - 390 + 1, 'augmented_price'] = augmented_minutely_df.loc[indx, 'open']
            augmented_minutely_df.loc[random.randint(a = indx - 390 + 2, b = indx - 1), 'augmented_price'] = augmented_minutely_df.loc[indx, 'high']
            augmented_minutely_df.loc[random.randint(a = indx - 390 + 2, b = indx - 1), 'augmented_price'] = augmented_minutely_df.loc[indx, 'low']
            augmented_minutely_df.loc[indx, 'augmented_price'] = augmented_minutely_df.loc[indx, 'close']

    # replace last augmented prices using real 'close' price column from minutely data
    for indx in range(-len(minutely_data_df), 0, 1):
        augmented_minutely_df.loc[indx, 'date'] = minutely_data_df['date'].iloc[indx]
        augmented_minutely_df.loc[indx, 'augmented_price'] = minutely_data_df['close'].iloc[indx]

    # remove columns that are not needed
    augmented_minutely_df = w2_dropRowsWithNANResetIndex(
        df = augmented_minutely_df[['date', 'augmented_price']]
    )

    return augmented_minutely_df


if __name__ == '__main__':
    # specify ticker symbol
    ticker_str = 'IAUM'

    # import dependencies
    from utils.w2_plot import w2_plotQuickly

    # derive and plot outputs
    output_df = w1_augmentHistoricalData_M(
        ticker_str = ticker_str,
        simulated_on = True
    )
    last_time_str = str(output_df['date'].iloc[-1])

    w2_plotQuickly(
        x_data_arr = range(len(output_df)),
        x_axis_label_str = 'Time Step',
        y_data_arr_list = [list(output_df['augmented_price'])],
        y_data_label_str_list = [f'Minutely Price for {ticker_str}'],
        y_axis_label_str = 'Minutely Price (USD)',
        plot_title_str = f'Historical Prices with Last Time Step at {last_time_str}',
        show_on = True
    )