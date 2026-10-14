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
class Strategy_SMA(bt.Strategy):
    params = (
        ('moving_average_period_int', 90),
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

        # add Simple Moving Average indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0],
            period = self.params.moving_average_period_int
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
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
    
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
            if self.close_price_obj[0] > self.sma[0]:
                # execute buy
                self.log('BUY CREATE, %.2f' % self.close_price_obj[0])
                # keep track of the created order to avoid a 2nd order
                self.order = self.buy()
        else:
            if self.close_price_obj[0] < self.sma[0]:
                # execute sell
                self.log('SELL CREATE, %.2f' % self.close_price_obj[0])
                # keep track of the created order to avoid a 2nd order
                self.order = self.sell()