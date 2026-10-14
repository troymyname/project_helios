# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

# import dependencies
import numpy as np
import ray.tune

from ray.rllib.utils.metrics import (
    ENV_RUNNER_RESULTS,
    EPISODE_RETURN_MEAN,
    EVALUATION_RESULTS
)

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify program name and version
PROGRAM_NAME = 'helios'
PROGRAM_VERSION = '2.0.0'

# specify root path
ROOT_PATH = '/home/tonmoyroy/tonmoy_projects/project_helios/'

# specify model save directory
MODEL_SAVE_PATH = '/mnt/Secondary/ray_models/'

# specify temporary file directory
TEMP_DIR = '/mnt/Secondary/ray_temp'

# specify exchanges ('amex', 'nasdaq', 'nyse')
TICKER_EXCHANGES = ['amex', 'nasdaq', 'nyse']

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify warnings to ignore
WARNING_IGNORE_CLASS_USER = UserWarning
WARNING_IGNORE_CLASS_FUTURE = FutureWarning
WARNING_IGNORE_CLASS_DEPRECATION = DeprecationWarning

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify random number generator seed
RNG_SEED = 2

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify wait times
WAIT_TIME_POINT_ONE = 0.1
WAIT_TIME_ONE = 1.0
WAIT_TIME_FIVE = 5.0
WAIT_TIME_TEN = 10.0
WAIT_TIME_FIFTEEN = 15.0

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify IBKR interface parameters
IBKR_WAIT_TIME_DISPATCH_DELAY = 0.5
IBKR_WAIT_TIME_LIVE_DATA_DOWN = 0.5
IBKR_WAIT_TIME_HIST_DATA_DOWN = 2.5
IBKR_WAIT_TIME_TRADE = 1.0

IBKR_ACCOUNT_INFORMATION_CLIENT_ID = 1
IBKR_HISTORICAL_DATA_CLIENT_ID = 2
IBKR_LIVE_DATA_CLIENT_ID = 3
IBKR_ORDER_CLIENT_ID = 4
IBKR_SCAN_DATA_CLIENT_ID = 5
IBKR_TRADE_CLIENT_ID = 6
IBKR_TRADE_SIGNAL_CLIENT_ID = 7

IBKR_COMMISSION = 0.0035                    # NOTE: This is per IBKR Pro Tiered pricing plan. 
IBKR_ORDER_QUANTITY_LIMIT = 500

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify batch quantity of tickers (needed during performing transactions, tuning, training, evaluating, inferencing)
# NOTE: This parameter must be greater than 1.
QUANTITY = 4

# specify initial balances (for tuning, training, and evaluating)
TUNE_INITIAL_BALANCE = 500.00
TRAIN_INITIAL_BALANCE = TUNE_INITIAL_BALANCE
EVAL_INITIAL_BALANCE = TRAIN_INITIAL_BALANCE

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify RL algorithm type
RAY_ALGO_TYPE = 'PPO'

# specify resources
RAY_CPUS = 8
RAY_GPUS = 0
RAY_OBJECT_STORE_MEMORY = 8*1024*1024*1024

# specify number of environment runner and learner parameters
# NOTE: 'RAY_ENV_RUNNERS' can be switched to 0 for debugging during training.
RAY_LEARNERS = 1
RAY_ENV_RUNNERS = 1
RAY_EVAL_ENV_RUNNERS = 1

# specify data type
RAY_DATA_TYPE = np.float32

# specify default metric to track
RAY_METRIC_RETURN_MEAN = f'{ENV_RUNNER_RESULTS}/{EPISODE_RETURN_MEAN}'
RAY_METRIC_RETURN_MEAN_TRACKING_MODE = 'max'
RAY_METRIC_RETURN_MEAN_EVAL = f'{EVALUATION_RESULTS}/{ENV_RUNNER_RESULTS}/{EPISODE_RETURN_MEAN}'
RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE = 'max'
RAY_METRIC_ENTROPY = 'learners/default_policy/entropy'
RAY_METRIC_ENTROPY_TRACKING_MODE = 'min'

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====
# specify train parameters
# reference: https://docs.ray.io/en/latest/_modules/ray/rllib/algorithms/ppo/ppo.html
RAY_TRAIN_SEED = 2                          # NOTE: 'RAY_TRAIN_SEED = 0' means no seed will be set.
RAY_TRAIN_EPOCH = 160                       # NOTE: Tuned 04/2026, approximated.
RAY_TRAIN_ITERATIONS_MAX = 10000
RAY_TRAIN_GRACE_PERIOD_MIN = 8
RAY_TRAIN_GAMMA = 0.9641                    # NOTE: This is discount factor. Value close to 0 means immediate rewards are prioritized, value close to 1 means future rewards are as important as immediate ones. Tuned Dec 2025.
RAY_TRAIN_LAMBDA = 0.9798                   # NOTE: This is bias-variance trade-off. 0 means high bias low variance estimate, 1 means opposite. Paper: https://arxiv.org/pdf/1506.02438. Tuned Dec 2025.
RAY_TRAIN_VF_LOSS_COEFF = 0.0036            # NOTE: According to documentation, this needs to be tuned if 'vf_share_layers' is set to True in model_config. Conventional Range: 1e-5 to 1e-2. Tuned 04/2026.
RAY_TRAIN_VF_CLIP_PARAM = 5.0               # NOTE: This is included after training data showed exploding vf_loss. Conventional Values: 1, 5, 10.
RAY_TRAIN_ENTROPY_COEFFICIENT = 0.0147      # NOTE: Increasing this value encourages the policy to maintain higher entropy, leading to more stochastic actions and increased exploration. Tuned 04/2026.
RAY_TRAIN_STARTING_LEARNING_RATE = 0.0075   # NOTE: Tuned 04/2026, approximated to a standard value.
RAY_TRAIN_ADJUSTED_LEARNING_RATE = 0.0075   # NOTE: Tuned 04/2026, approximated to a standard value.
RAY_TRAIN_ENDING_LEARNING_RATE = 0.0075     # NOTE: Tuned 04/2026, approximated to a stardard value.
RAY_TRAIN_MINIBATCH = 64
RAY_TRAIN_BATCH_PER_LEARNER = 512
RAY_TRAIN_CHECKPOINT_FREQUENCY = 256        # NOTE: This relates to number of iterations!
RAY_TRAIN_RECENT_DATA_CHUNK = 1152          # NOTE: 252 data points are needed to calculate Sharpe ratio. Data length of 1280 (batch * 10) is not available.
RAY_TRAIN_TICKER_SAMPLES = 250
RAY_TRAIN_GRAD_CLIP = 5.0                   # NOTE: This is used to mitigate the exploding gradient problem. TODO: The impact of this should be checked.
RAY_TRAIN_GRAD_CLIP_BY = 'global_norm'      # NOTE: This is used to mitigate the exploding gradient problem. TODO: The impact of this should be checked.
RAY_TRAIN_VERBOSITY = 2                     # NOTE: This value can be 0, 1, or 2. Below printout happens with value 2 (see printout example below).
RAY_TRAIN_DASHBOARD = False                 # NOTE: This is changed to 'False' to reduce load on RAM.
RAY_TRAIN_TIME_BUDGET = 1e6

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify evaluation parameters
RAY_EVAL_SEED = 2                           # NOTE: 'RAY_EVAL_SEED = 0' means no seed will be set. This is not necessary.
RAY_EVAL_INTERVAL = 4                       # NOTE: This relates to number of training iterations!
RAY_EVAL_DURATION = RAY_TRAIN_RECENT_DATA_CHUNK
RAY_EVAL_DURATION_UNIT = 'timesteps'
RAY_EVAL_RECENT_DATA_CHUNK = RAY_TRAIN_RECENT_DATA_CHUNK
RAY_EVAL_TICKER_SAMPLES = 50

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify tune parameters
RAY_TUNE_SEED = RAY_TRAIN_SEED
RAY_TUNE_ITERATIONS_MAX = 2000
RAY_TUNE_GRACE_PERIOD_MIN = 256
RAY_TUNE_NUM_SAMPLES = 50
RAY_TUNE_PARAM_SPACE = {
    'num_epochs': ray.tune.uniform(lower = 32.0, upper = 256.0),
    'gamma': ray.tune.uniform(lower = 0.95, upper = 0.99),
    'lambda_': ray.tune.uniform(lower = 0.95, upper = 0.99),
    'vf_loss_coeff': ray.tune.uniform(lower = 1e-5, upper = 1e-2),
    'entropy_coeff': ray.tune.uniform(lower = 0.01, upper =  0.05),
    'lr': ray.tune.uniform(lower = 1e-5, upper = 1e-2),
    'minibatch_size': RAY_TRAIN_MINIBATCH,
    'train_batch_size_per_learner': RAY_TRAIN_BATCH_PER_LEARNER
}
RAY_TUNE_CHECKPOINT_FREQUENCY = RAY_TRAIN_CHECKPOINT_FREQUENCY
RAY_TUNE_RECENT_DATA_CHUNK = RAY_TRAIN_RECENT_DATA_CHUNK
RAY_TUNE_TICKER_SAMPLES = 250
RAY_TUNE_VERBOSITY = 2                      # NOTE: This value can be 0, 1, or 2.
RAY_TUNE_TIME_BUDGET = 1e6                  # NOTE: This is the maximum amount of time the Ray tune session is going to run before terminating.
RAY_TUNE_MAX_CONCURRENT_TRIALS = 2

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify environment parameters (for debugging)
RAY_ENV_DEBUG_ON = False
RAY_ENV_DEBUG_VERBOSITY = 2                 # NOTE: This value can be 0, 1 or 2. The 'RAY_ENV_DEBUG_ON' parameter needs to be set to True!

# specify environment parameters (for reward calculation)
RAY_ENV_INITIAL_REWARD = 2.0
RAY_ENV_DISCOUNT_FACTOR_ON = False
RAY_ENV_DISCOUNT_FACTOR = 0.90
RAY_ENV_TIME_PENALTY_ON = False
RAY_ENV_PORTFOLIO_OVER_BALANCE_RATIO_MIN = 0.01
RAY_ENV_PRICE_IN_BROWNIAN_MOTION = False    # NOTE: This option simulates price data points using Geometric Brownian Motion for random selection of current price.
                                            # NOTE: This option is turned off as this adds stochasticity to the training/evaluation process.

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify reward/penalty function selection
# 0 - Sharpe-Based Reward
# 1 - Action-Based Reward
# 2 - Drawdown Penalty
RAY_REWARD_CLIP_RANGE = (-5.0, 5.0)
RAY_REWARD_SELECTOR = [0, 1, 1, 0, 0]
RAY_REWARD_WEIGHTS = [0.0, 0.5, 0.5, 0.0, 0.0]

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify data selection parameters
DATA_LENGTH_MIN = RAY_TRAIN_RECENT_DATA_CHUNK

# specify flag to turn on dimensionality reduction using PCA
PCA_DIM_REDUCTION = True
PCA_NUM_PRINCIPAL_COMPONENTS = 16

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

RAY_REPORTING_NUM_EPISODES_FOR_SMOOTHING = 16

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify ticker selection parameters
PE_RATIO_PROXIMITY_RANGE_PERCENTAGE = 0.05

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# specify trading flags
TRADE_IMMEDIATE_LIQUIDATE = False
TRADE_END_HOUR = 16                         # NOTE: This needs to be adjusted manually based on half-day trading.

# specify trading preference lists
# NOTE: This is just a way to indicate to Helios what not to do.
TRADE_ACQUISITION_PREFERENCE = []
TRADE_DISPOSAL_PREFERENCE = []

# specify trading starting cash
TRADE_LIVE_STARTING_CASH = 525.0
TRADE_SIMULATION_STARTING_CASH = 1000000.0

# specify trading upper and lower limits for ticker selection
TRADE_PRICE_LOWER_LIMIT = 10.0
TRADE_PRICE_UPPER_LIMIT = 150.0
TRADE_VOLUME_LOWER_LIMIT = 100000

# specify trading parameters
TRADE_RECENT_DATA_CHUNK_RL_INFERENCE = 250  # NOTE: This was reduced to 250 from 252 max number of data rows from IBKR (requested in threads) is 251.
TRADE_RECENT_DATA_CHUNK_SCAN = 200
TRADE_RL_EVALUATION_SAMPLE_FACTOR = 4       # NOTE: This is multiplied with QUANTITY to determine the number of samples to feed to the RL agent.

TRADE_ACQUISITION_PORT_OPT_MIN_COUNT = 4

TRADE_ACQUISITION_DIVERSITY = 10            # NOTE: buying power / diversity = acquisition price threshold.

TRADE_PRICE_CHANGE_SAFETY_THRESHOLD = 0.25  # NOTE: This is a safety threshold applied to prices before securities are disposed.

TRADE_LIMIT_ORDER_GAP = 0.50

TRADE_STRATEGY_COMP_WEIGHTS = {
    'ma': 0.05,
    'macd': 0.04,
    'rsi': 0.11,
    'bb': 0.41,
    'zscore': 0.39
}                                           # NOTE: Weights were derived via w1_generateMultiSecurityBacktest.py on 06/2026.      
TRADE_STRATEGY_COMP_THRESHOLD = 0.27        # NOTE: Threshold was derived via w1_generateMultiSecurityBacktest.py on 06/2026.

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

# printout example
# ╭──────────────────────────────────────────────────────╮
# │ Trial PPO_d018d_00000 result                         │
# ├──────────────────────────────────────────────────────┤
# │ env_runners/episode_len_mean                 1058.82 │
# │ env_runners/episode_return_mean                 4.22 │
# │ evaluation/env_runners/episode_return_mean       2.1 │
# │ num_env_steps_sampled_lifetime                231200 │
# ╰──────────────────────────────────────────────────────╯

# ==== ==== ==== ==== ==== ==== ==== ==== ==== ====
