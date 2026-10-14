# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://interactivebrokers.github.io/tws-api/historical_bars.html
# [2] Inspired by chat model Gemini 3.1 Pro Extended
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import os
import pandas as pd
import threading
import time

from concurrent.futures import ThreadPoolExecutor
from ibapi.client import *
from ibapi.wrapper import *

# import custom configs and utils
from config import (
    IBKR_HISTORICAL_DATA_CLIENT_ID,
    IBKR_WAIT_TIME_DISPATCH_DELAY,
    IBKR_WAIT_TIME_HIST_DATA_DOWN,
    ROOT_PATH,
    WAIT_TIME_TEN,
    WAIT_TIME_FIFTEEN
)
from utils.w2_compareFileAgeToThreshold import w2_compareFileAgeToThreshold
from utils.w2_constructIBKREndDateTimeStr import w2_constructIBKREndDateTimeStr
from utils.w2_performDataFrameOps import (
    w2_concatenateDataFramesInRows,
    w2_customConvertDateToDatetime,
    w2_dropRowsWithNANResetIndex,
    w2_generateDataFrame,
    w2_readCSVToDataFrame,
    w2_writeDataFrameToCSV
)

# define global pacing controls
rate_limiter_lock = threading.Lock()
last_request_time = 0


class HistoricalDataGetter(EClient, EWrapper):
    def __init__(self, ticker_str, data_path_str):
        # initialize
        EClient.__init__(self, self)
        self.orderId = 0
        self.ticker_str = ticker_str
        self.data_path_str = data_path_str
        self.data_df = w2_generateDataFrame(data = {})

    def error(
        self,
        reqId: TickerId,
        errorTime: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson = '',
    ):
        # print details
        # print(f'reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}')
        pass
    
    def nextValidId(self, orderId):
        # receive next valid orderId
        self.orderId = orderId

    def nextId(self):
        # increment orderId and return
        self.orderId += 1
        return self.orderId

    def historicalData(self, reqId, bar):
        # gather data in a dictionary and concatenate into one dataframe
        data_dict = {
            "date": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
            }
        self.data_df = w2_concatenateDataFramesInRows(
            df1 = self.data_df,
            df2 = w2_generateDataFrame(data = data_dict)
            )
    
    def historicalDataEnd(self, reqId, start, end):
        # convert 'date' column to standard datetime format
        self.data_df = w2_customConvertDateToDatetime(
            w2_dropRowsWithNANResetIndex(
                self.data_df
            )
        )
        # save historical data
        w2_writeDataFrameToCSV(
            df = self.data_df,
            file_path = ROOT_PATH + self.data_path_str + self.ticker_str + '.csv'
            )
        # stop receiving historical data
        self.cancelHistoricalData(reqId)


def w1_if_getHistoricalData_D(
        ticker_str,
        data_path_str = 'data/daily/',
        duration_str = '5 Y',
        bar_size_str = '1 day',
        in_loop_on = False,
        extended_delay_on = False,
        no_stale_on = False,
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
    if os.path.exists(
        os.path.join(
            ROOT_PATH, data_path_str, f'{ticker_str}.csv'
        )
    ) and w2_compareFileAgeToThreshold(
        file_path_str = os.path.join(
            ROOT_PATH, data_path_str, f'{ticker_str}.csv'
        ),
        threshold_type_str = 'day',
        threshold_value_int = 0,
        no_stale_on = no_stale_on
    ):
        return w2_customConvertDateToDatetime(
            w2_dropRowsWithNANResetIndex(
                w2_readCSVToDataFrame(
                    file_path = os.path.join(
                        ROOT_PATH, data_path_str, f'{ticker_str}.csv'
                    )
                )
            )
        )

    else:
        # construct the application
        application_obj = HistoricalDataGetter(
            ticker_str = ticker_str,
            data_path_str = data_path_str
        )
        if not simulated_on:
            application_obj.connect(
                host = "127.0.0.1",
                port = 7496,
                clientId = IBKR_HISTORICAL_DATA_CLIENT_ID
            )
        else:
            application_obj.connect(
                host = "127.0.0.1",
                port = 7497,
                clientId = IBKR_HISTORICAL_DATA_CLIENT_ID
            )

        # start the socket in a thread
        threading.Thread(target = application_obj.run).start()

        # construct contract
        contract_obj = Contract()
        contract_obj.symbol = ticker_str
        contract_obj.secType = 'STK'
        contract_obj.currency = 'USD'
        contract_obj.exchange = 'SMART'

        # request contract's historical data
        application_obj.reqHistoricalData(
            reqId = application_obj.nextId(),
            contract = contract_obj,
            endDateTime = w2_constructIBKREndDateTimeStr(),
            durationStr = duration_str,
            barSizeSetting = bar_size_str,
            whatToShow = "TRADES",
            useRTH = 1,
            formatDate = 1,
            keepUpToDate = False,
            chartOptions = []
            )

        # allow time for incoming data
        # NOTE: It seems at least 2 seconds are needed for daily data.
        # NOTE: If in loop, its best to wait more to prevent rejection from interface.
        if in_loop_on:
            if extended_delay_on:
                time.sleep(WAIT_TIME_FIFTEEN)
            else:
                time.sleep(WAIT_TIME_TEN)
        else:
            time.sleep(IBKR_WAIT_TIME_HIST_DATA_DOWN)

        # terminate connection with TWS
        application_obj.disconnect()

        return application_obj.data_df


def w1_if_getHistoricalData_H(
        ticker_str,
        data_path_str = 'data/hourly/',
        duration_str = '1 Y',
        bar_size_str = '1 hour',
        in_loop_on = False,
        extended_delay_on = False,
        no_stale_on = False,
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
    if os.path.exists(
        os.path.join(
            ROOT_PATH, data_path_str, f'{ticker_str}.csv'
        )
    ) and w2_compareFileAgeToThreshold(
        file_path_str = os.path.join(
            ROOT_PATH, data_path_str, f'{ticker_str}.csv'
        ),
        threshold_type_str = 'hour',
        threshold_value_int = 1,
        no_stale_on = no_stale_on
    ):
        return w2_customConvertDateToDatetime(
            w2_dropRowsWithNANResetIndex(
                w2_readCSVToDataFrame(
                    file_path = os.path.join(
                        ROOT_PATH, data_path_str, f'{ticker_str}.csv'
                    )
                )
            )
        )
    
    else:
        # construct the application
        application_obj = HistoricalDataGetter(
            ticker_str = ticker_str,
            data_path_str = data_path_str
        )
        if not simulated_on:
            application_obj.connect(
                host = "127.0.0.1",
                port = 7496,
                clientId = IBKR_HISTORICAL_DATA_CLIENT_ID + 10
            )
        else:
            application_obj.connect(
                host = "127.0.0.1",
                port = 7497,
                clientId = IBKR_HISTORICAL_DATA_CLIENT_ID + 10
            )

        # start the socket in a thread
        threading.Thread(target = application_obj.run).start()

        # construct contract
        contract_obj = Contract()
        contract_obj.symbol = ticker_str
        contract_obj.secType = 'STK'
        contract_obj.currency = 'USD'
        contract_obj.exchange = 'SMART'

        # request contract's historical data
        # NOTE: '2 Y' durationStr didn't work when attempted.
        application_obj.reqHistoricalData(
            reqId = application_obj.nextId(),
            contract = contract_obj,
            endDateTime = w2_constructIBKREndDateTimeStr(),
            durationStr = duration_str,
            barSizeSetting = bar_size_str,
            whatToShow = "TRADES",
            useRTH = 1,
            formatDate = 1,
            keepUpToDate = False,
            chartOptions = []
            )

        # allow time for incoming data
        # NOTE: It seems at least 2 seconds are needed for daily data.
        # NOTE: If in loop, its best to wait more to prevent rejection from interface.
        if in_loop_on:
            if extended_delay_on:
                time.sleep(WAIT_TIME_FIFTEEN)
            else:
                time.sleep(WAIT_TIME_TEN)
        else:
            time.sleep(IBKR_WAIT_TIME_HIST_DATA_DOWN)

        # terminate connection with TWS
        application_obj.disconnect()

        return application_obj.data_df


def w1_if_getHistoricalData_M(
        ticker_str,
        data_path_str = 'data/minutely/',
        duration_str = '1 W',
        bar_size_str = '1 min',
        in_loop_on = False,
        extended_delay_on = False,
        no_stale_on = False,
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
    if os.path.exists(
        os.path.join(
            ROOT_PATH, data_path_str, f'{ticker_str}.csv'
        )
    ) and w2_compareFileAgeToThreshold(
        file_path_str = os.path.join(
            ROOT_PATH, data_path_str, f'{ticker_str}.csv'
        ),
        threshold_type_str = 'minute',
        threshold_value_int = 1,
        no_stale_on = no_stale_on
    ):
        return w2_customConvertDateToDatetime(
            w2_dropRowsWithNANResetIndex(
                w2_readCSVToDataFrame(
                    file_path = os.path.join(
                        ROOT_PATH, data_path_str, f'{ticker_str}.csv'
                    )
                )
            )
        )

    else:
        # construct the application
        application_obj = HistoricalDataGetter(
            ticker_str = ticker_str,
            data_path_str = data_path_str
        )
        if not simulated_on:
            application_obj.connect(
                host = "127.0.0.1",
                port = 7496,
                clientId = IBKR_HISTORICAL_DATA_CLIENT_ID + 20
            )
        else:
            application_obj.connect(
                host = "127.0.0.1",
                port = 7497,
                clientId = IBKR_HISTORICAL_DATA_CLIENT_ID + 20
            )

        # start the socket in a thread
        threading.Thread(target = application_obj.run).start()

        # construct contract
        contract_obj = Contract()
        contract_obj.symbol = ticker_str
        contract_obj.secType = 'STK'
        contract_obj.currency = 'USD'
        contract_obj.exchange = 'SMART'

        # request contract's historical data
        # NOTE: '2 W' durationStr didn't work when attempted.
        application_obj.reqHistoricalData(
            reqId = application_obj.nextId(),
            contract = contract_obj,
            endDateTime = w2_constructIBKREndDateTimeStr(),
            durationStr = duration_str,
            barSizeSetting = bar_size_str,
            whatToShow = "TRADES",
            useRTH = 1,
            formatDate = 1,
            keepUpToDate = False,
            chartOptions = []
            )

        # allow time for incoming data
        # NOTE: It seems at least 2 seconds are needed for daily data.
        # NOTE: If in loop, its best to wait more to prevent rejection from interface.
        if in_loop_on:
            if extended_delay_on:
                time.sleep(WAIT_TIME_FIFTEEN)
            else:
                time.sleep(WAIT_TIME_TEN)
        else:
            time.sleep(IBKR_WAIT_TIME_HIST_DATA_DOWN)

        # terminate connection with TWS
        application_obj.disconnect()

        return application_obj.data_df
    

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


class HistoricalDataGetterInThreads(EWrapper, EClient):
    def __init__(self):
        # initialize
        EClient.__init__(self, self)
        self.data_df = w2_generateDataFrame(data = {})
        self.data_dict = {}
        self.event_dict = {}
        self.next_valid_id = None
        # initialize tracker when connection is fully established
        self.connected_event = threading.Event()

    def nextValidId(self, orderId: int):
        """This is fired when the connection is fully established."""
        super().nextValidId(orderId)
        self.next_valid_id = orderId
        self.connected_event.set()

    def historicalData(self, reqId, bar):
        """This is fired for every bar received from a historical data request."""
        if reqId not in self.data_dict:
            self.data_dict[reqId] = []
            
        self.data_dict[reqId].append(
            {
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume
            }
        )

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """This is fired when a specific historical data request finishes."""
        if reqId in self.event_dict:
            self.event_dict[reqId].set()

    def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson = ""):
        """This is fired when an error or informational message is received."""
        # NOTE: Codes >= 2000 are generally informational (e.g., connection success, market data farm status).
        # NOTE: We can filter them out to keep the console clean. Error 162 is a pacing violation.
        if errorCode < 2000:
            # print(f"[ERROR] ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")
            pass


def run_loop(app):
    """This is background loop to process IBKR messages."""
    app.run()


def w1_if_getHistoricalDataInThreads(
        app,
        req_id_int,
        ticker_str,
        resolution_str,
        data_path_str
):
    """
    This is a task to fetch data for a single symbol. This was designed to run in a ThreadPool.
    """
    global last_request_time

    # define resolution mapping (duration and bar size)
    res_map = {
        "minutely": {"duration": "1 D", "bar": "1 min"},
        "hourly":   {"duration": "1 M", "bar": "1 hour"},
        "daily":    {"duration": "1 Y", "bar": "1 day"}
    }
    settings = res_map.get(resolution_str.lower())
    if not settings:
        raise ValueError("[ERROR] Resolution must be 'minutely', 'hourly', or 'daily'.")
    
    # build contract (assuming US stocks on SMART exchange for this example)
    contract = Contract()
    contract.symbol = ticker_str
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    # setup data structures for this specific request
    app.data_dict[req_id_int] = []
    app.event_dict[req_id_int] = threading.Event()

    # enforce pacing limits to avoid being rejected by IBKR
    with rate_limiter_lock:
        time_since_last = time.time() - last_request_time
        if time_since_last < IBKR_WAIT_TIME_DISPATCH_DELAY:
            time.sleep(IBKR_WAIT_TIME_DISPATCH_DELAY - time_since_last)
            
        # dispatch the request to IBKR
        app.reqHistoricalData(
            reqId = req_id_int,
            contract = contract,
            endDateTime = "",
            durationStr = settings["duration"],
            barSizeSetting = settings["bar"],
            whatToShow = "TRADES",              # can also be "MIDPOINT" or "BID_ASK" depending on needs
            useRTH = 1,                         # 1 = Regular Trading Hours Only, 0 = Include After-Hours
            formatDate = 1,                     # 1 = YYYYMMDD HH:MM:SS format
            keepUpToDate = False,               # must be False for historical data looping
            chartOptions = []
        )
        last_request_time = time.time()
        # print(f"[INFO] Requested {ticker_str} data at {resolution_str} (ReqId: {req_id_int})...")

    # block this specific thread until IBKR fires 'historicalDataEnd'
    app.event_dict[req_id_int].wait(timeout = 30.0) # 30 second safety timeout

    # format and return data
    if app.data_dict[req_id_int]:
        data_df = pd.DataFrame(app.data_dict[req_id_int])
        # convert 'date' column to standard datetime format
        data_df = w2_customConvertDateToDatetime(
            w2_dropRowsWithNANResetIndex(
                data_df
            )
        )
        # save historical data
        w2_writeDataFrameToCSV(
            df = data_df,
            file_path = ROOT_PATH + data_path_str + ticker_str + '.csv'
            )
        
        return ticker_str, data_df
    
    else:
        return ticker_str, pd.DataFrame()
    

def w1_if_getHistoricalDataInThreadsMain(
        ticker_str_list,
        data_path_str = 'data/daily/',
        resolution_str = 'daily',
        results_dict = {},
        no_stale_on = False,
        simulated_on = True
):
    """
    Function to call w1_getHistoricalDataInThreads

    NOTE: If called in threads, data is capped at 251 rows.
    """
    # determine threshold type string based on resolution
    if resolution_str == 'daily':
        threshold_type_str = 'day'
        threshold_value_int = 0
    elif resolution_str == 'hourly':
        threshold_type_str = 'hour'
        threshold_value_int = 1
    elif resolution_str == 'minutely':
        threshold_type_str = 'minute'
        threshold_value_int = 1
    else:
        print("[ERROR] Failed to accept resolution string, it's either 'daily', 'hourly', or 'minutely'...")
        return
    
    # initialize app
    app = HistoricalDataGetterInThreads()

    # connect to IBKR
    if not simulated_on:
        app.connect(
            host = "127.0.0.1", 
            port = 7496, 
            clientId = 100
        )
    else:
        app.connect(
            host = "127.0.0.1", 
            port = 7497, 
            clientId = 100
        )

    # start the socket communication in a background daemon thread
    api_thread = threading.Thread(
        target = run_loop, 
        args = (app,), 
        daemon = True
    )
    api_thread.start()

    # wait for the API connection to complete
    app.connected_event.wait(timeout = 5.0)
    if not app.connected_event.is_set():
        print("[ERROR] Failed to connect to TWS/IB Gateway, check if it's running and API settings are correct...")
        return
    
    # start threads to handle concurrent requests
    with ThreadPoolExecutor(max_workers = os.cpu_count()) as executor:
        # map futures to our fetch function
        futures_list = []
        for i, ticker_str in enumerate(ticker_str_list):
            if os.path.exists(
                os.path.join(
                    ROOT_PATH, data_path_str, f'{ticker_str}.csv'
                )
            ) and w2_compareFileAgeToThreshold(
                file_path_str = os.path.join(
                    ROOT_PATH, data_path_str, f'{ticker_str}.csv'
                ),
                threshold_type_str = threshold_type_str,
                threshold_value_int = threshold_value_int,
                no_stale_on = no_stale_on
            ):
                results_dict[ticker_str] = w2_customConvertDateToDatetime(
                    w2_dropRowsWithNANResetIndex(
                        w2_readCSVToDataFrame(
                            file_path = os.path.join(
                                ROOT_PATH, data_path_str, f'{ticker_str}.csv'
                            )
                        )
                    )
                )
            else:
                req_id_int = app.next_valid_id + i # assign unique reqId
                future = executor.submit(
                    w1_if_getHistoricalDataInThreads, 
                    app, 
                    req_id_int, 
                    ticker_str, 
                    resolution_str,
                    data_path_str
                )
                futures_list.append(future)

        # retrieve results as they complete
        for future in futures_list:
            try:
                ticker_str, data_df = future.result()
                if not data_df.empty:
                    results_dict[ticker_str] = data_df
                    # print(f"[INFO] Successfully retrieved {ticker_str} data of length {len(data_df)} rows...")
                else:
                    # print(f"[WARN] No data returned for {ticker_str}...")
                    pass
            except Exception as e:
                print(f"[ERROR] Ran into exception during request: {e}")

        # disconnect when finished
        app.disconnect()

    return results_dict


if __name__ == '__main__':
    # define flag for type of call
    in_thread_on = False

    if not in_thread_on:
        # define flag
        with_drawdown_on = True

        # specify ticker symbol
        ticker_str = 'IAUM'

        if not with_drawdown_on:
            from utils.w2_plot import w2_plotInOneScale
            # get daily data
            temp_df = w2_dropRowsWithNANResetIndex(
                w1_if_getHistoricalData_D(
                    ticker_str = ticker_str,
                    in_loop_on = False,
                    simulated_on = True
                )
            )
            # plot data
            w2_plotInOneScale(
                x_data_df = temp_df['date'],
                x_axis_label_str = 'Time',
                y_data_df_list = [temp_df['open'], temp_df['high'], temp_df['low'], temp_df['close']],
                y_data_label_str_list = ['Open', 'High', 'Low', 'Close'],
                y_axis_label_str = 'Price (USD)',
                plot_title_str = f'Daily Price Data for {ticker_str}',
                recent_data_chunk_int = 1000,
                save_on = True,
                save_file_name_str = f'DailyPriceData_{ticker_str}',
                save_path_str = ROOT_PATH + 'reports/plots/',
                show_on = True
            )
        else:
            from utils.w2_calculateStats import w2_calculateMaximumDrawDown, w2_calculatePeaksAndTroughs
            from utils.w2_plot import w2_plotInTwoScales

            # get daily data
            temp_df = w2_dropRowsWithNANResetIndex(
                w1_if_getHistoricalData_D(
                    ticker_str = ticker_str,
                    in_loop_on = False,
                    simulated_on = True
                )
            )

            # calculate peaks and troughs
            temp_df['peaks'], temp_df['troughs'] = w2_calculatePeaksAndTroughs(
                closing_price_df = temp_df['close'],
                window_int = 64
            )
            # plot data
            w2_plotInTwoScales(
                x_data_df = temp_df['date'],
                x_axis_label_str = 'Time',
                y_data_df_list = [temp_df['close'], temp_df['peaks']],
                y_axes_label_str_list = ['Price (USD)', 'Peaks (USD)'],
                y_axes_limits_bool_list = [True, True],
                y_axes_limits_list = [[min(temp_df['close']), max(temp_df['close'])], [min(temp_df['close']), max(temp_df['close'])]],
                datetime_on = True,
                plot_title_str = f'Price Data with Rolling-Window Peaks for {ticker_str}',
                recent_data_chunk_int = None,
                save_on = True,
                save_file_name_str = f'PriceDataWithPeaks_{ticker_str}',
                save_path_str = ROOT_PATH + 'reports/plots/',
                show_on = True
            )
            # plot data
            w2_plotInTwoScales(
                x_data_df = temp_df['date'],
                x_axis_label_str = 'Time',
                y_data_df_list = [temp_df['close'], temp_df['troughs']],
                y_axes_label_str_list = ['Price (USD)', 'Troughs (USD)'],
                y_axes_limits_bool_list = [True, True],
                y_axes_limits_list = [[min(temp_df['close']), max(temp_df['close'])], [min(temp_df['close']), max(temp_df['close'])]],
                datetime_on = True,
                plot_title_str = f'Price Data with Rolling-Window Troughs for {ticker_str}',
                recent_data_chunk_int = None,
                save_on = True,
                save_file_name_str = f'PriceDataWithTroughs_{ticker_str}',
                save_path_str = ROOT_PATH + 'reports/plots/',
                show_on = True
            )

            # calculate maximum drawdown
            temp_df['drawdown'] = w2_calculateMaximumDrawDown(
                closing_price_df = temp_df['close'],
                window_int = 64
            )
            # plot data
            w2_plotInTwoScales(
                x_data_df = temp_df['date'],
                x_axis_label_str = 'Time',
                y_data_df_list = [temp_df['close'], temp_df['drawdown']],
                y_axes_label_str_list = ['Price (USD)', 'Draw-Down (%)'],
                y_axes_limits_bool_list = [False, True],
                y_axes_limits_list = [[], [-1.5, 1.5]],
                datetime_on = True,
                plot_title_str = f'Price Data with Maximum Draw-Down for {ticker_str}',
                recent_data_chunk_int = None,
                save_on = True,
                save_file_name_str = f'PriceDataWithDrawDown_{ticker_str}',
                save_path_str = ROOT_PATH + 'reports/plots/',
                show_on = True
            )
    
    else:
        ticker_str_list = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "MU", "LLY", "F", "PLUG"]
        resolution_str = "daily"

        data_dict = w1_if_getHistoricalDataInThreadsMain(
            ticker_str_list = ticker_str_list,
            resolution_str = resolution_str,
            simulated_on = True
        )

        print(data_dict)