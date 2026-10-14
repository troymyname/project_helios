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

from ray.rllib.algorithms.ppo import PPOConfig

# import custom configs and utils
from config import (
    RAY_CPUS,
    RAY_GPUS,
    RAY_ENV_RUNNERS,
    RAY_EVAL_ENV_RUNNERS,
    RAY_EVAL_INTERVAL,
    RAY_EVAL_DURATION,
    RAY_EVAL_DURATION_UNIT,
    RAY_LEARNERS,
    RAY_REPORTING_NUM_EPISODES_FOR_SMOOTHING,
    RAY_TRAIN_BATCH_PER_LEARNER,
    RAY_TRAIN_ENTROPY_COEFFICIENT,
    RAY_TRAIN_EPOCH,
    RAY_TRAIN_GAMMA,
    RAY_TRAIN_GRAD_CLIP,
    RAY_TRAIN_GRAD_CLIP_BY,
    RAY_TRAIN_LAMBDA,
    RAY_TRAIN_MINIBATCH,
    RAY_TRAIN_STARTING_LEARNING_RATE,
    RAY_TRAIN_VF_CLIP_PARAM,
    RAY_TRAIN_VF_LOSS_COEFF,
    RAY_TRAIN_ADJUSTED_LEARNING_RATE,
    RAY_TRAIN_ENDING_LEARNING_RATE
)


# generate model configuration dictionary
model_configuration_dict = {
    'fcnet_hiddens': [
        256,
        256
    ], # default
    "fcnet_activation": 'tanh', # default
    "conv_activation": 'relu', # default
    'vf_share_layers': True,
    'use_lstm': False, # default
    'max_seq_len': 8,
    'lstm_cell_size': 256, # default
    'lstm_use_prev_action': False, # default
    'lstm_use_prev_reward': False, # default
    'lstm_use_prev_action_reward': -1, # default
    'use_attention': True,
    'attention_num_transformer_units': 1, # default
    'attention_dim': 64, # default
    'attention_num_heads': 1, # default
    'attention_head_dim': 32, # default
    'attention_memory_inference': 64,
    'attention_memory_training': 64,
    'attention_position_wise_mlp_dim': 32, # default
    'attention_init_gru_gate_bias': 2.0, # default
    'attention_use_n_prev_actions': 8,
    'attention_use_n_prev_rewards': 8
}


def w2_implementPPOConfig(environment_name_str, environment_to_module_func):
    """
    Build a PPO algorithm configuration for Ray RLlib.

    This helper constructs a PPOConfig object with custom model, environment,
    training, evaluation, and reporting settings for the Helios RL trading system.
    It uses project-specific hyperparameters imported from the configuration
    module and enables the RL module + env runner pipeline.

    Parameters:
        environment_name_str (str): Registered environment name for Ray RLlib.
        environment_to_module_func (callable): Function that converts the env to an RL module.

    Returns:
        PPOConfig: Configured PPO algorithm object ready for training or evaluation.

    references:
        [1] https://docs.ray.io/en/latest/_modules/ray/rllib/algorithms/ppo/ppo.html
        [2] https://docs.ray.io/en/latest/_modules/ray/rllib/algorithms/algorithm_config.html
        [3] https://github.com/ray-project/ray/blob/master/rllib/algorithms/ppo/ppo.py
        [4] https://github.com/ray-project/ray/tree/master/rllib/tuned_examples/ppo < TODO: I need to review the examples.
    defaults:
        Model Information:
        ---------- ---------- ---------- ----------
        {
            "fcnet_hiddens": [
                256,
                256
            ],
            "fcnet_activation": "tanh",
            "fcnet_weights_initializer": null,
            "fcnet_weights_initializer_config": null,
            "fcnet_bias_initializer": null,
            "fcnet_bias_initializer_config": null,
            "conv_filters": null,
            "conv_activation": "relu",
            "conv_kernel_initializer": null,
            "conv_kernel_initializer_config": null,
            "conv_bias_initializer": null,
            "conv_bias_initializer_config": null,
            "conv_transpose_kernel_initializer": null,
            "conv_transpose_kernel_initializer_config": null,
            "conv_transpose_bias_initializer": null,
            "conv_transpose_bias_initializer_config": null,
            "post_fcnet_hiddens": [],
            "post_fcnet_activation": "relu",
            "post_fcnet_weights_initializer": null,
            "post_fcnet_weights_initializer_config": null,
            "post_fcnet_bias_initializer": null,
            "post_fcnet_bias_initializer_config": null,
            "free_log_std": false,
            "log_std_clip_param": 20.0,
            "no_final_linear": false,
            "vf_share_layers": false,
            "use_lstm": false,
            "max_seq_len": 20,
            "lstm_cell_size": 256,
            "lstm_use_prev_action": false,
            "lstm_use_prev_reward": false,
            "lstm_weights_initializer": null,
            "lstm_weights_initializer_config": null,
            "lstm_bias_initializer": null,
            "lstm_bias_initializer_config": null,
            "_time_major": false,
            "use_attention": false,
            "attention_num_transformer_units": 1,
            "attention_dim": 64,
            "attention_num_heads": 1,
            "attention_head_dim": 32,
            "attention_memory_inference": 50,
            "attention_memory_training": 50,
            "attention_position_wise_mlp_dim": 32,
            "attention_init_gru_gate_bias": 2.0,
            "attention_use_n_prev_actions": 0,
            "attention_use_n_prev_rewards": 0,
            "framestack": true,
            "dim": 84,
            "grayscale": false,
            "zero_mean": true,
            "custom_model": null,
            "custom_model_config": {},
            "custom_action_dist": null,
            "custom_preprocessor": null,
            "encoder_latent_dim": null,
            "always_check_shapes": false,
            "lstm_use_prev_action_reward": -1,
            "_use_default_native_models": -1,
            "_disable_preprocessor_api": false,
            "_disable_action_flattening": false
        }
        ---------- ---------- ---------- ----------
    """
    # modify properties of the PPOConfig class
    config = (
        PPOConfig()
        .api_stack(
            enable_rl_module_and_learner = True,
            enable_env_runner_and_connector_v2 = True
        )
        .environment(
            env = environment_name_str
        )
        .rl_module(
            model_config = model_configuration_dict
        )
        .env_runners(
            num_env_runners = RAY_ENV_RUNNERS,
            num_cpus_per_env_runner = 1,
            num_gpus_per_env_runner = 0,
            env_to_module_connector = environment_to_module_func
        )
        .framework(
            framework = 'torch'
        )
        .training(
            use_critic = True, # If this is set to true, vf_clip_param is in effect. This goes together with 'vf_clip_param' (per notes on 11/15/25).
            use_gae = True, # NOTE: This goes together with 'lambda_' parameter. 'True' is default in PPO.
            lambda_ = RAY_TRAIN_LAMBDA, # NOTE: This goes together with 'use_gae' parameter.
            vf_loss_coeff = RAY_TRAIN_VF_LOSS_COEFF,
            entropy_coeff = RAY_TRAIN_ENTROPY_COEFFICIENT,
            vf_clip_param = RAY_TRAIN_VF_CLIP_PARAM, # This goes together with 'use_critic = True'. 'False' is default in PPO.
            grad_clip = RAY_TRAIN_GRAD_CLIP,
            grad_clip_by = RAY_TRAIN_GRAD_CLIP_BY,
            gamma = RAY_TRAIN_GAMMA,
            lr = [
                [0, RAY_TRAIN_STARTING_LEARNING_RATE], # NOTE: This learning rate starts at time step 0.
                [10e5, RAY_TRAIN_ADJUSTED_LEARNING_RATE],
                [10e7, RAY_TRAIN_ENDING_LEARNING_RATE]
            ],
            minibatch_size = RAY_TRAIN_MINIBATCH,
            train_batch_size_per_learner = RAY_TRAIN_BATCH_PER_LEARNER,
            num_epochs = RAY_TRAIN_EPOCH,
        )
        .evaluation(
            evaluation_interval = RAY_EVAL_INTERVAL,
            evaluation_duration = RAY_EVAL_DURATION,
            evaluation_duration_unit = RAY_EVAL_DURATION_UNIT,
            evaluation_num_env_runners = RAY_EVAL_ENV_RUNNERS,
            # evaluation_auto_duration_min_env_steps_per_sample = None,
            # evaluation_auto_duration_max_env_steps_per_sample = None,
            evaluation_sample_timeout_s = 60,
            evaluation_parallel_to_training = True,
            evaluation_force_reset_envs_before_iteration = False
        )
        .reporting(
            keep_per_episode_custom_metrics = True,
            # metrics_episode_collection_timeout_s = None,
            metrics_num_episodes_for_smoothing = RAY_REPORTING_NUM_EPISODES_FOR_SMOOTHING,
            # min_time_s_per_iteration = None,
            # min_train_timesteps_per_iteration = None,
            # min_sample_timesteps_per_iteration = None,
            log_gradients = False
        )
        .learners(
            num_learners = RAY_LEARNERS,
            num_cpus_per_learner = RAY_CPUS - 3, # 1 - Train Env. Runner, 1 - Evaluation Env. Runner, 1 - Main Process
            num_gpus_per_learner = RAY_GPUS
        )
        .debugging(
            log_level = 'DEBUG'
        )
    )

    return config