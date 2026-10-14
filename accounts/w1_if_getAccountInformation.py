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

from ibapi.client import EClient
from ibapi.common import TickerId
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from threading import Timer

# import custom configs and utils
from config import (
    IBKR_ACCOUNT_INFORMATION_CLIENT_ID,
    TRADE_LIVE_STARTING_CASH,
    TRADE_SIMULATION_STARTING_CASH,
    WAIT_TIME_ONE
)


class AccountInformationGetter(EClient, EWrapper):
    """
    Interactive Brokers account information retrieval client.

    This class combines the IB API client and wrapper interfaces to request
    account updates, capture portfolio information, and store account-level
    metrics for later retrieval.
    """
    def __init__(self, simulated_on = True):
        """
        Initialize the account information getter.

        Parameters:
            simulated_on (bool): If True, the account value calculations use
                the simulation starting cash baseline.
        """
        # initialize
        EClient.__init__(self, self)
        self.account_name_str = ''
        self.buying_power_flt = 0.0
        self.stock_market_value_flt = 0.0
        self.unrealized_pnl_flt = 0.0
        self.portfolio_value_flt = 0.0
        self.unrealized_overall_pnl_perc_flt = 0.0
        self.account_information_dict = {}
        self.portfolio_information_dict = {}
        self.simulated_on = simulated_on
        self.done = False

    def error(
        self,
        reqId: TickerId,
        errorTime: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson = '',
    ):
        """
        Handle error messages emitted by the IB API.

        Parameters:
            reqId (TickerId): Request identifier.
            errorTime (int): Error timestamp.
            errorCode (int): IB-specific error code.
            errorString (str): Error message text.
            advancedOrderRejectJson: Optional advanced rejection details.
        """
        # print details
        # print(f'reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}')
        pass

    def nextValidId(self, orderId):
        """
        Callback invoked when the next valid IB order ID is received.

        Parameters:
            orderId (int): The next available order identifier.
        """
        # execute start method
        self.start()

    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float, averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        """
        Update the internal portfolio state based on IB portfolio callbacks.

        Parameters:
            contract (Contract): Contract information for the position.
            position (float): Position size.
            marketPrice (float): Current market price.
            marketValue (float): Total market value.
            averageCost (float): Average cost of the position.
            unrealizedPNL (float): Unrealized profit/loss for the position.
            realizedPNL (float): Realized profit/loss for the position.
            accountName (str): The account identifier.
        """
        # print details
        # print("UpdatePortfolio > Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:", contract.exchange, "Position:", position, "MarketPrice:", marketPrice, "MarketValue:", marketValue, "AverageCost:", averageCost, "UnrealizedPNL:", unrealizedPNL, "RealizedPNL:", realizedPNL, "AccountName:", accountName)
        # store information in a dictionary
        self.portfolio_information_dict.update(
            {
                str(contract.symbol): {
                    'quantity_int': int(position),
                    'market_price_flt': round(float(marketPrice), 2),
                    'market_value_flt': round(float(marketValue), 2),
                    'average_cost_flt': round(float(averageCost), 2),
                    'unrealized_pnl_flt': round(float(unrealizedPNL), 2),
                    'realized_pnl_flt': round(float(realizedPNL), 2)
                }
            }
        )

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        """
        Update account-level values received from IB account callbacks.

        Parameters:
            key (str): Account value key.
            val (str): Account value string.
            currency (str): Currency code for the value.
            accountName (str): The account identifier.
        """
        # print details
        # print("UpdateAccountValue > Key:", key, "Value:", val, "Currency:", currency, "AccountName:", accountName)
        # derive account code
        if self.account_name_str == '' and key == 'AccountCode':
            self.account_name_str = str(val)
        # derive buying power (or total cash balance)
        if self.buying_power_flt == 0.0 and key == 'TotalCashBalance' and currency == 'USD':
            self.buying_power_flt = float(val)
        # derive stock market value
        if self.stock_market_value_flt == 0.0 and key == 'StockMarketValue' and currency == 'USD':
            self.stock_market_value_flt = float(val)
        # derive unrealized profit or loss
        if self.unrealized_pnl_flt == 0.0 and key == 'UnrealizedPnL' and currency == 'USD':
            self.unrealized_pnl_flt = float(val)

        # calculate portfolio value
        self.portfolio_value_flt = self.buying_power_flt + self.stock_market_value_flt
        # calculate unrealized overall profit or loss
        if self.simulated_on:
            self.unrealized_overall_pnl_perc_flt = ((self.portfolio_value_flt - TRADE_SIMULATION_STARTING_CASH)/TRADE_SIMULATION_STARTING_CASH)*100
        else:
            self.unrealized_overall_pnl_perc_flt = ((self.portfolio_value_flt - TRADE_LIVE_STARTING_CASH) / TRADE_LIVE_STARTING_CASH) * 100

        # store information in a dictionary
        self.account_information_dict = {
            'account_name_str': self.account_name_str,
            'buying_power_flt': round(self.buying_power_flt, 2),
            'stock_market_value_flt': round(self.stock_market_value_flt, 2),
            'portfolio_value_flt': round(self.portfolio_value_flt, 2),
            'unrealized_pnl_flt': round(self.unrealized_pnl_flt, 2),
            'unrealized_overall_pnl_perc_flt': round(self.unrealized_overall_pnl_perc_flt, 2)
        }

    # def updateAccountTime(self, timeStamp: str):
    #     # NOTE: This was created for future usage purposes.
    #     # print details
    #     print("UpdateAccountTime > Time:", timeStamp)
    #     pass

    # def accountDownloadEnd(self, accountName):
    #     # NOTE: This was created for future usage purposes.
    #     # print details
    #     print("AccountDownloadEnd > Account:", accountName)
    #     pass

    def start(self):
        """
        Subscribe to IB account updates and begin receiving account information.
        """
        # NOTE: Account number can be emitted when using reqAccountUpdates with single account structure.
        self.reqAccountUpdates(subscribe = True, acctCode = '')

    def stop(self):
        """
        Unsubscribe from account updates and disconnect from the IB API.
        """
        self.reqAccountUpdates(subscribe = False, acctCode = '')
        self.done = True
        self.disconnect()


def w1_if_getAccountInformation(simulated_on = True):
    """
    Retrieve account and portfolio information from Interactive Brokers.

    This helper connects to either the live or simulated IBKR gateway depending
    on the `simulated_on` flag, requests account updates, waits for a short
    polling interval, and then returns the collected account and portfolio data.

    Parameters:
        simulated_on (bool): If True, connect to the simulated IBKR port.

    Returns:
        tuple: A tuple containing account information and portfolio information dictionaries.
    """
    # construct the application
    application_obj = AccountInformationGetter(
        simulated_on = simulated_on
    )
    if not simulated_on:
        application_obj.connect(
            host = "127.0.0.1",
            port = 7496,
            clientId = IBKR_ACCOUNT_INFORMATION_CLIENT_ID
        )
    else:
        application_obj.connect(
            host = "127.0.0.1",
            port = 7497,
            clientId = IBKR_ACCOUNT_INFORMATION_CLIENT_ID
        )
    # run the application
    Timer(
        interval = WAIT_TIME_ONE,
        function = application_obj.stop
    ).start()
    application_obj.run()

    return application_obj.account_information_dict, application_obj.portfolio_information_dict


if __name__ == "__main__":
    import json
    print(
        json.dumps(
            w1_if_getAccountInformation(), 
            indent = 4
        )
    )