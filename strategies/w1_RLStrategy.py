# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://docs.ray.io/en/latest/rllib/key-concepts.html
# [2] https://docs.ray.io/en/latest/tune/api/schedulers.html
# [3] https://docs.ray.io/en/latest/rllib/rl-modules.html#auto-regressive-action-distributions
# [4] https://github.com/ray-project/ray/blob/master/rllib/examples/inference/policy_inference_after_training.py
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import warnings
from config import WARNING_IGNORE_CLASS_DEPRECATION
warnings.simplefilter(action = 'ignore', category = WARNING_IGNORE_CLASS_DEPRECATION)

import gc
import gymnasium
import json
import logging
import numpy as np
import os
import psutil
import random
import ray
import torch

from datetime import datetime
from ray.rllib.connectors.env_to_module import EnvToModulePipeline, FlattenObservations
from ray.rllib.connectors.module_to_env import ModuleToEnvPipeline
from ray.rllib.core import (
    COMPONENT_ENV_RUNNER,
    COMPONENT_LEARNER,
    COMPONENT_LEARNER_GROUP,
    COMPONENT_MODULE_TO_ENV_CONNECTOR,
    COMPONENT_RL_MODULE, COMPONENT_ENV_TO_MODULE_CONNECTOR
)
from ray.rllib.core.columns import Columns
from ray.rllib.core.rl_module.rl_module import DEFAULT_MODULE_ID, RLModule
from ray.rllib.env.single_agent_episode import SingleAgentEpisode
from ray.train import CheckpointConfig
from ray.tune import Callback
from ray.tune import run
from ray.tune import TuneConfig
from ray.tune import Tuner
from ray.tune.analysis import ExperimentAnalysis
from ray.tune.registry import register_env
from ray.tune.schedulers import ASHAScheduler
from ray.tune.search.bayesopt import BayesOptSearch

# import custom configs and utils
from config import (
    RAY_CPUS,
    RAY_DATA_TYPE,
    RAY_METRIC_ENTROPY,
    RAY_METRIC_ENTROPY_TRACKING_MODE,
    # RAY_METRIC_RETURN_MEAN,
    # RAY_METRIC_RETURN_MEAN_TRACKING_MODE,
    RAY_METRIC_RETURN_MEAN_EVAL,
    RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE,
    RAY_GPUS, RAY_OBJECT_STORE_MEMORY,
    MODEL_SAVE_PATH,
    TEMP_DIR
)
from config import (
    RAY_EVAL_DURATION,
    RAY_EVAL_DURATION_UNIT,
    RAY_EVAL_ENV_RUNNERS,
    RAY_EVAL_INTERVAL
)
from config import (
    RAY_TRAIN_GRACE_PERIOD_MIN,
    RAY_TRAIN_ITERATIONS_MAX,
    RAY_TRAIN_TIME_BUDGET,
    RAY_TRAIN_VERBOSITY,
    RAY_TRAIN_DASHBOARD
)
from config import (
    RAY_TUNE_GRACE_PERIOD_MIN,
    RAY_TUNE_ITERATIONS_MAX,
    RAY_TUNE_MAX_CONCURRENT_TRIALS,
    RAY_TUNE_NUM_SAMPLES,
    RAY_TUNE_TIME_BUDGET,
    RAY_TUNE_VERBOSITY
)
from config_enums import OperationMode
from features.w1_if_deriveFeatures import w1_if_deriveFeatures
from strategies.w1_RLEnvironment import RLEnvironment
from strategies.w2_implementPPOConfig import w2_implementPPOConfig
from utils.w2_performDataFrameOps import w2_concatenateDataFramesInRows, w2_dropRowsWithEmptyCells, w2_generateDataFrame, w2_writeDataFrameToCSV
from utils.w2_performDictionaryOps import w2_filterDictionary
from utils.w2_plot import w2_plotInTwoScales


# specify environment name
environment_name_str = 'HeliosRLEnvironment'

# reference: https://docs.ray.io/en/latest/rllib/rllib-callback.html
class CustomMemoryCleanUpCallback(Callback):
    """
    Ray Tune callback that triggers garbage collection after episodes.

    This callback monitors virtual memory usage and performs a full garbage
    collection when memory pressure exceeds a configured threshold.
    """
    def __init__(self):
        """
        Initialize the memory cleanup callback.
        """
        super().__init__()
        # initialize thresholds
        self.virtual_memory_percent_threshold_flt = 85.0

    def on_episode_end(self, *, episode, **kwargs):
        """
        Handle end-of-episode cleanup for Ray Tune experiments.

        Parameters:
            episode: The completed Ray Tune episode instance.
            **kwargs: Additional callback context provided by Ray Tune.
        """
        # run a full collection of unused virtual memory
        print(f'INFO: Virtual memory is at {psutil.virtual_memory()}%...')
        if psutil.virtual_memory().percent >= self.virtual_memory_percent_threshold_flt:
            print('INFO: Started garbage collection...')
            _ = gc.collect()

class RLStrategy:
    """
    High-level reinforcement learning strategy manager for the Helios trading system.

    This class encapsulates Ray RLlib training and evaluation configuration,
    data preparation, environment module conversion, and experiment orchestration
    for portfolio trading. It translates sampled ticker data and RL problem
    parameters into a Ray-compatible training setup.

    Attributes:
        operation_enum: Operation mode, typically training or evaluation.
        algorithm_type_str (str): Name of the RL algorithm to use (e.g. 'PPO').
        sampled_tickers_list (list): List of tickers to load and prepare.
        initial_balance_flt (float): Starting portfolio cash balance.
        recent_data_chunk_int (int): Number of most recent time steps to include.
        reward_config_arr (list): Reward component flags for the environment.
        reward_config_weights_arr (list): Weights applied to reward components.
        quantity_int (int): Number of assets selected at each step.
        num_actions_int (int): Number of action choices per selected asset.
        tick_interval_str (str): Time interval string for the data source.
        simulated_on (bool): Whether to use simulated feature data.
    """
    def __init__(
            self,
            operation_enum,
            algorithm_type_str,
            sampled_tickers_list,
            initial_balance_flt,
            recent_data_chunk_int,
            reward_config_arr,
            reward_config_weights_arr,
            quantity_int,
            num_actions_int,
            tick_interval_str,
            simulated_on
    ):
        """
        Initialize the RL strategy manager with trading and model configuration.

        Parameters:
            operation_enum: Operation mode, e.g. training or evaluation.
            algorithm_type_str (str): RL algorithm identifier such as 'PPO'.
            sampled_tickers_list (list): Ticker symbols used for feature derivation.
            initial_balance_flt (float): Starting capital for portfolio simulation.
            recent_data_chunk_int (int): Number of recent time steps used for environment data.
            reward_config_arr (list): Flags enabling reward components.
            reward_config_weights_arr (list): Weights for each reward component.
            quantity_int (int): Number of tickers selected each step.
            num_actions_int (int): Number of action types available per ticker.
            tick_interval_str (str): Time interval string for data generation and sampling.
            simulated_on (bool): Whether to use simulated feature data.
        """
        # initialize arguments
        self.operation_enum = operation_enum
        self.algorithm_type_str = algorithm_type_str
        self.sampled_tickers_list = sampled_tickers_list
        self.initial_balance_flt = initial_balance_flt
        self.recent_data_chunk_int = recent_data_chunk_int
        self.reward_config_arr = reward_config_arr
        self.reward_config_weights_arr = reward_config_weights_arr
        self.quantity_int = quantity_int
        self.num_actions_int = num_actions_int
        self.tick_interval_str = tick_interval_str
        self.simulated_on = simulated_on

        # initialize refined sampled tickers list
        self.refined_sampled_tickers_list = []

        # initialize data container dictionary
        self.data_container_dict = {}

        # initialize configuration specification dictionary
        self.config_specification_dict = {}
        self.time_major_dict = {}

        # initialize constants and stochasticity bool (explore_on = False makes algorithm deterministic)
        self.constants_dict = {
            "initial_balance_flt": self.initial_balance_flt,
            "commission_flt": 0.0
        }
        self.explore_on = True

        # initialize object containing training parameters for evaluation
        self.training_parameters_for_eval_obj = None

        # run data checking and population function
        self.checkAndPopulateData()

    @staticmethod
    def setSeed(seed_int):
        """
        Set deterministic random seeds for Python, NumPy, and PyTorch.

        Parameters:
            seed_int (int): Seed value to apply. If zero, no deterministic seeding is performed.
        """
        # set seed
        if seed_int != 0:
            os.environ['PYTHONHASHSEED'] = str(seed_int)
            random.seed(seed_int)
            np.random.seed(seed_int)
            torch.manual_seed(seed_int)
            torch.cuda.manual_seed_all(seed_int)
        else:
            pass

    def checkAndPopulateData(self):
        """
        Load derived feature datasets and populate the internal data container.

        The method derives feature and support data for each sampled ticker,
        filters out support keys from the refined ticker list, and stores the
        most recent data chunk in self.data_container_dict.
        """
        # derive features data
        features_data_dict = w1_if_deriveFeatures(
            tickers_str_list = self.sampled_tickers_list,
            simulated_on = self.simulated_on
        )
        # derive refined sampled tickers list that doesn't contain the '_support' tag and that is up to date to features data dictionary
        for key_str in features_data_dict.keys():
            if '_support' not in key_str:
                self.refined_sampled_tickers_list.append(key_str)
        # populate data container
        for ticker_str in self.refined_sampled_tickers_list:
            if self.operation_enum == OperationMode.TRAIN:
                self.data_container_dict[ticker_str] = {}
                self.data_container_dict[ticker_str]['feature_data_dict'] = features_data_dict[ticker_str].iloc[-self.recent_data_chunk_int:]
                self.data_container_dict[ticker_str]['support_data_dict'] = features_data_dict[ticker_str + '_support'].iloc[-self.recent_data_chunk_int:]

            elif self.operation_enum == OperationMode.EVALUATE:
                self.data_container_dict[ticker_str] = {}
                self.data_container_dict[ticker_str]['feature_data_dict'] = features_data_dict[ticker_str].iloc[-self.recent_data_chunk_int:]
                self.data_container_dict[ticker_str]['support_data_dict'] = features_data_dict[ticker_str + '_support'].iloc[-self.recent_data_chunk_int:]

    @staticmethod
    def configureTrialName(trial):
        """
        Build a readable Ray Tune trial name from trial metadata.

        Parameters:
            trial: Ray Tune trial object containing `trainable_name` and `trial_id`.

        Returns:
            str: A string combining the trainable name and trial identifier.
        """
        return '{}_{}'.format(
            trial.trainable_name,
            trial.trial_id
        )

    def convertEnvironmentToModule(self, *args):
        """
        Convert the environment specification into an RLlib module connector.

        Returns:
            FlattenObservations: A pipeline stage that flattens observations and
            action spaces for RL module compatibility.
        """
        # define action space
        action_space = [self.quantity_int, self.num_actions_int]
        action_space = gymnasium.spaces.MultiDiscrete(
            nvec = action_space,
            dtype = np.uint8
        )

        # define observation space
        observation_length_int = self.data_container_dict[list(self.data_container_dict.keys())[0]]['feature_data_dict'].shape[1]
        observation_space_tpl = (self.quantity_int, observation_length_int)
        observation_space = gymnasium.spaces.Box(
            low = np.finfo(RAY_DATA_TYPE).min,
            high = np.finfo(RAY_DATA_TYPE).max,
            shape = observation_space_tpl,
            dtype = RAY_DATA_TYPE
        )

        return FlattenObservations(
            input_observation_space = observation_space,
            input_action_space = action_space,
            multi_agent = False
        )

    def generateConfigSpecifications(self, seed_int, operation_enum):
        """
        Generate Ray RLlib configuration specifications for the given operation.

        The method builds a base algorithm configuration, injects environment
        settings, and prepares evaluation or training settings depending on the
        requested operation mode.

        Parameters:
            seed_int (int): Random seed used for reproducibility.
            operation_enum: Operation mode, either TRAIN or EVALUATE.
        """
        if operation_enum == OperationMode.TRAIN:
            # generate custom configurations
            if self.algorithm_type_str == 'PPO':
                self.config_specification_dict = w2_implementPPOConfig(
                    environment_name_str = environment_name_str,
                    environment_to_module_func = self.convertEnvironmentToModule
                )
            # append settings to default configurations
            self.config_specification_dict['env_config'] = {
                'refined_sampled_tickers_list': self.refined_sampled_tickers_list,
                'constants_dict': self.constants_dict,
                'recent_data_chunk_int': self.recent_data_chunk_int,
                'feature_data_dict': {},
                'support_data_dict': {},
                'reward_config_arr': self.reward_config_arr,
                'reward_config_weights_arr': self.reward_config_weights_arr,
                'seed_int': seed_int,
                'quantity_int': self.quantity_int,
                'num_actions_int': self.num_actions_int
            }
            # make changes to default configurations
            self.config_specification_dict['evaluation_interval'] = RAY_EVAL_INTERVAL
            self.config_specification_dict['evaluation_duration'] = RAY_EVAL_DURATION
            self.config_specification_dict['evaluation_duration_unit'] = RAY_EVAL_DURATION_UNIT,
            self.config_specification_dict['evaluation_parallel_to_training'] = True
            self.config_specification_dict['in_evaluation'] = False
            self.config_specification_dict['evaluation_config'] = {'explore': self.explore_on}
            self.config_specification_dict['evaluation_num_env_runners'] = RAY_EVAL_ENV_RUNNERS
            self.config_specification_dict['custom_eval_function'] = None

        elif operation_enum == OperationMode.EVALUATE:
            # generate custom configurations
            if self.algorithm_type_str == 'PPO':
                self.config_specification_dict = w2_implementPPOConfig(
                    environment_name_str = environment_name_str,
                    environment_to_module_func = self.convertEnvironmentToModule
                )
            # append settings to default configurations
            self.config_specification_dict['env_config'] = {
                'refined_sampled_tickers_list': self.refined_sampled_tickers_list,
                'constants_dict': self.constants_dict,
                'recent_data_chunk_int': self.recent_data_chunk_int,
                'feature_data_dict': {},
                'support_data_dict': {},
                'reward_config_arr': self.reward_config_arr,
                'reward_config_weights_arr': self.reward_config_weights_arr,
                'seed_int': seed_int,
                'quantity_int': self.quantity_int,
                'num_actions_int': self.num_actions_int
            }
            # make changes to default configurations
            self.config_specification_dict['evaluation_interval'] = RAY_EVAL_INTERVAL
            self.config_specification_dict['evaluation_duration'] = RAY_EVAL_DURATION
            self.config_specification_dict['evaluation_duration_unit'] = RAY_EVAL_DURATION_UNIT,
            self.config_specification_dict['evaluation_parallel_to_training'] = False
            self.config_specification_dict['in_evaluation'] = False # TODO: I need to look into the get_evaluation_config_object function in env_helios/lib/python3.12/site-packages/ray/rllib/algorithms/algorithm_config.py.
            self.config_specification_dict['evaluation_config'] = {'explore': self.explore_on}
            self.config_specification_dict['evaluation_num_env_runners'] = RAY_EVAL_ENV_RUNNERS
            self.config_specification_dict['custom_eval_function'] = None

        # add data to custom configurations
        self.addDataToConfigSpecifications()

    def addDataToConfigSpecifications(self):
        """
        Attach feature and support data into the environment configuration.

        This helper populates env_config with the derived data for each ticker
        prior to training or evaluation.
        """
        for ticker in self.refined_sampled_tickers_list:
            if self.operation_enum == OperationMode.TRAIN:
                self.config_specification_dict['env_config']['feature_data_dict'][ticker] = self.data_container_dict[ticker]['feature_data_dict']
                self.config_specification_dict['env_config']['support_data_dict'][ticker] = self.data_container_dict[ticker]['support_data_dict']
            elif self.operation_enum == OperationMode.EVALUATE:
                self.config_specification_dict['env_config']['feature_data_dict'][ticker] = self.data_container_dict[ticker]['feature_data_dict']
                self.config_specification_dict['env_config']['support_data_dict'][ticker] = self.data_container_dict[ticker]['support_data_dict']

    def tune(
            self,
            seed_int,
            checkpoint_frequency_int,
            param_space_dict
    ):
        """
        Perform hyperparameter tuning using Ray Tune and Bayesian optimization.

        Parameters:
            seed_int (int): Random seed for reproducibility.
            checkpoint_frequency_int (int): Frequency of checkpoint creation.
            param_space_dict (dict): Search space configuration for tunable parameters.
        """
        # shut down previous ray sessions
        ray.shutdown()
        # set seed for reproducibility
        self.setSeed(seed_int = seed_int)
        # register custom environment
        register_env(environment_name_str, lambda config: RLEnvironment(config))
        # set temporary files directory
        os.environ['RAY_TMPDIR'] = TEMP_DIR

        ray.remote(max_calls = 1)
        # generate configuration specifications
        self.generateConfigSpecifications(
            seed_int = seed_int,
            operation_enum = OperationMode.TRAIN
        )
        # define search algorithm
        # reference: https://docs.ray.io/en/latest/tune/api/doc/ray.tune.search.bayesopt.BayesOptSearch.html
        bayesopt_search_obj = BayesOptSearch(
            metric = RAY_METRIC_RETURN_MEAN_EVAL,
            mode = RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE
        )
        # define scheduler
        # reference: https://docs.ray.io/en/latest/tune/api/schedulers.html
        asha_scheduler_obj = ASHAScheduler(
            time_attr = 'training_iteration',
            max_t = RAY_TUNE_ITERATIONS_MAX,
            grace_period = [RAY_TUNE_GRACE_PERIOD_MIN if RAY_TUNE_ITERATIONS_MAX > RAY_TUNE_GRACE_PERIOD_MIN else RAY_TUNE_ITERATIONS_MAX][0],
            reduction_factor = 4,
            brackets = 1,
            stop_last_trials = True
        )
        # define checkpointing config
        # reference: https://docs.ray.io/en/latest/train/user-guides/checkpoints.html
        checkpoint_config_obj = CheckpointConfig(
            num_to_keep = 5,
            checkpoint_score_attribute = RAY_METRIC_RETURN_MEAN_EVAL,
            checkpoint_score_order = RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE,
            checkpoint_frequency = checkpoint_frequency_int,
            checkpoint_at_end = False
        )

        # add tunable parameters to config specifications
        # reference: https://docs.ray.io/en/latest/tune/api/doc/ray.tune.TuneConfig.html#ray.tune.TuneConfig
        # reference: https://docs.ray.io/en/latest/tune/api/doc/ray.tune.RunConfig.html#ray.tune.RunConfig
        # reference: https://docs.ray.io/en/latest/tune/api/doc/ray.tune.grid_search.html
        # reference: https://docs.ray.io/en/latest/tune/api/search_space.html
        # reference: https://docs.ray.io/en/latest/tune/api/doc/ray.tune.search.basic_variant.BasicVariantGenerator.html
        for _, key in enumerate(param_space_dict):
            self.config_specification_dict[key] = param_space_dict[key]
        # construct tuner and derive results
        tuner_obj = Tuner(
            trainable = self.algorithm_type_str,
            param_space = self.config_specification_dict,
            tune_config = TuneConfig(
                metric = RAY_METRIC_RETURN_MEAN_EVAL,
                mode = RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE,
                search_alg = bayesopt_search_obj,
                scheduler = asha_scheduler_obj,
                num_samples = RAY_TUNE_NUM_SAMPLES,
                max_concurrent_trials = RAY_TUNE_MAX_CONCURRENT_TRIALS,
                time_budget_s = RAY_TUNE_TIME_BUDGET,
                reuse_actors = False, # NOTE: Setting this to 'True' generates 2025-[1] as shown below. This was confirmed multiple times.
                trial_name_creator = self.configureTrialName
            ),
            run_config = ray.tune.RunConfig(
                name = self.algorithm_type_str + f'_TuneSession_{datetime.today().strftime("%Y-%m-%d")}',
                callbacks = [CustomMemoryCleanUpCallback()],
                storage_path = MODEL_SAVE_PATH,
                checkpoint_config = checkpoint_config_obj,
                verbose = RAY_TUNE_VERBOSITY
            )
        )
        results_obj = tuner_obj.fit()

        # derive best results (with the most episode rewards/returns mean) and print summary
        best_result_metric = RAY_METRIC_RETURN_MEAN_EVAL
        best_result_metric_tracking_mode = RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE
        best_result_obj = results_obj.get_best_result(
            metric = best_result_metric,
            mode = best_result_metric_tracking_mode,
            scope = 'last-5-avg',
            filter_nan_and_inf = True
        )
        print()
        print()
        print('==== ==== ==== ==== ==== ==== ==== ==== ==== ====')
        print(f'INFO: Best Trial Config Based On: {best_result_metric_tracking_mode} of {best_result_metric}:')
        print(
            json.dumps(
                w2_filterDictionary(
                    data_dict = best_result_obj.config,
                    allowed_types_tpl = (bool, float, int, list, np.float16, np.float32, np.float64, str),
                    allowed_types_strict_tpl = (dict,),
                    allowed_types_strict_size_bytes_int = 200
                ),
                indent = 4
            )
        )
        print('==== ==== ==== ==== ==== ==== ==== ==== ==== ====')
        print(f'INFO: Best Trial Metrics Based On: {best_result_metric_tracking_mode} of {best_result_metric}:')
        print(
            json.dumps(
                w2_filterDictionary(
                    data_dict = best_result_obj.metrics,
                    allowed_types_tpl = (bool, float, int, list, np.float16, np.float32, np.float64, str),
                    allowed_types_strict_tpl = (dict,),
                    allowed_types_strict_size_bytes_int = 200
                ),
                indent = 4
            )
        )
        print('==== ==== ==== ==== ==== ==== ==== ==== ==== ====')
        print()
        print()

    def train(
            self,
            seed_int,
            checkpoint_frequency_int,
            results_path_str = MODEL_SAVE_PATH + 'results/'
    ):
        """
        Train the configured RL agent using Ray RLlib.

        Parameters:
            seed_int (int): Random seed for reproducibility.
            checkpoint_frequency_int (int): Frequency of model checkpoint saving.
            results_path_str (str): Directory path to save training results.
        """
        # shut down previous ray sessions
        ray.shutdown()
        # set seed for reproducibility
        self.setSeed(seed_int = seed_int)
        # register custom environment
        register_env(environment_name_str, lambda config: RLEnvironment(config))
        # set environment variable for temporary files directory
        os.environ['RAY_TMPDIR'] = TEMP_DIR

        # initialize
        ray.init(
            num_cpus = RAY_CPUS,
            num_gpus = RAY_GPUS,
            object_store_memory = RAY_OBJECT_STORE_MEMORY,
            include_dashboard = RAY_TRAIN_DASHBOARD,
            configure_logging = False,
            logging_level = logging.FATAL,
            log_to_driver = False,
            object_spilling_directory = TEMP_DIR,
            _temp_dir = TEMP_DIR
        )

        ray.remote(max_calls = 1)
        # generate configuration specifications
        self.generateConfigSpecifications(
            seed_int = seed_int,
            operation_enum = OperationMode.TRAIN
        )
        # define scheduler
        # reference: https://docs.ray.io/en/latest/tune/api/schedulers.html
        asha_scheduler_obj = ASHAScheduler(
            time_attr = 'training_iteration',
            max_t = RAY_TRAIN_ITERATIONS_MAX,
            grace_period = RAY_TRAIN_GRACE_PERIOD_MIN,
            reduction_factor = 4,
            brackets = 1,
            stop_last_trials = True
        )
        # define checkpointing config
        # reference: https://docs.ray.io/en/latest/train/user-guides/checkpoints.html
        # reference: https://docs.ray.io/en/latest/train/api/doc/ray.train.CheckpointConfig.html#ray.train.CheckpointConfig
        checkpoint_config_obj = CheckpointConfig(
            num_to_keep = 5,
            checkpoint_score_attribute = RAY_METRIC_RETURN_MEAN_EVAL,
            checkpoint_score_order = RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE,
            checkpoint_frequency = checkpoint_frequency_int,
            checkpoint_at_end = False
        )

        # execute training
        # NOTE: 'verbose' can be switched to 2 for debugging.
        # NOTE: A container such as 'training_obj' can be used to capture the results of run method and the below section can be uncommented.
        run(
            run_or_experiment = self.algorithm_type_str,
            metric = RAY_METRIC_RETURN_MEAN_EVAL,
            mode = RAY_METRIC_RETURN_MEAN_EVAL_TRACKING_MODE,
            name = self.algorithm_type_str,
            time_budget_s = RAY_TRAIN_TIME_BUDGET,
            config = self.config_specification_dict,
            num_samples = 1,
            storage_path = MODEL_SAVE_PATH,
            scheduler = asha_scheduler_obj,
            verbose = RAY_TRAIN_VERBOSITY,
            trial_name_creator = self.configureTrialName,
            max_failures = 2,
            resume = False,
            reuse_actors = True,
            callbacks = [CustomMemoryCleanUpCallback()],
            checkpoint_config = checkpoint_config_obj
        )
        # # save train results
        # w2_writeDataFrameToCSV(
        #     df = training_obj.results_df,
        #     file_path = ROOT_PATH + results_path_str + 'last_train_session.csv'
        # )

    def evaluate(
            self,
            seed_int,
            num_episodes_during_inference_int,
            explore_during_inference,
            data_save_on = False,
            results_path_str = MODEL_SAVE_PATH + 'results/',
            plot_save_on = False,
            plot_show_on = False,
            plot_recent_data_chunk_int = 500,
            plot_save_file_name_str = None,
            plot_save_path_str = None
    ):
        """
        Evaluate a trained RL agent over a specified number of inference episodes.

        Parameters:
            seed_int (int): Random seed for reproducibility.
            num_episodes_during_inference_int (int): Number of episodes to evaluate.
            explore_during_inference (bool): Whether to use exploration during inference.
            data_save_on (bool): Save evaluation info to CSV when True.
            results_path_str (str): Directory path to save evaluation results.
            plot_save_on (bool): Save evaluation plots when True.
            plot_show_on (bool): Display evaluation plots when True.
            plot_recent_data_chunk_int (int): Number of recent points to include in the plot.
            plot_save_file_name_str (str | None): Filename to save the plot under.
            plot_save_path_str (str | None): Directory path to save the plot.

        Returns:
            pd.DataFrame: Evaluation information history for the completed inference episodes.

        References:
            [1] https://github.com/ray-project/ray/blob/master/rllib/examples/inference/policy_inference_after_training_w_connector.py
        """
        # shut down previous ray sessions
        ray.shutdown()
        # set seed for reproducibility
        self.setSeed(seed_int = seed_int)
        # register custom environment
        register_env(environment_name_str, lambda config: RLEnvironment(config))
        # set temporary files directory
        os.environ['RAY_TMPDIR'] = TEMP_DIR

        # generate configuration specifications
        self.generateConfigSpecifications(
            seed_int = seed_int,
            operation_enum = OperationMode.EVALUATE
        )

        # get experiment analysis
        experiment_analysis_obj = ExperimentAnalysis(
            experiment_checkpoint_path = str(os.path.join(MODEL_SAVE_PATH, self.algorithm_type_str)),
            default_metric = RAY_METRIC_ENTROPY,
            default_mode = RAY_METRIC_ENTROPY_TRACKING_MODE
        )
        # get best trial
        best_trial_obj = experiment_analysis_obj.get_best_trial(
            metric = RAY_METRIC_ENTROPY,
            mode = RAY_METRIC_ENTROPY_TRACKING_MODE,
            scope = 'all'
        )
        # get best checkpoint
        best_checkpoint_obj = experiment_analysis_obj.get_best_checkpoint(
            trial = best_trial_obj,
            metric = RAY_METRIC_ENTROPY,
            mode = RAY_METRIC_ENTROPY_TRACKING_MODE
        )

        # ==== ==== ====
        # NOTE: Below steps are consistent with the reference used.

        # [line 199] create an environment-to-module pipeline from checkpoint
        env_to_module_obj = EnvToModulePipeline.from_checkpoint(
            os.path.join(
                str(best_checkpoint_obj.path),
                COMPONENT_ENV_RUNNER,
                COMPONENT_ENV_TO_MODULE_CONNECTOR
            )
        )

        # [line 214] create RL module from checkpoint
        rl_module_obj = RLModule.from_checkpoint(
            os.path.join(
                str(best_checkpoint_obj.path),
                COMPONENT_LEARNER_GROUP,
                COMPONENT_LEARNER,
                COMPONENT_RL_MODULE,
                DEFAULT_MODULE_ID
            )
        )

        # [line 228] create module-to-env object
        module_to_env_obj = ModuleToEnvPipeline.from_checkpoint(
            os.path.join(
                str(best_checkpoint_obj.path),
                COMPONENT_ENV_RUNNER,
                COMPONENT_MODULE_TO_ENV_CONNECTOR
            )
        )

        # initialize environment
        environment_cls = RLEnvironment(config = self.config_specification_dict['env_config'])

        # [reference line 241] derive (reset) observations
        observations_arr, _ = environment_cls.reset()

        # [reference line 242] initialize episode with first (reset) observation
        episode_obj = SingleAgentEpisode(
            observations = [observations_arr],
            observation_space = environment_cls.observation_space,
            action_space = environment_cls.action_space
        )

        num_episodes_int = 0
        info_history_df = w2_generateDataFrame(data = {})
        while num_episodes_int < num_episodes_during_inference_int:
            shared_data_dict = {}
            input_dict = env_to_module_obj(
                episodes = [episode_obj],
                rl_module = rl_module_obj,
                explore = explore_during_inference,
                shared_data = shared_data_dict
            )

            if explore_during_inference:
                rl_module_dict = rl_module_obj.forward_exploration(batch = input_dict)
            else:
                rl_module_dict = rl_module_obj.forward_inference(batch = input_dict)

            to_env_obj = module_to_env_obj(
                batch = rl_module_dict,
                episodes = [episode_obj],
                rl_module = rl_module_obj,
                explore = explore_during_inference,
                shared_data = shared_data_dict
            )

            # [line 307] send the computed action to the environment
            action_obj = to_env_obj.pop(Columns.ACTIONS)[0]
            observations_arr, reward_flt, terminated_bool, truncated_bool, info_dict = environment_cls.step(action = action_obj)

            # [line 310] keep the 'SingleAgentEpisode' instance updated at all times
            episode_obj.add_env_step(
                observation = observations_arr,
                action = action_obj,
                reward = reward_flt,
                terminated = terminated_bool,
                truncated = truncated_bool,
                extra_model_outputs = {k: v[0] for k, v in to_env_obj.items()}
            )

            # [line 321] check if the episode is done, if so, reset
            if episode_obj.is_done:
                observations_arr, info = environment_cls.reset()
                episode_obj = SingleAgentEpisode(
                    observations = [observations_arr],
                    observation_space = environment_cls.observation_space,
                    action_space = environment_cls.action_space
                )
                num_episodes_int += 1

            # preserve info history
            processed_info_dict = {}
            for key in list(info_dict.keys()):
                processed_info_dict[key] = str(info_dict[key])
            info_history_df = w2_concatenateDataFramesInRows(
                df1 = info_history_df,
                df2 = w2_generateDataFrame(data = processed_info_dict)
            )

        # drop rows with empty cells
        last_eval_session_df = w2_dropRowsWithEmptyCells(info_history_df)

        # save data
        if data_save_on:
            w2_writeDataFrameToCSV(
                df = last_eval_session_df,
                file_path = results_path_str + 'last_eval_session.csv'
            )

        # plot data
        if plot_save_on or plot_show_on:
            plot_x_data_df = last_eval_session_df['step']
            plot_y1_data_df = last_eval_session_df['reward']
            plot_y2_data_df = last_eval_session_df['portfolio']
            w2_plotInTwoScales(
                x_data_df = plot_x_data_df,
                x_axis_label_str = 'Number of Steps',
                y_data_df_list = [plot_y1_data_df, plot_y2_data_df],
                y_axes_label_str_list = ['Reward', 'Portfolio'],
                y_axes_limits_bool_list = [True, False],
                y_axes_limits_list = [[-10, 10], []],
                datetime_on = False,
                plot_title_str = f'Agent Evaluation Results [{str(best_checkpoint_obj.path)}]',
                recent_data_chunk_int = plot_recent_data_chunk_int,
                save_on = plot_save_on,
                save_file_name_str = plot_save_file_name_str,
                save_path_str = plot_save_path_str,
                show_on = plot_show_on
            )

        return info_history_df

# ------------------------------------------------------------------------------
# REFERENCE TERMINAL OUTPUTS
# 2025-[1]: Could not re-use actor for trial PPO_82988b1c: Trainable runner reuse requires reset_config() to be implemented and return True.
# ------------------------------------------------------------------------------