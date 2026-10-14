# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] Inspired by chat model Haiku 4.5 with Reasoning
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

# import custom configs and utils
from data.w1_if_getHistoricalData import w1_if_getHistoricalData_D
from strategies.w2_appendATRIndicator import w2_appendATRIndicator


def w2_calculatePositionSize(
    account_size_flt,
    security_name_str,
    risk_per_trade_percentage_flt = 0.05,     
    multiplier_flt = 1.0,
    dbz_prevent_flt = 1e-6,
    simulated_on = True
):
    """
        description:
            Estimates a position size for a security by translating a fixed risk budget
            into a dollar-based quantity using the latest ATR-derived volatility.
        args:
            account_size_flt: float
                Total capital available for trading.
            security_name_str: str
                Ticker symbol to evaluate.
            risk_per_trade_percentage_flt: float, default 0.05
                Fraction of account equity that should be risked per trade.
            multiplier_flt: float, default 1.0
                Multiplier applied to the ATR value before sizing.
            dbz_prevent_flt: float, default 1e-6
                Small safeguard value to avoid division-by-zero issues.
            simulated_on: bool, default True
                Determines whether historical data should be retrieved from the simulated
                or live data pipeline.
        returns:
            int
                The calculated position size rounded down to an integer quantity.
    """
    # derive ATR indicator
    data_df = w2_appendATRIndicator(
        timeseries_df = w1_if_getHistoricalData_D(
            ticker_str = security_name_str,
            in_loop_on = False,
            simulated_on = simulated_on
        )
    )

    # calculate dollar risk
    dollar_risk_flt = account_size_flt * risk_per_trade_percentage_flt

    # calculate ATR (with multiplier)
    atr_with_multiplier_flt = float(data_df['atr'].iloc[-1]) * multiplier_flt

    # calculate position size
    position_size_int = int(dollar_risk_flt / (atr_with_multiplier_flt + dbz_prevent_flt))

    return position_size_int


if __name__ == '__main__':
    # specify ticker symbol
    ticker_str = 'IAUM'

    print(
        w2_calculatePositionSize(
            account_size_flt = 500.0,
            security_name_str = ticker_str,
            risk_per_trade_percentage_flt = 0.05,
            multiplier_flt = 1.0,
            simulated_on = True
        )
    )