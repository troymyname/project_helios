# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://github.com/ranaroussi/quantstats/blob/main/quantstats/stats.py
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import numpy as np

# import custom configs and utils
from utils.w2_performDataFrameOps import w2_calculateRollingWindowMinMax


def w2_calculateAutoCorrelationPenalty(returns_narr):
    """
        description:
            Computes a penalty factor that accounts for autocorrelation in a return series.
            The penalty is used to temper risk-adjusted metrics when returns are serially correlated.
        args:
            returns_narr: numpy.ndarray
                Return series to analyze.
        returns:
            float
                The calculated autocorrelation penalty factor, which is at least one.
    """
    num = len(returns_narr)

    # calculate autocorrelation coefficient between consecutive returns_narr
    coef = np.abs(np.corrcoef(returns_narr[:-1], returns_narr[1:])[0, 1])

    # vectorize calculation instead of list comprehension
    x = np.arange(1, num)

    # calculate weighted correlation effects over time
    corr = ((num - x) / num) * (coef**x)

    # return penalty factor (square root of 1 + 2 * sum of correlations)
    return np.sqrt(1 + 2 * np.sum(corr))


def w2_calculateSharpe(returns_narr, period_int = 252, smart_on = True, annualize_on = True):
    """
        description:
            Calculates the Sharpe ratio for a return series, optionally applying an
            autocorrelation penalty and annualizing the result.
        args:
            returns_narr: numpy.ndarray
                Return series to analyze.
            period_int: int, default 252
                Number of periods per year used when annualizing the ratio.
            smart_on: bool, default True
                Whether to penalize the denominator for autocorrelation.
            annualize_on: bool, default True
                Whether to annualize the result.
        returns:
            float
                The calculated Sharpe ratio.
    """
    # calculate standard deviation as denominator
    divisor = float(np.std(returns_narr, ddof = 1))

    # apply autocorrelation penalty if smart mode enabled
    if smart_on:
        # penalize Sharpe with autocorrelation
        divisor = divisor * w2_calculateAutoCorrelationPenalty(returns_narr)

    # calculate base Sharpe ratio
    result_flt = returns_narr.mean() / divisor

    # annualize if requested
    if annualize_on:
        return result_flt * np.sqrt(1 if period_int is None else period_int)

    return result_flt


def w2_calculateSmartSharpe(returns_narr, period_int = 252, annualize_on = True):
    """
        description:
            Computes the Sharpe ratio with the autocorrelation penalty enabled.
            This is a convenience wrapper for the more general Sharpe helper.
        args:
            returns_narr: numpy.ndarray
                Return series to analyze.
            period_int: int, default 252
                Number of periods per year used when annualizing the ratio.
            annualize_on: bool, default True
                Whether to annualize the ratio.
        returns:
            float
                The smart Sharpe ratio.
    """
    return w2_calculateSharpe(
        returns_narr = returns_narr,
        period_int = period_int,
        smart_on = True,
        annualize_on = annualize_on
    )


def w2_calculatePeaksAndTroughs(closing_price_df, window_int = 252):
    """
        description:
            Identifies local maxima and minima in a price series using rolling window logic.
        args:
            closing_price_df: pandas.DataFrame
                Price series indexed by time.
            window_int: int, default 252
                Window size used for the rolling calculation.
        returns:
            tuple
                DataFrames containing rolling peaks and troughs.
    """
    # calculate maximum peaks and troughs
    maximum_peaks_df = w2_calculateRollingWindowMinMax(
        one_column_df = closing_price_df,
        type_str = 'max',
        window_int = window_int
    )
    maximum_troughs_df = w2_calculateRollingWindowMinMax(
        one_column_df = closing_price_df,
        type_str = 'min',
        window_int = window_int
    )

    return maximum_peaks_df, maximum_troughs_df


def w2_calculateMaximumDrawDown(closing_price_df, window_int = 252):
    """
        description:
            Calculates the maximum drawdown series for a price history by comparing each
            point against the recent rolling peak and tracking the largest observed decline.
        args:
            closing_price_df: pandas.DataFrame
                Price series indexed by time.
            window_int: int, default 252
                Window size used for the rolling drawdown calculation.
        returns:
            pandas.DataFrame
                The rolling maximum drawdown percentage series.
    """
    # calculate maximum drawdown percentage
    maximum_peaks_df = w2_calculateRollingWindowMinMax(
        one_column_df = closing_price_df,
        type_str = 'max',
        window_int = window_int
    )
    daily_troughs_percentage_df = (closing_price_df/maximum_peaks_df) - 1.0
    maximum_drawdown_percentage_df = w2_calculateRollingWindowMinMax(
        one_column_df = daily_troughs_percentage_df,
        type_str = 'min',
        window_int = window_int
    )

    return maximum_drawdown_percentage_df