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
from config import TRADE_VOLUME_LOWER_LIMIT
from config_banned import BANNED_AMEX_TICKERS, BANNED_COUNTRIES, BANNED_INDUSTRIES, BANNED_NASDAQ_TICKERS, BANNED_NYSE_TICKERS
from utils.w2_performDataFrameOps import w2_dropRowsByIndices


def w2_filterTickerSelection(
        data_df,
        filter_by_last_sale_on = True,
        last_sale_thresh = 1.0,
        filter_by_market_cap_on = True,
        market_cap_thresh = TRADE_VOLUME_LOWER_LIMIT,
        filter_by_country_on = True,
        filter_by_industry_on = True,
        filter_by_custom_lists_on = True,
):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # ====
    # filter by last sale price (penny stocks) and market capitalization (higher trading)
    if filter_by_last_sale_on and filter_by_market_cap_on:
        indices_list = []
        for i in range(len(data_df)):
            # NOTE: Below exceptions handling was included to remove indices that do not have the proper information available.
            try:
                if float(data_df.loc[i, 'lastsale'].replace('$', '')) < last_sale_thresh or float(data_df.loc[i, 'marketCap']) < market_cap_thresh:
                    indices_list.append(i)
            except ValueError:
                indices_list.append(i)
                continue
        data_df = w2_dropRowsByIndices(
            df = data_df,
            indices_list = indices_list
        )

    # ====
    # filter by country
    if filter_by_country_on:
        data_df = data_df.loc[~data_df['country'].isin(BANNED_COUNTRIES)]

    # ====
    # filter by industry
    if filter_by_industry_on:
        data_df = data_df.loc[~data_df['industry'].isin(BANNED_INDUSTRIES)]

    # ====
    # filter by custom banned lists
    if filter_by_custom_lists_on:
        custom_banned_tickers_list = BANNED_AMEX_TICKERS + BANNED_NASDAQ_TICKERS + BANNED_NYSE_TICKERS
        data_df = data_df.loc[~data_df['symbol'].isin(custom_banned_tickers_list)]

    # ====
    # reset index before returning
    data_df = data_df.reset_index(drop = True)

    return data_df