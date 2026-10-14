# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://www.interactivebrokers.com/campus/trading-lessons/python-receiving-market-data/
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import threading
import time

from ibapi.client import *
from ibapi.ticktype import TickTypeEnum
from ibapi.wrapper import *

# import custom configs and utils
from config import IBKR_LIVE_DATA_CLIENT_ID, IBKR_WAIT_TIME_LIVE_DATA_DOWN


class LiveDataGetter(EClient, EWrapper):
    def __init__(self):
        # initialize
        EClient.__init__(self, self)
        self.orderId = 0
        self.live_data_dict = {}
        
    def nextValidId(self, orderId):
        # receive next valid orderId
        self.orderId = orderId

    def nextId(self):
        # increment orderId and return
        self.orderId += 1
        return self.orderId
    
    def error(
        self,
        reqId: TickerId,
        errorTime: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson = '',
    ):
        # print details
        # print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}")
        pass

    def tickPrice(self, reqId, tickType, price, attrib):
        # print details
        # print(f"reqId: {reqId}, tickType: {TickTypeEnum.toStr(tickType)}, price: {price}, attrib: {attrib}")
        # gather data in a dictionary and merge (value on right of '|' is prioritized)
        temp_dict = {
            f"{TickTypeEnum.toStr(tickType)}": round(price, 2),
        }
        self.live_data_dict = self.live_data_dict | temp_dict

    # def tickSize(self, reqId, tickType, size):
    #     # NOTE: This was created for future usage purposes.
    #     # print details
    #     print(f"reqId: {reqId}, tickType: {TickTypeEnum.toStr(tickType)}, size: {size}")


def w1_if_getLiveData(
        ticker_str,
        additional_wait_time_flt = 0.0,
        simulated_on = True
    ):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # construct the application
    app = LiveDataGetter()
    if not simulated_on:
        app.connect(
            host = "127.0.0.1",
            port = 7496,
            clientId = IBKR_LIVE_DATA_CLIENT_ID
        )
    else:
        app.connect(
            host = "127.0.0.1",
            port = 7497,
            clientId = IBKR_LIVE_DATA_CLIENT_ID
        )

    # start the socket in a thread
    threading.Thread(target = app.run).start()

    # construct contract
    contract_object = Contract()
    contract_object.symbol = ticker_str
    contract_object.secType = 'STK'
    contract_object.currency = 'USD'
    contract_object.exchange = 'SMART'

    # request market data type (1 - live, 2 - frozen, 3 - delayed, 4 - delayed frozen)
    app.reqMarketDataType(marketDataType = 3)
    app.reqMktData(
        reqId = app.nextId(), 
        contract = contract_object, 
        genericTickList = "232", 
        snapshot = False, 
        regulatorySnapshot = False, 
        mktDataOptions = []
        )
    
    # allow time for incoming data (and dynamically adjust the wait time as needed)
    counter_int = 0
    while not app.live_data_dict:
        time.sleep(IBKR_WAIT_TIME_LIVE_DATA_DOWN + additional_wait_time_flt)
        additional_wait_time_flt += 0.5
        counter_int += 1
        # force to break out of loop if counter value of 4 is reached
        if counter_int >= 4:
            break

    # terminate connection with TWS
    app.disconnect()

    # derive last known price
    last_known_price_flt = 0.0
    for key_str in app.live_data_dict.keys():
        if 'LAST' in key_str:
            last_known_price_flt = float(app.live_data_dict[key_str])
        elif 'CLOSE' in key_str:
            last_known_price_flt = float(app.live_data_dict[key_str])
        elif 'PRICE' in key_str:
            last_known_price_flt = float(app.live_data_dict[key_str])
        else:
            last_known_price_flt = 0.0

    return last_known_price_flt, app.live_data_dict


if __name__ == '__main__':
    # specify ticker symbol
    symbol_str = 'SPY'

    # download data
    last_known_price, data_dict = w1_if_getLiveData(
        ticker_str = symbol_str,
        simulated_on = True
    )

    print()
    print(data_dict)
    print()
    print(f'The last known price is for {symbol_str} is {last_known_price}.')
    print()