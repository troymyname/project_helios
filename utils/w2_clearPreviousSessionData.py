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

import os
import shutil

# import custom configs and utils
from config import MODEL_SAVE_PATH, ROOT_PATH, TEMP_DIR
from utils.w2_generateDateStringYYYYMMDD import w2_generateDateStringYYYYMMDD


def w2_removeData(location_str, external = False):
    """
        description:
            Removes files or directories from a target location inside the project tree.
            When `external` is True, the path is treated as an absolute or already-rooted
            location rather than being prefixed by the repository root.
        args:
            location_str: str
                Relative or absolute path to the data directory to clear.
            external: bool, default False
                Whether the path should be interpreted as external to the project root.
        returns:
            None
    """
    if external:
        if len(os.listdir(location_str)) != 0:
            for item in os.listdir(location_str):
                try:
                    os.remove(path = location_str + '/' + item)
                except IsADirectoryError:
                    shutil.rmtree(path = location_str + '/' + item, ignore_errors = True)
    else:
        if len(os.listdir(ROOT_PATH + location_str)) != 0:
            for item in os.listdir(ROOT_PATH + location_str):
                try:
                    os.remove(path = ROOT_PATH + location_str + '/' + item)
                except IsADirectoryError:
                    shutil.rmtree(path = ROOT_PATH + location_str + '/' + item, ignore_errors = True)


def w2_clearPreviousSessionData(
        remove_tickers_on = False,
        remove_scans = False,
        remove_daily_on = False,
        remove_hourly_on = False,
        remove_minutely_on = False,
        remove_features_on = False,
        remove_fundamentals_on = False,
        remove_returns_on = False,
        remove_logs_on = False,
        remove_plots_on = False,
        remove_results_on = False,
        remove_temps = False,
        remove_all = False
):
    """
        description:
            Clears selected project artifacts such as market data, reports, logs, and
            temporary files so a new training, evaluation, or trading session can start cleanly.
        args:
            remove_tickers_on: bool, default False
                Whether to remove ticker data.
            remove_scans: bool, default False
                Whether to remove scan outputs.
            remove_daily_on: bool, default False
                Whether to remove daily data files.
            remove_hourly_on: bool, default False
                Whether to remove hourly data files.
            remove_minutely_on: bool, default False
                Whether to remove minutely data files.
            remove_features_on: bool, default False
                Whether to remove feature data.
            remove_fundamentals_on: bool, default False
                Whether to remove fundamental data.
            remove_returns_on: bool, default False
                Whether to remove return-series artifacts.
            remove_logs_on: bool, default False
                Whether to remove log files.
            remove_plots_on: bool, default False
                Whether to remove generated plots.
            remove_results_on: bool, default False
                Whether to remove model or experiment results.
            remove_temps: bool, default False
                Whether to remove temporary files.
            remove_all: bool, default False
                Convenience flag that enables all cleanup operations.
        returns:
            None
    """
    # remove data
    if remove_all or remove_tickers_on:
        w2_removeData(location_str = 'data/tickers')
    if remove_all or remove_scans:
        w2_removeData(location_str = 'data/scans')
    if remove_all or remove_daily_on:
        w2_removeData(location_str = 'data/daily')
    if remove_all or remove_hourly_on:
        w2_removeData(location_str = 'data/hourly')
    if remove_all or remove_minutely_on:
        w2_removeData(location_str = 'data/minutely')
    if remove_all or remove_features_on:
        w2_removeData(location_str = 'data/features')
    if remove_all or remove_fundamentals_on:
        w2_removeData(location_str = 'data/fundamentals')
    if remove_all or remove_returns_on:
        w2_removeData(location_str = 'data/returns')
    # remove logs
    if remove_all or remove_logs_on:
        w2_removeData(location_str = 'logs')
    # remove plots and reports
    if remove_all or remove_plots_on:
        w2_removeData(location_str = 'reports/plots')
    # remove results
    if remove_all or remove_results_on:
        w2_removeData(location_str = MODEL_SAVE_PATH + 'results', external = True)
    # remove temporary files (from RLLib)
    if remove_all or remove_temps:
        w2_removeData(location_str = TEMP_DIR, external = True)


def w2_stashAway(
        location_str, 
        stash_folder_name_str = None
    ):
    """
        description:
            Moves non-directory files from a target location into a dated stash folder
            so the original directory can be preserved for later inspection.
        args:
            location_str: str
                Relative path to the directory whose contents should be stashed.
            stash_folder_name_str: str, default None
                Optional custom name for the stash folder. If omitted, the current date
                string is used.
        returns:
            None
    """
    if stash_folder_name_str is None:
        stash_folder_name_str = w2_generateDateStringYYYYMMDD()
    # generate a stash folder
    try:
        os.mkdir(ROOT_PATH + location_str + stash_folder_name_str)
    except FileExistsError:
        pass
    # move non-directory items to the stash folder
    for item in os.listdir(ROOT_PATH + location_str):
        if not os.path.isdir(ROOT_PATH + location_str + item):
            shutil.move(
                src = ROOT_PATH + location_str + item,
                dst = ROOT_PATH + location_str + stash_folder_name_str + '/' + item
            )