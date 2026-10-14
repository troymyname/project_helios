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

import backtrader as bt


# create a strategy
class Strategy_EMA_BB(bt.Strategy):
    params = (
        ('ema_period_low_int', 9),
        ('ema_period_high_int', 21),
        ('bb_period_int', 20),
        ('bb_stdev_flt', 2.0)
    )

    def log(self, txt, dt = None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order = None
        self.bar_executed = None
        self.buy_price_flt = None
        self.buy_comm_flt = None
        self.close_price_obj = self.datas[0].close

        # add low and high Exponential Moving Average indicators
        self.lema = bt.indicators.ExponentialMovingAverage(
            period = self.params.ema_period_low_int
        )
        self.hema = bt.indicators.ExponentialMovingAverage(
            period = self.params.ema_period_high_int
        )

        # add Bollinger Bands indicator
        self.bb = bt.indicators.BollingerBands(
            period = self.params.bb_period_int,
            devfactor = self.params.bb_stdev_flt
        )

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

    def next(self):
        # log the closing price of the series from the reference
        self.log('Close, %.2f' % self.close_price_obj[0])
        # check if an order is pending, if yes, do nothing
        if self.order:
            return
        # check if in the market
        if not self.position:
            # check buy condition
            if (self.lema[0] > self.hema[0]) and (self.close_price_obj[0] > self.bb.lines.top[0]):
                # execute buy
                self.log('BUY CREATE, %.2f' % self.close_price_obj[0])
                # keep track of the created order to avoid a 2nd order
                self.order = self.buy()
        else:
            if (self.lema[0] < self.hema[0]) and (self.close_price_obj[0] < self.bb.lines.bot[0]):
                # execute sell
                self.log('SELL CREATE, %.2f' % self.close_price_obj[0])
                # keep track of the created order to avoid a 2nd order
                self.order = self.sell()