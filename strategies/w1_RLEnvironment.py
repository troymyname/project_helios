# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://docs.ray.io/en/latest/tune/tutorials/tune-metrics.html
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import warnings
from config import WARNING_IGNORE_CLASS_USER, WARNING_IGNORE_CLASS_DEPRECATION
warnings.simplefilter(action = 'ignore', category = WARNING_IGNORE_CLASS_USER)
warnings.simplefilter(action = 'ignore', category = WARNING_IGNORE_CLASS_DEPRECATION)

import gymnasium
import numpy as np
import os
import random
import torch

# import custom configs and utils
from config import (
    RAY_DATA_TYPE,
    RAY_ENV_DEBUG_ON,
    RAY_ENV_DEBUG_VERBOSITY,
    RAY_ENV_DISCOUNT_FACTOR_ON,
    RAY_ENV_DISCOUNT_FACTOR,
    RAY_ENV_INITIAL_REWARD,
    RAY_ENV_PORTFOLIO_OVER_BALANCE_RATIO_MIN,
    RAY_ENV_PRICE_IN_BROWNIAN_MOTION,
    RAY_ENV_TIME_PENALTY_ON,
    RAY_REWARD_CLIP_RANGE
)
from utils.w2_optimizePortfolio import w2_optimizePortfolio
from utils.w2_performNumPyOps import w2_calculateNDiscreteDifference, w2_standardizeData
from utils.w2_calculateStats import w2_calculateSmartSharpe
from utils.w2_simulateBrownianMotion import w2_simulatePriceInBrownianMotion


class RLEnvironment(gymnasium.Env):
    """
    Reinforcement Learning environment for portfolio allocation and trading.

    The environment exposes a gymnasium-compatible interface that simulates a
    multi-asset portfolio using historical feature and support data. It supports
    random ticker sampling, portfolio execution of buy/hold/sell actions, and
    reward computation based on configurable metrics such as Sharpe, action
    performance, and drawdown penalties.

    Attributes:
        action_space (gymnasium.Space): MultiDiscrete action space for ticker selection and action type.
        observation_space (gymnasium.Space): Box observation space representing feature vectors for selected tickers.
        feature_data_dict (dict): Time-series feature matrices for each ticker.
        support_data_dict (dict): Reference pricing data used to compute buy/sell quotes.
        reward_config_arr (list): Flags enabling individual components of the reward function.
        reward_config_weights_arr (list): Weights for each enabled reward component.
    """
    def __init__(self, config):
        """
        Initialize the reinforcement learning environment from config.

        Parameters:
            config (dict): Environment configuration containing action/observation settings,
                reward settings, ticker lists, feature data, and support data.
        """
        # set seed for reproducibility
        self.seed_int = int(config['seed_int'])
        self.setSeed(seed_int = self.seed_int)

        # set parameters for padding observations (required for LSTM)
        self.padding_on = False
        self.padded_length_int = 256

        # extract required parameters
        self.quantity_int = int(config['quantity_int'])
        self.num_actions_int = int(config['num_actions_int'])
        self.recent_data_chunk_int = int(config['recent_data_chunk_int'])
        self.initial_balance_flt = float(config['constants_dict']['initial_balance_flt'])
        self.commission_flt = float(config['constants_dict']['commission_flt'])

        # extract reward configuration and corresponding weights
        self.reward_config_arr = config['reward_config_arr']
        self.reward_config_weights_arr = config['reward_config_weights_arr']

        # extract required data
        self.refined_sampled_tickers_list = list(config['refined_sampled_tickers_list'])
        self.feature_data_dict = config['feature_data_dict']
        self.support_data_dict = config['support_data_dict']

        # initialize environment parameters
        self.picked_tickers_list = []
        self.held_assets_dict = {}
        self.bought_assets_dict = {}
        self.buy_prices_dict = {}
        self.sold_assets_dict = {}
        self.sell_prices_dict = {}
        # --
        self.transaction_income_flt = 0.0
        self.transaction_expense_flt = 0.0
        # --
        self.current_step_int = 0
        self.current_reward_flt = 0.0
        self.current_reward_drawdown_peak_flt = None
        self.current_reward_clip_low_flt, self.current_reward_clip_high_flt = RAY_REWARD_CLIP_RANGE
        self.current_security_acquisition_incentive_flt = 0.0
        self.current_security_disposal_incentive_flt = 0.0
        self.current_cash_flt = self.initial_balance_flt
        self.current_portfolio_flt = self.initial_balance_flt
        self.current_transactions_dict = {}
        self.current_buy_prices_dict = {}
        self.current_sell_prices_dict = {}
        # --
        self.portfolio_history_narr = np.array([])
        self.reward_history_narr = np.array([])

        # initialize risk measure string (see w2_optimizePortfolio.py for details)
        self.risk_measure_str = 'MV'

        # define action space
        action_space = [self.quantity_int, self.num_actions_int]
        if self.seed_int != 0:
            self.action_space = gymnasium.spaces.MultiDiscrete(
                nvec = action_space,
                dtype = np.uint8,
                seed = self.seed_int,
            )
        else:
            self.action_space = gymnasium.spaces.MultiDiscrete(
                nvec = action_space,
                dtype = np.uint8
            )

        # define observation space
        if self.padding_on:
            self.observation_length_int = int(self.padded_length_int/self.quantity_int)
        else:
            self.observation_length_int = config['feature_data_dict'][self.refined_sampled_tickers_list[0]].shape[1]
        observation_space_tpl = (self.quantity_int, self.observation_length_int)
        if self.seed_int != 0:
            self.observation_space = gymnasium.spaces.Box(
                low = np.finfo(RAY_DATA_TYPE).min,
                high = np.finfo(RAY_DATA_TYPE).max,
                shape = observation_space_tpl,
                dtype = RAY_DATA_TYPE,
                seed = self.seed_int
            )
        else:
            self.observation_space = gymnasium.spaces.Box(
                low = np.finfo(RAY_DATA_TYPE).min,
                high = np.finfo(RAY_DATA_TYPE).max,
                shape = observation_space_tpl,
                dtype = RAY_DATA_TYPE
            )

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

    def sampleTickers(self):
        """
        Select tickers for the current environment step.

        If the refined ticker list is larger than the configured quantity, this
        method samples a random subset. Otherwise it copies the full list.
        """
        if len(self.refined_sampled_tickers_list) != self.quantity_int:
            self.picked_tickers_list = random.sample(self.refined_sampled_tickers_list, self.quantity_int).copy()
        else:
            self.picked_tickers_list = self.refined_sampled_tickers_list.copy()

    def reset(self, seed = None, options = None):
        """
        Reset the environment and return an initial observation.

        Parameters:
            seed: Optional seed parameter for compatibility with gymnasium reset API.
            options: Optional reset options for compatibility with gymnasium.

        Returns:
            tuple: A tuple containing the initial observation and info dictionary.
        """
        # initialize empty info dictionary
        info = {}
        # reset all trackers
        self.resetAllTrackers()
        # sample tickers
        self.sampleTickers()

        return self.deriveObservation(), info

    def stepPrint(self, step_reward_flt, verbose_int):
        """
        Print debugging output for the current environment step.

        Parameters:
            step_reward_flt (float): Reward achieved at the current step.
            verbose_int (int): Verbosity level controlling printed detail.
        """
        print()
        print('----------------------------------------------------------------------')
        print('Step | Reward:   {} | {}'.format(self.current_step_int, round(step_reward_flt, 2)))
        if verbose_int == 2:
            print('----------------------------------------------------------------------')
            print('Refined:         {}'.format(self.refined_sampled_tickers_list))
            print('Picked:          {}'.format(self.picked_tickers_list))
            print('Held             {}'.format(self.held_assets_dict))
            print('----------------------------------------------------------------------')
            print('Cash | Port.:    {} | {}'.format(round(self.current_cash_flt, 2), round(self.current_portfolio_flt, 2)))
        print('----------------------------------------------------------------------')
        print()

    def step(
            self,
            action,
            debug_on = RAY_ENV_DEBUG_ON,
            verbose_int = RAY_ENV_DEBUG_VERBOSITY,
            portfolio_over_balance_ratio_min_flt = RAY_ENV_PORTFOLIO_OVER_BALANCE_RATIO_MIN
    ):
        """
        Advance the environment by one action and return the next state.

        Parameters:
            action: Action array specifying ticker selection and action type.
            debug_on (bool): Whether debug printing is enabled.
            verbose_int (int): Level of verbosity for debug output.
            portfolio_over_balance_ratio_min_flt (float): Minimum portfolio ratio before truncation.

        Returns:
            tuple: observation, reward, terminated, truncated, info.
        """
        # sample tickers
        if self.current_step_int > 0:
            self.sampleTickers()
        # execute one step within the environment
        self.executeCurrentAction(
            action_arr = action
        )
        # derive return truncated flag, terminated flag, reward, observation, and information
        truncated = False # ((self.current_portfolio_flt / self.initial_balance_flt) <= portfolio_over_balance_ratio_min_flt)
        terminated = (self.current_step_int >= (len(self.feature_data_dict[self.picked_tickers_list[0]]) - 1))
        self.current_reward_flt = self.computeCurrentReward(
            action_arr = action,
            reward_config_arr = self.reward_config_arr
        )
        observation = self.deriveObservation()
        info = {
            'step': self.current_step_int,
            'reward': round(self.current_reward_flt, 2),
            'incentives': round(self.current_security_disposal_incentive_flt, 2),
            'cash': round(self.current_cash_flt, 2),
            'portfolio': round(self.current_portfolio_flt, 2),
            'transactions': self.current_transactions_dict,
            'income': round(self.transaction_income_flt, 2),
            'expense': round(self.transaction_expense_flt, 2),
            'picked_tickers_list': self.picked_tickers_list,
            'bought_assets_dict': self.bought_assets_dict,
            'sold_assets_dict': self.sold_assets_dict,
            'held_assets_dict': self.held_assets_dict
        }
        # display debug information once per iteration
        if debug_on and verbose_int > 0:
            self.stepPrint(
                step_reward_flt = self.current_reward_flt,
                verbose_int = verbose_int
            )
        # increment step number
        self.current_step_int += 1

        return observation, self.current_reward_flt, terminated, truncated, info

    def executeCurrentAction(self, action_arr):
        """
        Execute the selected action and update internal transaction state.

        Parameters:
            action_arr: Array containing action selection and action type.
        """
        # estimate current price
        self.estimateCurrentPrices(
            Brownian_Motion = RAY_ENV_PRICE_IN_BROWNIAN_MOTION
        )
        # execute actions
        self.resetIncomeExpenseTrackers()
        self.resetTransactionTrackers()
        self.executeHoldBuySell(
            selection_index_int = int(action_arr[0]),
            action_type_int = int(action_arr[1])
        )
        # generate current transaction records and computer current portfolio
        self.generateCurrentTransactionRecords()
        self.computeCurrentPortfolio()

    def executeHoldBuySell(
            self,
            selection_index_int,
            action_type_int,
            acquisition_incentive_period_int = 5
    ):
        """
        Execute hold, buy, or sell logic for the selected ticker.

        Parameters:
            selection_index_int (int): Index of the selected ticker within the current batch.
            action_type_int (int): Action type (0=hold, 1=buy, 2=sell).
            acquisition_incentive_period_int (int): Lookback period for acquisition incentive calculation.
        """
        # reset current security acquisition and disposal incentives
        self.current_security_acquisition_incentive_flt = 0.0
        self.current_security_disposal_incentive_flt = 0.0
        # execute actions
        for ticker_index_int, ticker_name_str in enumerate(self.picked_tickers_list):
            if ticker_index_int == selection_index_int:
                # ==
                # check for and execute hold action
                if action_type_int == 0:
                    # do not do anything
                    pass

                # ==
                # check for and execute buy action
                elif action_type_int == 1:
                    # check feasibility condition - ticker symbol not in held assets
                    buy_flag1 = ticker_name_str not in list(self.held_assets_dict.keys())
                    # check feasibility condition - no asset of ticker symbol held (dependent on buy_flag1)
                    if not buy_flag1:
                        buy_flag2 = int(self.held_assets_dict[ticker_name_str]) == 0
                    else:
                        buy_flag2 = False
                    if buy_flag1 or buy_flag2:
                        # extract weights for optimal portfolio
                        weights_dict = w2_optimizePortfolio(
                            picked_tickers_list = self.picked_tickers_list,
                            risk_measure_selection_str = self.risk_measure_str
                        )[self.risk_measure_str]
                        if isinstance(weights_dict, dict):
                            # compute buy quantity
                            if float(self.current_buy_prices_dict[ticker_name_str]) != 0.0:
                                # calculate buy quantity without fraction
                                buy_quantity_int = int((float(weights_dict[ticker_name_str]) * self.current_cash_flt) // float(self.current_buy_prices_dict[ticker_name_str]))
                            else:
                                buy_quantity_int = 0

                            if buy_quantity_int >= 1:
                                # buy security
                                self.buySecurity(
                                    ticker_name_str = ticker_name_str,
                                    buy_quantity_int = buy_quantity_int
                                )
                                # update current security acquisition incentive (i.e. more incentive if bought cheaper than mean of previous n closing price(s))
                                if self.current_step_int >= acquisition_incentive_period_int:
                                    self.current_security_acquisition_incentive_flt = (
                                            np.mean(self.support_data_dict[ticker_name_str]['close'].iloc[(self.current_step_int - acquisition_incentive_period_int):self.current_step_int]) -
                                            float(self.current_buy_prices_dict[ticker_name_str])
                                    )
                            else:
                                pass
                        else:
                            print("ERROR: Weights are not in preferred format...")
                            assert type(weights_dict) == dict
                    else:
                        pass

                # ==
                # check for and execute sell action
                elif action_type_int == 2:
                    # check feasibility condition - ticker symbol in held assets
                    sell_flag1 = ticker_name_str in list(self.held_assets_dict.keys())
                    # check feasibility condition - asset of ticker symbol held (dependent on sell_flag1)
                    if sell_flag1:
                        sell_flag2 = int(self.held_assets_dict[ticker_name_str]) != 0
                    else:
                        sell_flag2 = False
                    if sell_flag1 and sell_flag2:
                        # sell security
                        self.sellSecurity(
                            ticker_name_str = ticker_name_str
                        )
                        # update current security disposal incentive (i.e. more incentive if sold with profit)
                        self.current_security_disposal_incentive_flt = (
                                float(self.sell_prices_dict[ticker_name_str]) - float(self.buy_prices_dict[ticker_name_str])
                        )
                    else:
                        pass

    def buySecurity(self, ticker_name_str, buy_quantity_int):
        """
        Record a buy transaction and update cash, holdings, and expense trackers.

        Parameters:
            ticker_name_str (str): Ticker symbol being purchased.
            buy_quantity_int (int): Quantity of shares to buy.
        """
        # update bought assets records
        self.bought_assets_dict[ticker_name_str] = buy_quantity_int
        self.buy_prices_dict[ticker_name_str] = self.current_buy_prices_dict[ticker_name_str]
        # update held assets records
        self.held_assets_dict[ticker_name_str] = 0
        self.held_assets_dict[ticker_name_str] += self.bought_assets_dict[ticker_name_str]
        # update transaction expense/expense
        self.transaction_expense_flt = int(self.bought_assets_dict[ticker_name_str]) * float(self.current_buy_prices_dict[ticker_name_str]) * (1.0 + self.commission_flt)
        # update cash balance
        self.current_cash_flt -= self.transaction_expense_flt

    def sellSecurity(self, ticker_name_str):
        """
        Record a sell transaction and update cash, holdings, and income trackers.

        Parameters:
            ticker_name_str (str): Ticker symbol being sold.
        """
        # update sold assets records
        self.sold_assets_dict[ticker_name_str] = self.held_assets_dict[ticker_name_str]
        self.sell_prices_dict[ticker_name_str] = self.current_sell_prices_dict[ticker_name_str]
        # update held assets records
        self.held_assets_dict[ticker_name_str] -= self.sold_assets_dict[ticker_name_str]
        _ = self.held_assets_dict.pop(ticker_name_str)
        # update transaction income/expense
        self.transaction_income_flt = int(self.sold_assets_dict[ticker_name_str]) * float(self.current_sell_prices_dict[ticker_name_str]) * (1.0 - self.commission_flt)
        # update cash balance
        self.current_cash_flt += self.transaction_income_flt

    def generateCurrentTransactionRecords(self):
        """
        Build the current transaction summary dictionary for the active tickers.

        The method includes positive quantities for buys and negative quantities for sells.
        """
        for ticker_str in self.picked_tickers_list:
            try:
                if self.bought_assets_dict[ticker_str] > 0:
                    self.current_transactions_dict.update({ticker_str: str(self.bought_assets_dict[ticker_str])})
            except KeyError:
                pass
            try:
                if self.sold_assets_dict[ticker_str] > 0:
                    self.current_transactions_dict.update({ticker_str: "-" + str(self.sold_assets_dict[ticker_str])})
            except KeyError:
                pass

    def estimateCurrentPrices(self, Brownian_Motion):
        """
        Estimate current buy and sell prices for the selected tickers.

        Parameters:
            Brownian_Motion (bool): Whether to simulate prices using Brownian motion.
        """
        if Brownian_Motion:
            # for each ticker symbol, simulate 390 trading minutes of stock price fluctuation starting from open price, and pick buy/sell price randomly
            # NOTE: In the future the price selection will be directed by another system.
            for ticker_str in self.picked_tickers_list:
                _, simulation_values_arr = w2_simulatePriceInBrownianMotion(
                    initial_value_flt = float(self.support_data_dict[ticker_str]['open'].iloc[self.current_step_int]),
                    samples_int = 390*60
                )
                self.current_buy_prices_dict[ticker_str] = float(random.choice(simulation_values_arr))
                self.current_sell_prices_dict[ticker_str] = float(random.choice(simulation_values_arr))
        else:
            # for each ticker symbol, assume that security is bought at the lowest price of the day and sold at the highest price of the day
            # NOTE: Even though this is an assumption, this removes stochasticity from the training/evaluation process.
            # NOTE: This is OK for selection of potential tickers based on historical daily data.
            for ticker_str in self.picked_tickers_list:
                self.current_buy_prices_dict[ticker_str] = float(self.support_data_dict[ticker_str]['low'].iloc[self.current_step_int])
                self.current_sell_prices_dict[ticker_str] = float(self.support_data_dict[ticker_str]['high'].iloc[self.current_step_int])

    def computeCurrentPortfolio(self):
        """
        Compute the current portfolio value from cash and held asset positions.
        """
        self.current_portfolio_flt = self.current_cash_flt
        for ticker_str in self.held_assets_dict.keys():
            # NOTE: Usage of sell price to compute portfolio is intentional!
            self.current_portfolio_flt += self.held_assets_dict[ticker_str]*self.current_sell_prices_dict[ticker_str]
        # save portfolio change history
        self.portfolio_history_narr = np.append(self.portfolio_history_narr, self.current_portfolio_flt)

    def computeCurrentReward(
            self,
            action_arr,
            reward_config_arr,
            sharpe_period_int = 256,
            dbz_prevent_flt = 1e-3,
            standardization_min_quantity_int = 7, # NOTE: This value was chosen to standardize by a week.
            rolling_window_standardization_on = True,
            initial_reward_flt = RAY_ENV_INITIAL_REWARD,
            discount_factor_on = RAY_ENV_DISCOUNT_FACTOR_ON,
            discount_factor_flt = RAY_ENV_DISCOUNT_FACTOR,
            time_penalty_on = RAY_ENV_TIME_PENALTY_ON
    ):
        """
        Compute the reward for the current step using configured reward components.

        Parameters:
            action_arr: Action array executed by the agent.
            reward_config_arr (list): Flags indicating which reward components are enabled.
            sharpe_period_int (int): Lookback period for Sharpe reward computation.
            dbz_prevent_flt (float): Small constant to avoid division by zero.
            standardization_min_quantity_int (int): Minimum reward history length for standardization.
            rolling_window_standardization_on (bool): Whether to standardize using a rolling window.
            initial_reward_flt (float): Default reward used when insufficient history exists.
            discount_factor_on (bool): If True, apply discount factor.
            discount_factor_flt (float): Discount factor multiplier.
            time_penalty_on (bool): If True, apply a time-based penalty to the reward.

        Returns:
            float: Clipped and standardized reward for the current step.
        """
        # initialize current reward and current standardized reward
        current_reward_flt = 0.0
        current_standardized_reward_flt = 0.0

        # ==== ==== construct rewarding method
        # compute Sharpe-based reward
        if reward_config_arr[0]:
            if len(self.portfolio_history_narr) > sharpe_period_int:
                # compute portfolio returns and current reward
                portfolio_returns_narr = w2_calculateNDiscreteDifference(
                    narr = self.portfolio_history_narr,
                    period = 1
                )
                current_reward_flt = w2_calculateSmartSharpe(
                    returns_narr = portfolio_returns_narr,
                    period_int = sharpe_period_int,
                    annualize_on = True
                ) * self.reward_config_weights_arr[0]
            else:
                current_reward_flt = initial_reward_flt * self.reward_config_weights_arr[0]

        # --

        # compute action-based reward
        if reward_config_arr[1]:
            for ticker_index_int, ticker_name_str in enumerate(self.picked_tickers_list):
                if ticker_index_int == int(action_arr[0]):
                    if int(action_arr[1]) == 0:
                        # reward agent if portfolio value increased/decreased
                        if self.current_step_int != 0:
                            current_reward_flt += (self.portfolio_history_narr[-1] - self.portfolio_history_narr[-2]) * self.reward_config_weights_arr[1]
                        else:
                            current_reward_flt += initial_reward_flt * self.reward_config_weights_arr[1]
                    elif int(action_arr[1]) == 1:
                        # reward agent if security is bought cheaper, else penalize
                        if self.current_step_int != 0:
                            current_reward_flt += self.current_security_acquisition_incentive_flt * self.reward_config_weights_arr[1]
                        else:
                            current_reward_flt += initial_reward_flt * self.reward_config_weights_arr[1]
                    elif int(action_arr[1]) == 2:
                        # reward agent if security is sold with profit, else penalize
                        current_reward_flt += self.current_security_disposal_incentive_flt * self.reward_config_weights_arr[1]
                    else:
                        pass

        # --

        # compute step portfolio change + drawdown penalty
        if reward_config_arr[2]:
            if len(self.portfolio_history_narr) > 1:
                # compute current reward
                current_reward_flt += (self.portfolio_history_narr[-1] - self.portfolio_history_narr[-2])/(self.portfolio_history_narr[-2] + dbz_prevent_flt)

                # penalize based on drawdown
                if self.current_reward_drawdown_peak_flt is None:
                    self.current_reward_drawdown_peak_flt = max([self.portfolio_history_narr[-2], self.portfolio_history_narr[-1], 0.0])
                else:
                    self.current_reward_drawdown_peak_flt = max([self.current_reward_drawdown_peak_flt, self.portfolio_history_narr[-2], self.portfolio_history_narr[-1]])
                current_reward_flt += max([0.0, (self.current_reward_drawdown_peak_flt - self.portfolio_history_narr[-1])/(self.current_reward_drawdown_peak_flt + dbz_prevent_flt)]) * self.reward_config_weights_arr[2]

        # ==== ====

        # computer reward with time penalty and/or discount factor applied
        if time_penalty_on:
            current_reward_flt = current_reward_flt * (100.0 / ((0.01 * self.current_step_int) + 1))
        if discount_factor_on:
            current_reward_flt = current_reward_flt * discount_factor_flt

        # keep a running history of reward values
        self.reward_history_narr = np.append(self.reward_history_narr, current_reward_flt)

        # compute standardized reward
        if rolling_window_standardization_on:
            current_standardized_reward_flt = w2_standardizeData(
                sample_flt = current_reward_flt,
                sample_history_narr = self.reward_history_narr[-standardization_min_quantity_int:]
            )
        else:
            if len(self.reward_history_narr) >= standardization_min_quantity_int:
                current_standardized_reward_flt = w2_standardizeData(
                    sample_flt = current_reward_flt,
                    sample_history_narr = self.reward_history_narr
                )
            else:
                current_standardized_reward_flt = initial_reward_flt

        # compute clipped reward
        clipped_current_standardized_reward_flt = max([self.current_reward_clip_low_flt, min([self.current_reward_clip_high_flt, current_standardized_reward_flt])])

        return clipped_current_standardized_reward_flt

    def deriveObservation(self):
        """
        Construct the current observation array from selected ticker features.

        Returns:
            np.ndarray: Observation array shaped by selected tickers and feature dimensions.
        """
        if self.padding_on:
            # construct observation array and apply padding on observations if a use_lstm = True argument is used in rl_module configuration
            observation_arr = np.empty(
                shape = (0, int(self.padded_length_int/self.quantity_int)),
                dtype = RAY_DATA_TYPE
            )
            for ticker_str in self.picked_tickers_list:
                current_pick_observation_narr = np.array(self.feature_data_dict[ticker_str].values[self.current_step_int])
                current_pick_observation_padded_narr = np.pad(
                    array = current_pick_observation_narr,
                    pad_width = (0, (int(self.padded_length_int/self.quantity_int) - len(current_pick_observation_narr))),
                    mode = 'constant',
                    constant_values = 0.0
                )
                observation_arr = np.append(
                    arr = observation_arr,
                    values = current_pick_observation_padded_narr.reshape((1, int(self.padded_length_int/self.quantity_int))),
                    axis = 0
                )
        else:
            # construct observation array
            observation_arr = np.empty(
                shape = (0, self.observation_length_int),
                dtype = RAY_DATA_TYPE
            )
            for ticker_str in self.picked_tickers_list:
                current_pick_observation_narr = np.array(self.feature_data_dict[ticker_str].values[self.current_step_int])
                observation_arr = np.append(
                    arr = observation_arr,
                    values = current_pick_observation_narr.reshape((1, self.observation_length_int)),
                    axis = 0
                )

        return observation_arr.astype(RAY_DATA_TYPE)

    def resetIncomeExpenseTrackers(self):
        """
        Reset the environment's income and expense trackers for the current step.
        """
        self.transaction_income_flt = None
        self.transaction_income_flt = 0.0
        self.transaction_expense_flt = None
        self.transaction_expense_flt = 0.0

    def resetTransactionTrackers(self):
        """
        Reset per-step transaction tracking dictionaries.
        """
        self.bought_assets_dict = None
        self.bought_assets_dict = {}
        self.sold_assets_dict = None
        self.sold_assets_dict = {}
        self.current_transactions_dict = None
        self.current_transactions_dict = {}

    def resetAllTrackers(self):
        """
        Reset all environment trackers to their default state.

        This includes tickers, holdings, cash, portfolio metrics, and reward history.
        """
        # reset environment parameters
        self.picked_tickers_list = None
        self.picked_tickers_list = []
        self.held_assets_dict = None
        self.held_assets_dict = {}
        self.bought_assets_dict = None
        self.bought_assets_dict = {}
        self.buy_prices_dict = None
        self.buy_prices_dict = {}
        self.sold_assets_dict = None
        self.sold_assets_dict = {}
        self.sell_prices_dict = None
        self.sell_prices_dict = {}
        # --
        self.transaction_income_flt = None
        self.transaction_income_flt = 0.0
        self.transaction_expense_flt = None
        self.transaction_expense_flt = 0.0
        # --
        self.current_step_int = None
        self.current_step_int = 0
        self.current_reward_flt = None
        self.current_reward_flt = 0.0
        self.current_reward_drawdown_peak_flt = None
        self.current_reward_clip_low_flt, self.current_reward_clip_high_flt = RAY_REWARD_CLIP_RANGE
        self.current_security_acquisition_incentive_flt = None
        self.current_security_acquisition_incentive_flt = 0.0
        self.current_security_disposal_incentive_flt = None
        self.current_security_disposal_incentive_flt = 0.0
        self.current_cash_flt = None
        self.current_cash_flt = self.initial_balance_flt
        self.current_portfolio_flt = None
        self.current_portfolio_flt = self.initial_balance_flt
        self.current_transactions_dict = None
        self.current_transactions_dict = {}
        self.current_buy_prices_dict = None
        self.current_buy_prices_dict = {}
        self.current_sell_prices_dict = None
        self.current_sell_prices_dict = {}
        # --
        self.portfolio_history_narr = None
        self.portfolio_history_narr = np.array([])
        self.reward_history_narr = None
        self.reward_history_narr = np.array([])