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

import datetime
import os


def w2_calculateFileAge(file_path_str):
    """
    Calculate the age of a file based on its last modification timestamp.

    Parameters:
        file_path_str (str): Path to the file whose age should be measured.

    Returns:
        datetime.timedelta: Time elapsed since the file was last modified.

    Raises:
        OSError: If the file does not exist or its metadata cannot be accessed.
    """
    return datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file_path_str))


def w2_compareFileAgeToThreshold(
        file_path_str, 
        threshold_type_str, 
        threshold_value_int,
        no_stale_on = False
    ):
    """
    Evaluate whether a file is newer than a given age threshold.

    Parameters:
        file_path_str (str): Path to the file to check.
        threshold_type_str (str): Threshold unit, one of 'day', 'D', 'hour', 'H', 'minute', 'M', 'second', or 'S'.
        threshold_value_int (int): Maximum allowed age in the chosen unit.
        no_stale_on (bool, optional): If True, bypass stale checking and always return True. Defaults to False.

    Returns:
        bool: True when the file age is within the threshold or when stale checking is disabled; False otherwise.

    Notes:
        - The function compares the file's last modification time against the current time.
        - For day thresholds it uses the timedelta.days value.
        - For hour, minute, and second thresholds it uses the elapsed seconds component.
        - Unsupported threshold types will result in False.
    """
    # return true if no state on flag is True
    if no_stale_on:
        return True
    # calculate age
    age_datatime_obj = w2_calculateFileAge(file_path_str = file_path_str)
    # compare age to threshold
    age_within_thresh = False
    if threshold_type_str == 'day' or threshold_type_str == 'D':
        if age_datatime_obj.days <= threshold_value_int:
            age_within_thresh = True
    elif threshold_type_str == 'hour' or threshold_type_str == 'H':
        if (age_datatime_obj.seconds // 3600) <= threshold_value_int:
            age_within_thresh = True
    elif threshold_type_str == 'minute' or threshold_type_str == 'M':
        if (age_datatime_obj.seconds // 60) <= threshold_value_int:
            age_within_thresh = True
    elif threshold_type_str == 'second' or threshold_type_str == 'S':
        if age_datatime_obj.seconds <= threshold_value_int:
            age_within_thresh = True
    else:
        pass

    return age_within_thresh