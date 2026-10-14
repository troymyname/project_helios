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

import holidays

from datetime import datetime

# import custom configs and utils
from config_enums import OperationPhase


def w2_manageTrade(
        debug_override_on = False,
        debug_override_cycle_count_int = 0,
        debug_override_cycle_thresh_int = 50
    ):
    """
        description:
            A function that will provide information on the time phase the logic is in
            The time phases are divided into the following segments:
            'strategize' - This phase starts at 5:00 AM ET and ends at 9:30 AM ET.
            'act' - This phase starts at 9:30 AM ET and ends at market end time.
            'reflect' - This phase starts at market end time and ends at 5:00 AM ET.
            'wait' - This phase is selected if no other phase conditions are met.
        args:
            debug_override_on:
                Boolean flag indicating whether conditions need to be overridden
        returns:
            n/a
    """
    # check time
    holiday = datetime.today() in holidays.country_holidays('US')
    weekend = datetime.today().weekday() >= 5

    # check liquidation command online
    from config import TRADE_IMMEDIATE_LIQUIDATE
    immediate_liquidate_on = False
    if TRADE_IMMEDIATE_LIQUIDATE:
        immediate_liquidate_on = True

    # check acquisition and disposal preferences online
    from config import TRADE_ACQUISITION_PREFERENCE, TRADE_DISPOSAL_PREFERENCE
    acquisition_preference_list = TRADE_ACQUISITION_PREFERENCE
    disposal_preference_list = TRADE_DISPOSAL_PREFERENCE

    # check trade end hour online
    from config import TRADE_END_HOUR
    trade_end_hour_int = TRADE_END_HOUR

    # generate flag for limiting override cycle
    if debug_override_on and (debug_override_cycle_count_int < debug_override_cycle_thresh_int):
         debug_override_on_limited = True
         debug_override_cycle_count_int += 1
    else:
         debug_override_on_limited = False

    # manage phase
    hour_int = datetime.now().hour
    minute_int = datetime.now().minute
    if (not holiday and not weekend):
        if (2 < hour_int < 9) or (hour_int == 9 and minute_int < 30) or debug_override_on_limited:
                phase_enum = OperationPhase.PHASE_STRATEGIZE
        elif ((9 <= hour_int < trade_end_hour_int) and not immediate_liquidate_on) or debug_override_on:
            phase_enum = OperationPhase.PHASE_ACT
        elif ((hour_int <= 2) or (hour_int >= trade_end_hour_int)):
            phase_enum = OperationPhase.PHASE_REFLECT
        else:
            phase_enum = OperationPhase.PHASE_WAIT
    else:
        phase_enum = OperationPhase.PHASE_WAIT

    return phase_enum, immediate_liquidate_on, acquisition_preference_list, disposal_preference_list, debug_override_cycle_count_int