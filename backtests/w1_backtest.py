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

# import custom configs and utils
from backtests.w2_Strategy_EMA_KMA_MACD_RSI import Strategy_EMA_KMA_MACD_RSI
from config import ROOT_PATH, IBKR_COMMISSION
from data.w1_if_getHistoricalData import w1_if_getHistoricalData_M
from utils.w2_performDataFrameOps import w2_setColumnAsIndex


def w1_downloadData(symbol_str, simulated_on = True):
    """
    Download intraday historical data for a ticker and prepare it for backtesting.

    Parameters:
        symbol_str (str): Ticker symbol to download.
        simulated_on (bool): Whether to use simulated data sources.

    Returns:
        pd.DataFrame | None: Time series data indexed by date, or None if download failed.
    """
    # initialize data container
    timeseries_df = None

    # download data
    try:
        timeseries_df = w2_setColumnAsIndex(
            df = w1_if_getHistoricalData_M(
                ticker_str = symbol_str,
                in_loop_on = False,
                simulated_on = simulated_on
            ),
            column_to_index_name_str = 'date',
            drop_column = True
        )
    except KeyError:
        pass

    return timeseries_df


def w1_backtest(
        ticker_str,
        cash_flt = 1000000.0,
        stake_int = 100,
        commission_flt = 0.0, # NOTE: This is in percentage. IBKR_COMMISSION is used instead.
        verbose_on = True,
        candle_sticks_on = True,
        show_on = True,
        save_on = True,
        save_path_str = 'reports/plots/',
        simulated_on = True,
):
    """
    Execute a Backtrader backtest using the EMA/KMA/MACD/RSI strategy.

    Parameters:
        ticker_str (str): Ticker symbol to backtest.
        cash_flt (float): Starting cash for the broker.
        stake_int (int): Fixed stake size for each trade.
        commission_flt (float): Commission rate applied to each trade.
        verbose_on (bool): If True, print portfolio summary information.
        candle_sticks_on (bool): If True, render candlestick charts; otherwise plot line charts.
        show_on (bool): If True, display the resulting plot interactively.
        save_on (bool): If True, save the generated plot to disk.
        save_path_str (str): Path where the plot image should be saved.
        simulated_on (bool): Whether to use simulated data for the backtest.

    Returns:
        None: The function runs the backtest and may save or display charts.
    """
    # create a cerebro object
    cerebro_obj = bt.Cerebro()

    # add a strategy
    cerebro_obj.addstrategy(
        strategy = Strategy_EMA_KMA_MACD_RSI,
        verbose_on = verbose_on
    )

    # construct data object
    data_df = w1_downloadData(
        symbol_str = ticker_str,
        simulated_on = simulated_on
    )

    # add a data feed
    # reference: https://www.backtrader.com/docu/pandas-datafeed/pandas-datafeed/
    data_obj = bt.feeds.PandasData(
        dataname = data_df,
        name = ticker_str,
        timeframe = bt.TimeFrame.Minutes
    )
    cerebro_obj.adddata(
        data = data_obj,
        name = f'Backtest | {stake_int} of {ticker_str} | Strategy: MACD/Signal Cross + EWMA Conf. With KMA of Closing Price'
    )

    # set desired starting cash
    cerebro_obj.broker.setcash(cash = cash_flt)

    # add a fixed-size sizer according to the stake
    cerebro_obj.addsizer(
        sizercls = bt.sizers.FixedSize,
        stake = stake_int
    )

    # set commission
    # NOTE: This is in percentage. IBKR_COMMISSION is used instead. 
    cerebro_obj.broker.setcommission(commission = commission_flt) 

    # print out start portfolio value
    start_portfolio_value_flt = cerebro_obj.broker.getvalue()
    if verbose_on:
        print('INFO: Start Portfolio Value: %.2f' % start_portfolio_value_flt)

    # backtest with data
    cerebro_obj.run()

    # print out final portfolio value
    final_portfolio_value_flt = cerebro_obj.broker.getvalue()
    if verbose_on:
        print('INFO: Final Portfolio Value: %.2f' % final_portfolio_value_flt)
    
    # calculate realized profit/loss
    # NOTE: If final portfolio value is unchanged, commission is not charged.
    if final_portfolio_value_flt != start_portfolio_value_flt:
        realized_pnl_flt = round(((final_portfolio_value_flt - start_portfolio_value_flt)/stake_int) - 2*IBKR_COMMISSION, 2)
    else:
        realized_pnl_flt = round(((final_portfolio_value_flt - start_portfolio_value_flt)/stake_int), 2)

    # print summary
    print()
    print(f'Backtest Results: {ticker_str}')
    print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
    print(f'Start Time                  | {data_df.index[0]}')
    print(f'End Time                    | {data_df.index[-1]}')
    print(f'Commission Per Trade        | ${IBKR_COMMISSION}')
    if realized_pnl_flt >= 0.0:
        print(f'Returns Per Unit            | ${realized_pnl_flt}')
    else:
        print(f'Returns Per Unit            | -${abs(realized_pnl_flt)}')
    print('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
    print()

    # show and save plot
    if save_on:
        if candle_sticks_on:
            figure_obj = cerebro_obj.plot(
                iplot = False,
                width = 64,
                height = 32,
                style = 'candle'
            )[0][0]
            figure_obj.savefig(
                fname = ROOT_PATH + save_path_str + 'Backtest_' + ticker_str + '.jpg',
                transparent = False,
                dpi = 300,
            )
        else:
            figure_obj = cerebro_obj.plot(
                iplot = False,
                width = 64,
                height = 32,
                style = 'line'
            )[0][0]
            figure_obj.savefig(
                fname = ROOT_PATH + save_path_str + 'Backtest_' + ticker_str + '.jpg',
                transparent = False,
                dpi = 300
            )

    # show plot
    if show_on:
        if candle_sticks_on:
            cerebro_obj.plot(style = 'candle')

        else:
            cerebro_obj.plot(style = 'line')


if __name__ == '__main__':
    w1_backtest(
        ticker_str = 'TSLA',
        verbose_on = True,
        candle_sticks_on = False,
        save_on = True,
        show_on = False,
        simulated_on = True
    )
