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

# import custom configs and utils
from config import ROOT_PATH
from utils.w2_performDataFrameOps import (
    w2_concatenateDataFramesInRows,
    w2_generateDataFrame,
    w2_readCSVToDataFrame,
    w2_writeDataFrameToCSV
)


def w2_updateLedgerEntries(
        data_dict,
        ledgers_dir_str = 'ledgers/',
        ledgers_file_name_str = 'ledger_entries_simulated.csv',
        erase_on = False,
        simulated_on = True
):
    """
        description:
            Appends a trade event or ledger payload to the appropriate ledger CSV file.
            The function selects the simulated or live ledger filename and writes a new file
            when needed.
        args:
            data_dict: dict
                Row data to append to the ledger.
            ledgers_dir_str: str, default 'ledgers/'
                Directory containing the ledger file.
            ledgers_file_name_str: str, default 'ledger_entries_simulated.csv'
                Ledger filename to read from or create.
            erase_on: bool, default False
                Whether to overwrite the existing ledger rather than append to it.
            simulated_on: bool, default True
                Determines whether the simulated or live ledger file should be used.
        returns:
            None
    """
    # override ledgers file name during live trading
    if not simulated_on:
        ledgers_file_name_str = 'ledger_entries.csv'
        
    # if file exists, update, else save a new one
    if os.path.isfile(ROOT_PATH + ledgers_dir_str + ledgers_file_name_str) and not erase_on:
        # read data
        ledger_df = w2_readCSVToDataFrame(ROOT_PATH + ledgers_dir_str + ledgers_file_name_str)
        # update data
        ledger_df = w2_concatenateDataFramesInRows(
            df1 = ledger_df,
            df2 = w2_generateDataFrame(
                data = data_dict,
                columns_list = list(data_dict.keys())
            )
        )
        # save data
        w2_writeDataFrameToCSV(
            df = ledger_df,
            file_path = ROOT_PATH + ledgers_dir_str + ledgers_file_name_str
        )

    else:
        # generate a new dataframe and save data
        w2_writeDataFrameToCSV(
            df = w2_generateDataFrame(
                data = data_dict,
                columns_list = list(data_dict.keys())
            ),
            file_path = ROOT_PATH + ledgers_dir_str + ledgers_file_name_str
        )