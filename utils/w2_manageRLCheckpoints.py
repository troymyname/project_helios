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
import pickle

# import custom configs and utils
from config import ROOT_PATH


def w2_manageRLCheckpoints(configurations_path_str):
    """
        description:
            Loads and validates a saved RL configuration pickle so the sampled ticker list,
            recent data chunk, and other runtime settings can be recovered for downstream
            evaluation or analysis steps.
        args:
            configurations_path_str: str
                Relative or absolute path to the checkpoint configuration file.
        returns:
            tuple
                A tuple containing the configuration dictionary, the sampled ticker list,
                and the recent data chunk size.
    """
    # load configuration pickle file
    configurations_dict = {}
    if os.path.exists(ROOT_PATH + configurations_path_str):
        with open(ROOT_PATH + configurations_path_str, 'rb') as f:
            configurations_dict = pickle.load(f)
    else:
        raise ValueError('ERROR: Configurations path does not exist...')

    if configurations_dict['env_config']:
        environment_config_dict = configurations_dict['env_config']
        if environment_config_dict['sampled_tickers_list']:
            sampled_tickers_list = environment_config_dict['sampled_tickers_list']
        else:
            raise ValueError('ERROR: Tickers list not available...')

        if environment_config_dict['recent_data_chunk_int']:
            recent_data_chunk_int = environment_config_dict['recent_data_chunk_int']
        else:
            raise ValueError('ERROR: Recent data chunk value not available...')
    else:
        raise ValueError('ERROR: Environment config not available...')

    return configurations_dict, sampled_tickers_list, recent_data_chunk_int