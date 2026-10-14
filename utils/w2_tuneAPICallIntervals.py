# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# CAUTION:
# w1_generateTradeSignal_Strategy_EMA_KMA_MACD_RSI makes use of memories.json!
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import time

# import custom configs and utils
from config import ROOT_PATH
from strategies.w1_generateTradeSignal import w1_generateTradeSignal_Strategy_EMA_KMA_MACD_RSI
from utils.w2_clearPreviousSessionData import w2_clearPreviousSessionData
from utils.w2_performHDF5Ops import w2_readDataFromHDF5

simulated_on = True

scanned_tickers_dir_str = 'data/scans/'
scanned_file_name_str = 'price_threshold_scan_list.h5'

wait_time_flt = 0.1
start_trials_int = 20
current_trials_int = start_trials_int


for security_name_str in w2_readDataFromHDF5(save_path_str = ROOT_PATH + scanned_tickers_dir_str + scanned_file_name_str):
    try:
        # ==== ==== ==== ==== ==== API CALL FUNCTION
        # CAUTION:
        # w1_generateTradeSignal_Strategy_EMA_KMA_MACD_RSI makes use of memories.json!

        _, _ = w1_generateTradeSignal_Strategy_EMA_KMA_MACD_RSI(
            ticker_str = security_name_str,
            simulated_on = simulated_on
        )
        
        # ==== ==== ==== ==== ====
        # wait
        time.sleep(wait_time_flt)
        # decrement trials number
        current_trials_int -= 1
        # print
        print(
            f'INFO: Executed test function successfully, current num. of trials is {current_trials_int}, current wait time is {round(wait_time_flt, 2)} s...'
        )
        if current_trials_int == 0:
            break

    except Exception as e:
        # print
        print(
            f'WARNING: Handled an exception "{e}" while deriving action signal, adjusting wait time by + 0.05 s...'
        )
        # increment time
        wait_time_flt += 0.05
        # reset trials number
        current_trials_int = start_trials_int
        # clear previous day session data
        w2_clearPreviousSessionData(
            remove_minutely_on = True
        )