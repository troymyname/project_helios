# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://github.com/rreichel3/US-Stock-Symbols
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import os
import subprocess

from pathlib import Path

# import custom configs and utils
from config import ROOT_PATH, TICKER_EXCHANGES
from utils.w2_compareFileAgeToThreshold import w2_compareFileAgeToThreshold
from utils.w2_performDataFrameOps import (
    w2_addNewColumnWithConstantData,
    w2_concatenateDataFramesInRows,
    w2_generateDataFrame,
    w2_readJSONToDataFrame,
    w2_writeDataFrameToJSON
)


def w1_if_getTickers(
        temps_dir_str = 'data/temps/',
        tickers_dir_str = 'data/tickers/',
        max_age_type_str = 'day',
        max_age_value_int = 90,
        test_on = False
):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # determine if the age of the tickers JSON file is within threshold
    age_within_thresh = False
    contents_list = os.listdir(ROOT_PATH + tickers_dir_str)
    if contents_list:
        for file_name_str in contents_list:
            if file_name_str == 'tickers.json':
                age_within_thresh = w2_compareFileAgeToThreshold(
                    file_path_str = ROOT_PATH + tickers_dir_str + 'tickers.json',
                    threshold_type_str = max_age_type_str,
                    threshold_value_int = max_age_value_int
                )

    if age_within_thresh:
        # read previously saved JSON file
        tickers_df = w2_readJSONToDataFrame(ROOT_PATH + tickers_dir_str + 'tickers.json')

        # test results
        if test_on:
            print(tickers_df.head())

        return tickers_df

    else:
        # empty files from previous runs if they exist
        if contents_list:
            for file_name_str in contents_list:
                os.remove(os.path.join(ROOT_PATH, tickers_dir_str, file_name_str))

        # ensure that directories exits
        clones_path = Path(ROOT_PATH + temps_dir_str)
        try:
            clones_path.mkdir()
        except FileExistsError:
            pass
        tickers_path = Path(ROOT_PATH + tickers_dir_str)
        try:
            tickers_path.mkdir(parents = True, exist_ok = True)
        except FileExistsError:
            pass

        # clone and save the repository
        print()
        command = ["git", "clone", "https://github.com/rreichel3/US-Stock-Symbols", ROOT_PATH + temps_dir_str]
        subprocess.run(command, check = True)
        print()

        # copy relevant files from 'temps' to 'tickers'
        raw_tickers_dir_str_dict = {
            'amex': 'amex/amex_full_tickers.json',
            'nasdaq': 'nasdaq/nasdaq_full_tickers.json',
            'nyse': 'nyse/nyse_full_tickers.json'
        }
        for key in raw_tickers_dir_str_dict.keys():
            if key in TICKER_EXCHANGES:
                command = ["cp", "-f", f"{ROOT_PATH + temps_dir_str}{raw_tickers_dir_str_dict[key]}", f"{ROOT_PATH + tickers_dir_str}{key}.json"]
                subprocess.run(command, check = True)

        # initialize empty dataframe
        tickers_df = w2_generateDataFrame(data = {})

        # read all files in 'tickers', add 'exchange' column and concatenate into one dataframe
        for file_name_str in os.listdir(ROOT_PATH + tickers_dir_str):
            if file_name_str != 'tickers.json':
                temp_df = w2_readJSONToDataFrame(
                    file_path = ROOT_PATH + tickers_dir_str + file_name_str
                    )
                temp_df = w2_addNewColumnWithConstantData(
                    df = temp_df,
                    column_str = 'exchange',
                    data_str = (file_name_str[:-5]).upper()
                    )
                tickers_df = w2_concatenateDataFramesInRows(
                    df1 = tickers_df,
                    df2 = temp_df
                    )

        # save dataframe for later reference
        w2_writeDataFrameToJSON(
            df = tickers_df,
            file_path = ROOT_PATH + tickers_dir_str + 'tickers.json'
            )

        # show results
        if test_on:
            print(tickers_df.head())

        # clean previous clone
        command = ['rm', '-rf', f"{ROOT_PATH + temps_dir_str}"]
        subprocess.run(command, check = True)

        return tickers_df


if __name__ == '__main__':
    w1_if_getTickers(test_on = True)