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

import math

# import custom configs and utils
from data.w1_if_getLiveData import w1_if_getLiveData


def w2_calculateAcquisitionQuantities(
        weights_dict,
        buying_power_flt,
        simulated_on = True
):
    """
        description:
            Calculates the number of shares that can be acquired for each ticker
            based on a target weight allocation and the available buying power.
            The function queries the latest live price for each ticker and floors
            the resulting position size to an integer quantity.
        args:
            weights_dict: dict
                Mapping of ticker symbols to target portfolio weights.
            buying_power_flt: float
                Total capital available for acquisition.
            simulated_on: bool, default True
                Determines whether to query simulated or live market data.
        returns:
            dict
                A dictionary mapping each ticker to the calculated acquisition quantity.
    """
    # calculate quantities that can be bought
    acquisition_quantities_dict = {}
    for ticker_str in list(weights_dict.keys()):
        # derive live price
        last_known_price_flt, _ = w1_if_getLiveData(
            ticker_str = ticker_str,
            simulated_on = simulated_on
        )
        # derive acquisition quantity
        if last_known_price_flt != 0.0:
            acquisition_quantities_dict[ticker_str] = math.floor(
                (buying_power_flt * weights_dict[ticker_str])/last_known_price_flt
            )
        else:
            acquisition_quantities_dict[ticker_str] = 0

    return acquisition_quantities_dict