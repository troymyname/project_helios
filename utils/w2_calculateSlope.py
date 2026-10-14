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


def w2_calculateSlope(y2_flt, y1_flt, x2_flt = 0.0, x1_flt = 0.0):
    """
        description:
            Computes the slope between two points using the standard rise-over-run formula.
            When the x-axis interval is zero, the function falls back to the raw change in y.
        args:
            y2_flt: float
                Second y value.
            y1_flt: float
                First y value.
            x2_flt: float, default 0.0
                Second x value.
            x1_flt: float, default 0.0
                First x value.
        returns:
            float
                The calculated slope or raw y-difference when the x-difference is zero.
    """
    return (y2_flt - y1_flt)/(x2_flt - x1_flt) if (x2_flt - x1_flt) != 0.0 else (y2_flt - y1_flt)