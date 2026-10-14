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

import numpy as np
import os
import random
import time


def w2_setSeedFromTime():
    """
        description:
            Sets a deterministic random seed derived from the current Unix timestamp so
            stochastic operations across Python, NumPy, and the hash seed environment
            are initialized in a reproducible yet time-varying manner.
        args:
            None
        returns:
            None
    """
    # multiply time by value to generate a more variable number
    seed_int = round(time.time())

    # set seed
    os.environ['PYTHONHASHSEED'] = str(seed_int)
    random.seed(seed_int)
    np.random.seed(seed_int)