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

import copy
import os

# import custom configs and utils
from config import ROOT_PATH
from accounts.w1_if_getAccountInformation import w1_if_getAccountInformation
from utils.w2_performJSONOps import w2_readJSON, w2_writeToJSON


def w2_refreshTransactionMemories(
        memories_path_str = 'strategies/memories/',
        simulated_on = True
    ):
    """
        description:
            Refreshes persisted trading memories by reloading the saved decision state,
            reconciling it with the current account portfolio information, and rewriting
            the memory file so it reflects the latest holdings.
        args:
            memories_path_str: str, default 'strategies/memories/'
                Directory containing the persisted memories file.
            simulated_on: bool, default True
                Determines whether to query simulated or live account information.
        returns:
            None
    """
    # generate/read decision memory dictionary
    if os.path.exists(ROOT_PATH + memories_path_str + 'memories.json'):
        # read memory file
        decision_memory_dict = w2_readJSON(
            json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
        )
    
        # derive updated portfolio information
        portfolio_information_dict = None
        while not portfolio_information_dict:
            try:
                _, portfolio_information_dict = w1_if_getAccountInformation(
                    simulated_on = simulated_on
                )
            except KeyError:
                pass

        # remove dictionary keys that do not belong
        temp_dict = copy.deepcopy(decision_memory_dict)
        for security_name_str in decision_memory_dict.keys():
            if security_name_str in list(portfolio_information_dict.keys()):
                if int(portfolio_information_dict[security_name_str]['quantity_int']) != 0:
                    pass
                else:
                    del temp_dict[security_name_str]
            else:
                del temp_dict[security_name_str]
        decision_memory_dict = copy.deepcopy(temp_dict)

        # save fresh copy of decision memory dictionary
        w2_writeToJSON(
            data_dict = decision_memory_dict,
            json_path_str = ROOT_PATH + memories_path_str + 'memories.json'
        )
    
    else:
        print('ERROR: Memories file not found...')


if __name__ == '__main__':
    w2_refreshTransactionMemories(
        simulated_on = True
    )