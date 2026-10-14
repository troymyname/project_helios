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

from ibapi.client import *
from ibapi.tag_value import *
from ibapi.wrapper import *

# import custom configs and utils
from config import IBKR_SCAN_DATA_CLIENT_ID, ROOT_PATH
from utils.w2_performDictionaryOps import w2_appendToDictionary, w2_writeDictionaryToJSON


class MarketScannerDataGetter(EClient, EWrapper):
    def __init__(self, data_path_str):
        EClient.__init__(self, self)
        self.orderId = 0
        self.data_path_str = data_path_str

    def nextValidId(self, orderId: int):
        # receive next valid orderId
        self.orderId = orderId
        # request an xml string that describes all possible scanner queries
        self.reqScannerParameters()

    def scannerParameters(self, xml: str):
        # write scanner parameters for review
        with open(self.data_path_str + 'scan.xml', 'w') as file_obj:
            file_obj.write(xml)

    def scannerDataEnd(self, reqId: int):
        # stop receiving scanner data
        self.cancelScannerSubscription(reqId)
        self.disconnect()


class CustomMarketScannerDataGetter(EClient, EWrapper):
    def __init__(self, data_path_str):
        EClient.__init__(self, self)
        self.orderId = 0
        self.data_dict = {}
        self.data_path_str = data_path_str

    def nextValidId(self, orderId: int):
        # receive next valid orderId
        self.orderId = orderId

        # construct subscription object
        subscription_obj = ScannerSubscription()
        subscription_obj.instrument = 'STK'
        subscription_obj.locationCode = 'STK.US.MAJOR' # NOTE: This provides data from AMEX, NASDAQ, NYSE, and more.
        subscription_obj.scanCode = 'TOP_OPEN_PERC_GAIN'

        # construct scanner subscription request based on preferences
        scan_options_list = []
        filter_options_list = [
            TagValue(tag = 'priceAbove', value = '1'),
        ]
        self.reqScannerSubscription(
            reqId = orderId,
            subscription = subscription_obj,
            scannerSubscriptionOptions = scan_options_list,
            scannerSubscriptionFilterOptions = filter_options_list
        )

    def scannerData(
        self,
        reqId: int,
        rank: int,
        contractDetails: ContractDetails,
        distance: str,
        benchmark: str,
        projection: str,
        legsStr: str,
    ):
        # collect data
        self.data_dict = w2_appendToDictionary(
            data_dict = self.data_dict,
            new_data_dict = {
                'reqId': reqId,
                'rank': rank,
                'contractDetails': contractDetails,
                'distance': distance,
                'benchmark': benchmark,
                'projection': projection,
                'legsStr': legsStr
            }
        )

    def scannerDataEnd(self, reqId: int):
        # stop receiving scanner data
        self.cancelScannerSubscription(reqId)
        self.disconnect()
        # save all data to preferred location
        w2_writeDictionaryToJSON(
            data_dict = self.data_dict,
            save_path_str = self.data_path_str + 'custom_scan.json'
        )


def w1_if_getMarketScannerData(data_path_str = ROOT_PATH + 'data/scans/'):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # construct and run the application
    app = MarketScannerDataGetter(data_path_str = data_path_str)
    app.connect(
        host = '127.0.0.1',
        port = 7496,
        clientId = IBKR_SCAN_DATA_CLIENT_ID
    )
    app.run()


def w1_if_getCustomMarketScannerData(data_path_str = ROOT_PATH + 'data/scans/'):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # construct and run the application
    app = CustomMarketScannerDataGetter(data_path_str = data_path_str)
    app.connect(
        host = '127.0.0.1',
        port = 7496,
        clientId = IBKR_SCAN_DATA_CLIENT_ID
    )
    app.run()


if __name__ == '__main__':
    # w1_if_getMarketScannerData()
    w1_if_getCustomMarketScannerData()