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

import threading
import time

from ibapi.client import *
from ibapi.wrapper import *

# import custom configs and utils
from config import (
    IBKR_ORDER_CLIENT_ID,
    IBKR_WAIT_TIME_TRADE
)

class OrderSender(EClient, EWrapper):
    """
    Interactive Brokers order sender client wrapper.

    This class combines the IB API client and wrapper interfaces to construct
    and place a stock order for a given ticker. It also captures order status
    updates in a structured dictionary for downstream inspection.
    """
    def __init__(
            self,
            ticker_str,
            action_type_str,
            quantity_int,
            order_type_str = 'MKT',
            limit_order_price_flt = 0.0,
            tif_str = 'DAY'
    ):
        """
        Initialize the IB order sender.

        Parameters:
            ticker_str (str): The equity ticker symbol to trade.
            action_type_str (str): Order side, typically 'BUY' or 'SELL'.
            quantity_int (int): Number of shares to trade.
            order_type_str (str): Order type, such as 'MKT' or 'LMT'.
            limit_order_price_flt (float): Limit price when using a limit order.
            tif_str (str): Time-in-force instruction, e.g. 'DAY', 'GTC', or 'IOC'.
        """
        # initialize
        EClient.__init__(self, self)
        self.orderId = 0
        self.ticker_str = ticker_str
        self.action_type_str = action_type_str
        self.quantity_int = quantity_int
        self.order_type_str = order_type_str # 'MKT' / 'LMT'
        self.limit_price_flt = limit_order_price_flt
        self.tif_str = tif_str # 'DAY' / 'GTC' / 'IOC'
        self.order_information_stream_count_int = -1
        self.order_information_dict = {}
        self.done = False

    def error(
        self,
        reqId: TickerId,
        errorTime: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson = ''
    ):
        """
        Handle error messages received from the IB API.

        Parameters:
            reqId (TickerId): Request identifier.
            errorTime (int): Timestamp of the error.
            errorCode (int): IB error code.
            errorString (str): Error message text.
            advancedOrderRejectJson: Optional advanced rejection details.
        """
        # print details
        # print(f'reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}')
        pass
    
    def nextValidId(self, orderId: int):
        """
        Receive the next valid order identifier from the IB API.

        Parameters:
            orderId (int): Next available IB order identifier.
        """
        # construct an instance of a contract
        contract_obj = Contract()
        contract_obj.symbol = self.ticker_str
        contract_obj.secType = 'STK'
        contract_obj.exchange = 'SMART'
        contract_obj.currency = 'USD'
        self.reqContractDetails(
            reqId = orderId,
            contract = contract_obj
        )

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        """
        Receive contract details and place the order once the contract is resolved.

        Parameters:
            reqId (int): Request identifier used as the order ID.
            contractDetails (ContractDetails): Resolved contract details from IB.
        """
        # construct contract details
        order_obj = Order()
        order_obj.orderId = reqId
        order_obj.action = self.action_type_str
        order_obj.totalQuantity = self.quantity_int
        order_obj.orderType = self.order_type_str
        if self.order_type_str == 'LMT' and self.limit_price_flt != 0.0:
            order_obj.lmtPrice = self.limit_price_flt
        order_obj.tif = self.tif_str
        # place order
        self.placeOrder(
            orderId = reqId,
            contract = contractDetails.contract,
            order = order_obj
        )

    # def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
    #     # NOTE: This was created for future usage purposes.
    #     # print details
    #     print(f"OpenOrder > orderId: {orderId}, contract: {contract}, order: {order}, orderState: {orderState}")

    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        """
        Receive order status updates and record them in the internal dictionary.

        Parameters:
            orderId (OrderId): Order identifier.
            status (str): Current order status.
            filled (float): Quantity filled so far.
            remaining (float): Quantity remaining.
            avgFillPrice (float): Average fill price.
            permId (int): Permanent order identifier.
            parentId (int): Parent order identifier.
            lastFillPrice (float): Price of the last fill.
            clientId (int): Client identifier.
            whyHeld (str): Explanation for holds, if any.
            mktCapPrice (float): Market cap price.
        """
        # print details
        # print(f"OrderStatus > orderId: {orderId}, status: {status}, filled: {filled}, remaining: {remaining}, avgFillPrice: {avgFillPrice}, permId: {permId}, parentId: {parentId}, lastFillPrice: {lastFillPrice}, clientId: {clientId}, whyHeld: {whyHeld}, mktCapPrice: {mktCapPrice}")
        # update order information dictionary
        self.order_information_stream_count_int += 1
        self.order_information_dict.update(
            {
                str(self.order_information_stream_count_int) : {
                    'order_id_int': int(orderId),
                    'order_status_str': str(status),
                    'filled_int': int(filled),
                    'average_fill_price_flt': float(avgFillPrice),
                    'last_fill_price_flt': float(lastFillPrice)
                }
            }
        )

    # def execDetails(self, reqId: int, contract: Contract, execution: Execution):
    #     # NOTE: This was created for future usage purposes.
    #     # print details
    #     print(f"ExecDetails > reqId: {reqId}, contract: {contract}, execution: {execution}")

    def stop(self):
        """
        Terminate the IB API connection cleanly.
        """
        self.done = True
        self.disconnect()


def w1_if_placeOrder(
        ticker_str,
        action_type_str,
        quantity_int,
        order_type_str = 'MKT',
        limit_order_price_flt = 0.0,
        tif_str = 'DAY',
        simulated_on = True
):
    """
    Place an IBKR stock order using the Interactive Brokers API wrapper.

    This helper creates an OrderSender instance, connects to the appropriate
    TWS/Gateway port depending on simulation mode, submits the order, waits for
    processing, and then disconnects.

    Parameters:
        ticker_str (str): Stock ticker symbol.
        action_type_str (str): Order side, e.g. 'BUY' or 'SELL'.
        quantity_int (int): Number of shares to trade.
        order_type_str (str): Order type, such as 'MKT' or 'LMT'.
        limit_order_price_flt (float): Limit price for limit orders.
        tif_str (str): Time-in-force string, e.g. 'DAY', 'GTC', or 'IOC'.
        simulated_on (bool): If True, connect to the IBKR paper trading/simulated port.

    Returns:
        dict: Order status details collected during the order lifecycle.
    """
    # construct the application
    application_obj = OrderSender(
        ticker_str = ticker_str,
        action_type_str = action_type_str,
        quantity_int = quantity_int,
        order_type_str = order_type_str,
        limit_order_price_flt = limit_order_price_flt,
        tif_str = tif_str
    )
    if not simulated_on:
        application_obj.connect(
            host = "127.0.0.1",
            port = 7496,
            clientId = IBKR_ORDER_CLIENT_ID
        )
    else:
        application_obj.connect(
            host = "127.0.0.1",
            port = 7497,
            clientId = IBKR_ORDER_CLIENT_ID
        )

    # start the socket in a thread
    threading.Thread(target = application_obj.run).start()

    # allow time for incoming stream and also wait to prevent rejection from interface
    time.sleep(IBKR_WAIT_TIME_TRADE)

    # terminate connection with TWS
    application_obj.disconnect()

    return application_obj.order_information_dict


if __name__ == "__main__":
    # NOTE: The argument 'primary_exchange_str' is not really required. This is an issue with the current version of IB API.
    # NOTE: Line 67 of .venv/client_utils.py in lib/python-3.12/site-packages/ibapi/client_utils.py was commented.
    print(
        w1_if_placeOrder(
            ticker_str = 'KO',
            action_type_str = 'BUY',
            quantity_int = 1,
            order_type_str = 'LMT',
            limit_order_price_flt = 82.0,
            tif_str = 'DAY',
            simulated_on = True
        )
    )