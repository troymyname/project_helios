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


def w2_performDivision(numerator, denominator):
    """
        description:
            Safely performs division and returns zero when the denominator is zero or empty.
        args:
            numerator: numeric
                The dividend value.
            denominator: numeric
                The divisor value.
        returns:
            float
                The quotient as a float, or zero when the denominator evaluates to zero.
    """
    return float(numerator)/denominator if int(denominator) else 0.0