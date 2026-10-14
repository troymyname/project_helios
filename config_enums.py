from enum import Enum


# define action signal enum
class ActionSignal(Enum):
    HOLD_OR_IGNORE = 0
    IMMEDIATE_BUY = 1
    IMMEDIATE_SELL = 2
    LIMIT_BUY = 3
    LIMIT_SELL = 4

# define operation mode enum
class OperationMode(Enum):
    TRAIN = 0
    EVALUATE = 1
    DEPLOY = 2
    RESTART = 3

# define operation phase enum
class OperationPhase(Enum):
    PHASE_STRATEGIZE = 0
    PHASE_ACT = 1
    PHASE_REFLECT = 2
    PHASE_WAIT = 3