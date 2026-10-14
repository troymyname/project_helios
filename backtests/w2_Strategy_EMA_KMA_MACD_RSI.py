# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://www.backtrader.com/
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import backtrader as bt

from copy import deepcopy

# import custom configs and utils
from config import IBKR_COMMISSION, TRADE_PRICE_CHANGE_SAFETY_THRESHOLD
from backtests.w2_KalmanMovingAverage import KalmanMovingAverage


# create a strategy
class Strategy_EMA_KMA_MACD_RSI(bt.Strategy):
    params = (
        ('macd_period_low_int', 12),
        ('macd_period_high_int', 26),
        ('macd_period_signal_int', 9),
        ('rsi_period_int', 14),
        ('rsi_lower_bound_flt', 15.0),
        ('rsi_upper_bound_flt', 85.0),
        ('ema_period_high_int', 21),
        ('min_comparison_gap_flt', 0.02),
        ('commission_flt', IBKR_COMMISSION),
        ('trade_price_change_safety_thresh_flt', TRADE_PRICE_CHANGE_SAFETY_THRESHOLD),
        ('verbose_on', True)
    )

    def __init__(self):
        # define parameters
        self.order = None
        self.bar_executed = None
        self.buy_price_flt = None
        self.buy_comm_flt = None
        self.close_price_flt = self.datas[0].close
        self.prev_price_at_buy = 0.0
        self.prev_kma_at_buy = 0.0
        self.rounding_int = 2
        self.lock_on = False

        # add high Exponential (or Exponentially Weighted) Moving Average indicators
        self.hema = bt.indicators.ExponentialMovingAverage(
            period = self.params.ema_period_high_int
        )

        # add Kalman Moving Average indicator
        self.kma = KalmanMovingAverage()

        # add Moving Average Convergence Divergence indicator
        self.macd = bt.indicators.MACD(
            period_me1 = self.params.macd_period_low_int,
            period_me2 = self.params.macd_period_high_int,
            period_signal = self.params.macd_period_signal_int
        )

        # add Relative Strength Index indicator
        self.rsi = bt.indicators.RelativeStrengthIndex(
            period = self.params.rsi_period_int
        )

        # # add Laguerre Filter Indicator
        # self.lf = bt.indicators.LaguerreFilter(
        #     period = self.params.rsi_period_int
        # )

        # # add Laguerre Relative Strength Index Indicator
        # self.lrsi = bt.indicators.LaguerreRSI(
        #     period = self.params.rsi_period_int
        # )

    def log(self, txt, dt = None):
        if self.params.verbose_on:
            dt = dt or self.datas[0].datetime.date(0)
            print('-- %s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # do nothing if buy/sell order submitted/accepted to/by broker
            return

        # check if an order has been completed
        if order.status in [order.Completed]:
            # execute buy order
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (
                             order.executed.price,
                             order.executed.value,
                             order.executed.comm
                         )
                         )
                print()
                self.buy_price_flt = order.executed.price
                self.buy_comm_flt = order.executed.comm
            # execute sell order
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (
                             order.executed.price,
                             order.executed.value,
                             order.executed.comm
                         )
                         )
            # get the length of the dataset
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %(trade.pnl, trade.pnlcomm))
        print()

    # def notify_cashvalue(self, cash, value):
    #     # NOTE: This was created for future usage purposes.
    #     pass

    # def notify_fund(self, cash, value, fundvalue, shares):
    #     # NOTE: This was created for future usage purposes.
    #     pass

    def start(self):
        if self.params.verbose_on:
            print('INFO: Backtesting is about to start...')
            print()
    
    def next(self):
        # log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.close_price_flt[0])
        # check if an order is pending, if yes, do nothing
        if self.order:
            return

        # check Relative Strength Index conditions
        if round(self.rsi.rsi[0], self.rounding_int) > self.params.rsi_upper_bound_flt:
            self.lock_on = False
        elif round(self.rsi.rsi[0], self.rounding_int) <= self.params.rsi_lower_bound_flt:
            # NOTE: This condition was introduced to exit the market when early signs of sharp sell-off are detected, and never enter again for *some* time.
            self.lock_on = True

        # check if in the market
        if not self.position:
            # check buy condition
            acquisition_condition1 = (
                    (round(self.macd.signal[0], self.rounding_int) + self.params.min_comparison_gap_flt < round(self.macd.macd[0], self.rounding_int)) and
                    (round(self.kma.kma[0], self.rounding_int) > round(self.hema[0], self.rounding_int) + self.params.min_comparison_gap_flt)
            )
            acquisition_condition2 = (not self.lock_on)
            if acquisition_condition1 and acquisition_condition2:
                # execute buy
                self.log('BUY CREATE, %.2f' % self.close_price_flt[0])
                # print parameters for verification
                self.log(f'MACD Signal/Line: {self.macd.signal[0]}/{self.macd.macd[0]}, KMA: {self.kma.kma[0]}, EWMA: {self.hema[0]}')
                # keep track of the created order to avoid a second order
                self.order = self.buy()
                # keep track of previous buy price and previous smoothed buy price
                self.prev_price_at_buy = round(self.close_price_flt[0], self.rounding_int)
                self.prev_kma_at_buy = deepcopy(round(self.kma.kma[0], self.rounding_int))

        else:
            # NOTE: Commission fees for both buying and selling are accounted for.
            disposal_condition1 = (
                    (round(self.macd.signal[0], self.rounding_int) > round(self.macd.macd[0], self.rounding_int) + self.params.min_comparison_gap_flt) and
                    (round(self.kma.kma[0], self.rounding_int) + self.params.min_comparison_gap_flt < round(self.hema[0], self.rounding_int)) and
                    (round(self.kma.kma[0], self.rounding_int) > self.prev_kma_at_buy + self.params.min_comparison_gap_flt) and
                    (round(self.close_price_flt[0], self.rounding_int) > (self.prev_price_at_buy + (self.params.commission_flt*2) + self.params.trade_price_change_safety_thresh_flt))
            )
            disposal_condition2 = (self.lock_on == True)
            if disposal_condition1 or disposal_condition2:
                # execute sell
                self.log('SELL CREATE, %.2f' % self.close_price_flt[0])
                # print parameters for verification
                self.log(f'MACD Signal/Line: {self.macd.signal[0]}/{self.macd.macd[0]}, KMA: {self.kma.kma[0]}, EWMA: {self.hema[0]}, Prev. Buy Price Smoothed: {self.prev_kma_at_buy}')
                # keep track of the created order to avoid a second order
                self.order = self.sell()

    def stop(self):
        if self.params.verbose_on:
            print('INFO: Backtesting is completed!')