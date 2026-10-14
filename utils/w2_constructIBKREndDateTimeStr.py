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

from datetime import datetime


def w2_constructIBKREndDateTimeStr():
    """
    Construct an IBKR-compatible end date-time string for the current moment.

    This helper generates a timestamp string formatted for Interactive Brokers
    APIs using the current machine time and the fixed timezone suffix
    `US/Eastern`.

    Returns:
        str: Current date-time formatted as `YYYYMMDD HH:MM:SS US/Eastern`.
    """
    return datetime.now().strftime('%Y%m%d %H:%M:%S') + ' US/Eastern'