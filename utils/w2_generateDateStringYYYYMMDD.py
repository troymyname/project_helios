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


def w2_generateDateStringYYYYMMDD():
    """
        description:
            Generates a date string in YYYY-MM-DD format for the current system date.
        args:
            None
        returns:
            str
                The current date formatted as a string in YYYY-MM-DD form.
    """
    return str(datetime.strftime(datetime.today(), '%Y-%m-%d'))