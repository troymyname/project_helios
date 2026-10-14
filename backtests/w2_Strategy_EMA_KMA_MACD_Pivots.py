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
from backtests.w2_KalmanMovingAverage import KalmanMovingAverage


# create a strategy
class Strategy_EMA_KMA_MACD_Pivots(bt.Strategy):
    params = (
        ('macd_period_low_int', 12),
        ('macd_period_high_int', 26),
        ('macd_period_signal_int', 9),
        ('rsi_period_int', 14),
        ('ema_period_high_int', 21),
        ('verbose_on', True)
    )

    def __init__(self):
        # define parameters
        self.order = None
        self.bar_executed = None
        self.buy_price_flt = None
        self.buy_comm_flt = None
        self.close_price_flt = self.datas[0].close
        self.prev_buy_price_smoothed_flt = 0.0

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

        # add Pivot Point Indicator (NOTE: Setting _autoplot = False shows the plots.)
        self.pivots = bt.indicators.PivotPoint(
            open = False,
            close = True,
            _autoplot = False
        )

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

    # def notify_cashvalue(self, cash, value):
    #     # NOTE: This was created for future usage purposes.
    #     pass

    # def notify_fund(self, cash, value, fundvalue, shares):
    #     # NOTE: This was created for future usage purposes.
    #     pass

    def start(self):
        if self.params.verbose_on:
            print('INFO: Backtesting is about to start...')
    
    def next(self):
        # log the closing price of the series from the reference
        self.log('Close, %.2f' % self.close_price_flt[0])
        # check if an order is pending, if yes, do nothing
        if self.order:
            return
        # check if in the market
        if not self.position:
            # check buy condition
            acquisition_condition1 = (self.macd.signal[0] > self.macd.macd[0]) and (self.kma.kma[0] > self.hema[0])
            if acquisition_condition1:
                # execute buy
                self.log('BUY CREATE, %.2f' % self.close_price_flt[0])
                # print parameters for verification
                self.log(f'MACD Signal/Line: {self.macd.signal[0]}/{self.macd.macd[0]}, KMA: {self.kma.kma[0]}, HEMA: {self.hema[0]}')
                # keep track of the created order to avoid a second order
                self.order = self.buy()
                # keep track of previous smoothed buy price
                self.prev_buy_price_smoothed_flt = deepcopy(self.kma.kma[0])
        else:
            disposal_condition1 = (self.macd.signal[0] < self.macd.macd[0]) and (self.kma.kma[0] < self.hema[0]) and (self.kma.kma[0] > self.prev_buy_price_smoothed_flt)
            if disposal_condition1:
                # execute sell
                self.log('SELL CREATE, %.2f' % self.close_price_flt[0])
                # print parameters for verification
                self.log(f'MACD Signal/Line: {self.macd.signal[0]}/{self.macd.macd[0]}, KMA: {self.kma.kma[0]}, HEMA: {self.hema[0]}, Prev. Buy Price Smoothed: {self.prev_buy_price_smoothed_flt}')
                # keep track of the created order to avoid a second order
                self.order = self.sell()

    def stop(self):
        if self.params.verbose_on:
            print('INFO: Backtesting is completed!')