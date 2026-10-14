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

import json

# import custom configs and utils
from config import ROOT_PATH
from utils.w2_performJSONOps import w2_readJSONIteratively


# construct path
checkpoint_folder_name_str = 'PPO_TuneSession_2025-10-01/PPO_b2b268bf_1_disable_action_flattening=False,disable_execution_plan_api=-1,disable_initialize_loss_from_dummy_batch=False,disabl_2025-10-01_06-14-34'
results_path_str = ROOT_PATH + f'/models/{checkpoint_folder_name_str}/' + 'result.json'

# read data file
data_dict_list = w2_readJSONIteratively(json_path_str = results_path_str)

# print data file (last iteration)
print('Results from Last Iteration:')
print('---------- ---------- ---------- ----------')
print(json.dumps(data_dict_list[-1], indent = 4))
print('---------- ---------- ---------- ----------')

print()
print()
print()
print()

# print model information
print('Model Information:')
print('---------- ---------- ---------- ----------')
print(json.dumps(data_dict_list[-1]['config']['model'], indent = 4))
print('---------- ---------- ---------- ----------')