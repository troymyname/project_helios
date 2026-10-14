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


def w2_calculateNDiscreteDifference(narr, period):
    """
        description:
            Computes a discrete difference over a given lag period for a NumPy array.
        args:
            narr: numpy.ndarray
                Input array of values.
            period: int
                Number of periods to lag the difference calculation.
        returns:
            numpy.ndarray
                The differenced series with the specified lag applied.
    """
    return np.diff(
        a = np.hstack(tup = (np.zeros(period), narr)),
        n = period
    )


def w2_standardizeData(sample_flt, sample_history_narr):
    """
        description:
            Standardizes a single sample against the historical mean and standard deviation.
            If the history has zero variance, the original sample is returned unchanged.
        args:
            sample_flt: float
                The value to standardize.
            sample_history_narr: numpy.ndarray
                Historical samples used to derive the normalization statistics.
        returns:
            float
                The standardized value, or the original sample if the history is constant.
    """
    mean_flt = np.mean(a = sample_history_narr, axis = 0)
    std_flt = np.std(a = sample_history_narr, axis = 0)
    if std_flt == 0.0:
        return sample_flt
    else:
        return (sample_flt - mean_flt)/std_flt