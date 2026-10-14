# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://docs.bokeh.org/en/3.0.1/docs/examples/interaction/tools/hover_tooltip_formatting.html
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import numpy as np
import pandas as pd

from bokeh.core.serialization import SerializationError
from bokeh.layouts import gridplot
from bokeh.models import HoverTool, Label, Paragraph, Range1d
from bokeh.palettes import Spectral4 # Viridis4
from bokeh.plotting import figure, output_file, save
from math import pi

# import custom configs and utils
from config import ROOT_PATH
from data.w1_if_getFundamentals import w1_if_getFundamentals
from data.w1_if_getHistoricalData import w1_if_getHistoricalData_D, w1_if_getHistoricalData_M
from strategies.w2_appendEWMATracker import w2_appendEWMATracker
from strategies.w2_appendKFTracker import w2_appendKMATracker
from strategies.w2_appendMACDIndicator import w2_appendMACDIndicator
from strategies.w2_appendRSIIndicator import w2_appendRSIIndicator
from utils.w2_calculateStats import w2_calculatePeaksAndTroughs, w2_calculateMaximumDrawDown
from utils.w2_generateDateStringYYYYMMDD import w2_generateDateStringYYYYMMDD
from utils.w2_performDataFrameOps import w2_roundByDecimals


def w1_generateAnalysisReport(
        ticker_str,
        display_range_daily_int = 252,
        display_range_minutely_int = int(60*6.5),
        peaks_troughs_window_int = 64,
        drawdown_window_int = 64,
        plot_alpha_flt = 0.75,
        simulated_on = True
    ):
    """
    Generate a Bokeh-based analysis report for a given stock ticker.

    The function downloads daily and minutely historical data, computes technical
    indicators, derives market peaks/troughs and drawdown statistics, and builds
    a visual report layout using Bokeh.

    Parameters:
        ticker_str (str): Stock ticker symbol to analyze.
        display_range_daily_int (int): Number of daily bars to include in the report.
        display_range_minutely_int (int): Number of minutely bars to include in the report.
        peaks_troughs_window_int (int): Window size used to identify peaks and troughs.
        drawdown_window_int (int): Rolling window size used for maximum drawdown calculation.
        plot_alpha_flt (float): Alpha transparency value for plot glyphs.
        simulated_on (bool): Whether to use simulated historical data sources.

    Returns:
        None: The function produces a Bokeh report and saves or displays it as configured in the report code.
    """

    # initialize parameters
    document_width_int = 1600
    bar_width_int = 1e8*0.85

    # specify functionalities for plotting
    plot_function_str = 'pan, wheel_zoom, zoom_in, zoom_out, box_zoom, reset, save'

    # download daily data and append information
    historical_data_daily_df = w1_if_getHistoricalData_D(
        ticker_str = ticker_str,
        in_loop_on = True,
        simulated_on = simulated_on
    )
    plot_data_daily_df = historical_data_daily_df[-display_range_daily_int:]
    peaks_df, troughs_df = w2_calculatePeaksAndTroughs(
        closing_price_df = plot_data_daily_df['close'],
        window_int = peaks_troughs_window_int
    )
    drawdown_percentages_df = w2_calculateMaximumDrawDown(
        closing_price_df = plot_data_daily_df['close'],
        window_int = drawdown_window_int
    )

    # download minutely data and append information
    historical_data_minutely_df = w1_if_getHistoricalData_M(
        ticker_str = ticker_str,
        in_loop_on = True,
        simulated_on = simulated_on
    )
    plot_data_minutely_df = w2_roundByDecimals(
        df = w2_appendEWMATracker(
            timeseries_df = w2_appendKMATracker(
                timeseries_df = w2_appendMACDIndicator(
                    timeseries_df = w2_appendRSIIndicator(
                        timeseries_df = historical_data_minutely_df
                    )
                )
            )
        ),
        decimals_int = 2
    )[-display_range_minutely_int + 1:] # NOTE: A + 1 produces a nicer looking plot on Monday of the week.

    # download fundamentals data (exceptions handling is built in)
    fundamentals_variable_name_str_list = [
        'EarningsPerShareBasic',
        'AssetsCurrent',
        'LiabilitiesCurrent'
    ]
    fundamentals_data_dict = w1_if_getFundamentals(
        ticker_str = ticker_str,
        variable_name_str_list = fundamentals_variable_name_str_list
    )

    # ==== ==== construct main header
    if fundamentals_data_dict:
        ticker_descriptor_str = fundamentals_data_dict[ticker_str]['title']
    else:
        ticker_descriptor_str = '##'
    main_header_str = f'{ticker_str}, {ticker_descriptor_str}'
    main_header_obj = Paragraph(
        text = main_header_str,
        width = document_width_int,
        height_policy = 'auto',
        styles = {'font-size':'16pt', 'color': 'black', 'font-weight': 'bold', 'font-family': 'arial'}
    )

    report_date_str = f'Report Generated: {w2_generateDateStringYYYYMMDD()}'
    report_date_obj = Paragraph(
        text = report_date_str,
        width = document_width_int,
        height_policy = 'auto',
        styles = {'font-size':'8pt', 'color': 'black', 'font-family': 'arial'}
    )
    
    # ==== ==== construct sub heading #1
    sub_heading_one_str = f'Daily Price & Volume History for {display_range_daily_int} Days'
    sub_heading_1_obj = Paragraph(
        text = sub_heading_one_str,
        width = document_width_int,
        height_policy = 'auto',
        styles = {'font-size':'12pt', 'color': 'black', 'font-weight': 'bold', 'font-family': 'arial'}
    )
    # ==== ====

    # ==== ==== construct sub plot #1-1
    sub_plot_11_obj = figure(
        x_axis_type = 'datetime',
        tools = plot_function_str,
        width = document_width_int,
        title = 'Daily Price History with Candlesticks'
    )
    sub_plot_11_obj.grid.grid_line_alpha = 0.5
    # sub_plot_11_obj.xaxis.axis_label = 'Time'
    sub_plot_11_obj.yaxis.axis_label = 'Price'
    # map dataframe indices to date strings and use as label overrides
    # sub_plot_11_obj.xaxis.major_label_overrides = {i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(plot_data_daily_df['date'].values))}
    # sub_plot_11_obj.xaxis.major_label_orientation = pi/4
    sub_plot_11_obj.xaxis.visible = False

    # render price candlestick plot
    increase_stick_bool_list = plot_data_daily_df['close'] > plot_data_daily_df['open']
    decrease_stick_bool_list = plot_data_daily_df['close'] < plot_data_daily_df['open']
    sub_plot_11_obj.segment(
        x0 = plot_data_daily_df['date'],
        y0 = plot_data_daily_df['high'],
        x1 = plot_data_daily_df['date'],
        y1 = plot_data_daily_df['low'],
        color = 'black'
    )
    sub_plot_11_obj.vbar(
        x = plot_data_daily_df['date'][increase_stick_bool_list],
        width = bar_width_int,
        bottom = plot_data_daily_df['open'][increase_stick_bool_list],
        top = plot_data_daily_df['close'][increase_stick_bool_list],
        legend_label = 'Increase Day OHLC Prices', 
        fill_color = '#99D594', 
        line_color = 'black', 
        alpha = plot_alpha_flt
    )
    sub_plot_11_obj.vbar(
        x = plot_data_daily_df['date'][decrease_stick_bool_list],
        width = bar_width_int,
        bottom = plot_data_daily_df['open'][decrease_stick_bool_list],
        top = plot_data_daily_df['close'][decrease_stick_bool_list],
        legend_label = 'Decrease Day OHLC Prices', 
        fill_color = '#F2583E', 
        line_color = 'black', 
        alpha = plot_alpha_flt
    )

    # render price peaks and troughs
    sub_plot_11_obj.line(
        x = plot_data_daily_df['date'],
        y = peaks_df,
        legend_label = f'{peaks_troughs_window_int}-Day Close Price Peaks',
        color = Spectral4[0],
        alpha = plot_alpha_flt
    )
    sub_plot_11_obj.line(
        x = plot_data_daily_df['date'],
        y = troughs_df,
        legend_label = f'{peaks_troughs_window_int}-Day Close Price Troughs',
        color = Spectral4[1],
        alpha = plot_alpha_flt
    )

    # render additional information
    sub_plot_11_obj.hspan(
        y = max(list(historical_data_daily_df['high'].values)[-display_range_daily_int::]),
        line_width = 1,
        line_color = "#00FF11",
        line_dash = 'dashed',
        legend_label = '1-Year Daily High Max',
        alpha = plot_alpha_flt
    )
    sub_plot_11_obj.hspan(
        y = min(list(historical_data_daily_df['low'].values)[-display_range_daily_int:]),
        line_width = 1,
        line_color = "#FF0000",
        line_dash = 'dashed',
        legend_label = '1-Year Daily Low Min',
        alpha = plot_alpha_flt
    )

    # configure legend location
    sub_plot_11_obj.legend.location = 'top_left'
    # ==== ====

    # ==== ==== construct sub plot #1-2
    sub_plot_12_obj = figure(
        x_axis_type = 'datetime',
        tools = plot_function_str,
        width = document_width_int,
        height = 250,
        x_range = sub_plot_11_obj.x_range,
        title = 'Daily Volume History'
    )
    sub_plot_12_obj.grid.grid_line_alpha = 0.50
    sub_plot_12_obj.xaxis.axis_label = 'Time'
    sub_plot_12_obj.yaxis.axis_label = 'Normalized Trade Volume'
    # map dataframe indices to date strings and use as label overrides
    sub_plot_12_obj.xaxis.major_label_overrides = {i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(plot_data_daily_df['date'].values))}
    sub_plot_12_obj.xaxis.major_label_orientation = pi/4
    
    # render volume plot
    sub_plot_12_obj.extra_y_ranges = {'Trade Volume': Range1d(start = -0.2, end = 1.2)}
    volume_min_flt = np.min(plot_data_daily_df['volume'].values)
    volume_max_flt = np.max(plot_data_daily_df['volume'].values)
    sub_plot_12_obj.vbar(
        x = plot_data_daily_df['date'][increase_stick_bool_list],
        top = (plot_data_daily_df['volume'][increase_stick_bool_list] - volume_min_flt)/(volume_max_flt - volume_min_flt),
        legend_label = 'Increase Day Normalized Volume',
        width = bar_width_int,
        fill_color = '#99D594',
        line_color = 'black',
        alpha = plot_alpha_flt,
        y_range_name = 'Trade Volume'
    )
    sub_plot_12_obj.vbar(
        x = plot_data_daily_df['date'][decrease_stick_bool_list],
        top = (plot_data_daily_df['volume'][decrease_stick_bool_list] - volume_min_flt)/(volume_max_flt - volume_min_flt),
        legend_label = 'Decrease Day Normalized Volume',
        width = bar_width_int,
        fill_color = '#F2583E',
        line_color = 'black',
        alpha = plot_alpha_flt,
        y_range_name = 'Trade Volume'
    )
    
    # configure legend location
    sub_plot_12_obj.legend.location = 'top_left'
    # ==== ====

    # ==== ==== construct sub plot #1-3
    sub_plot_13_obj = figure(
        x_axis_type = 'datetime',
        tools = plot_function_str,
        width = document_width_int,
        height = 250,
        x_range = sub_plot_11_obj.x_range,
        title = 'Maximum Drawdown Percentage History'
    )
    sub_plot_13_obj.grid.grid_line_alpha = 0.50
    sub_plot_13_obj.xaxis.axis_label = 'Time'
    sub_plot_13_obj.yaxis.axis_label = 'Maximum Drawdown'
    # map dataframe indices to date strings and use as label overrides
    sub_plot_13_obj.xaxis.major_label_overrides = {i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(plot_data_daily_df['date'].values))}
    sub_plot_13_obj.xaxis.major_label_orientation = pi/4

    # render maximum drawdown lines
    sub_plot_13_obj.line(
        x = plot_data_daily_df['date'],
        y = drawdown_percentages_df,
        legend_label = 'Maximum Drawdown',
        color = Spectral4[2],
        alpha = plot_alpha_flt
    )

    # add capability for information display when hovered around plot
    hover_13_obj = HoverTool(
        tooltips = [
            ('Date/Time', '@x{%Y-%m-%d %H:%M:%S}'),
            ('Value', '@y{0.00}')
        ],
        formatters = {'@x': 'datetime'}
    )
    sub_plot_13_obj.add_tools(hover_13_obj)

    # configure legend location
    sub_plot_13_obj.legend.location = 'top_left'

    # ==== ====

    # ==== ==== construct sub heading #2
    sub_heading_two_str = f'Minutely Price History for {display_range_minutely_int} Minutes'
    sub_heading_2_obj = Paragraph(
        text = sub_heading_two_str,
        width = document_width_int,
        height_policy = 'auto',
        styles = {'font-size':'12pt', 'color': 'black', 'font-weight': 'bold', 'font-family': 'arial'}
    )
    # ==== ====

    # ==== ==== construct sub plot #2-1
    sub_plot_21_obj = figure(
        x_axis_type = 'datetime',
        tools = plot_function_str,
        width = document_width_int,
        title = 'Minutely Price History with Indicators'
    )
    sub_plot_21_obj.grid.grid_line_alpha = 0.5
    # sub_plot_21_obj.xaxis.axis_label = 'Time'
    sub_plot_21_obj.yaxis.axis_label = 'Price'
    # map dataframe indices to date strings and use as label overrides
    # sub_plot_21_obj.xaxis.major_label_overrides = {i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(plot_data_minutely_df['date'].values))}
    # sub_plot_21_obj.xaxis.major_label_orientation = pi/4
    sub_plot_21_obj.xaxis.visible = False

    # render price and indicator lines
    sub_plot_21_obj.line(
        x = plot_data_minutely_df['date'],
        y = plot_data_minutely_df['close'],
        legend_label = 'Close Price',
        color = Spectral4[0],
        alpha = plot_alpha_flt
    )
    sub_plot_21_obj.line(
        x = plot_data_minutely_df['date'],
        y = plot_data_minutely_df['ewma'],
        legend_label = 'Exponentially Weighted Moving Average',
        color = Spectral4[1],
        alpha = plot_alpha_flt
    )
    sub_plot_21_obj.line(
        x = plot_data_minutely_df['date'],
        y = plot_data_minutely_df['kma'],
        legend_label = 'Kalman Moving Average',
        color = Spectral4[2],
        alpha = plot_alpha_flt
    )

    # add capability for information display when hovered around plot
    hover_21_obj = HoverTool(
        tooltips = [
            ('Date/Time', '@x{%Y-%m-%d %H:%M:%S}'),
            ('Value', '$@y{0.00}')
        ],
        formatters = {'@x': 'datetime'}
    )
    sub_plot_21_obj.add_tools(hover_21_obj)

    # configure legend location
    sub_plot_21_obj.legend.location = 'top_left'
    # ==== ====

    # ==== ==== construct sub plot #2-2
    sub_plot_22_obj = figure(
        x_axis_type = 'datetime',
        tools = plot_function_str,
        width = document_width_int,
        x_range = sub_plot_21_obj.x_range,
        height = 250,
        title = 'Moving Average Convergence/Divergence & Signal'
    )
    sub_plot_22_obj.grid.grid_line_alpha = 0.50
    # sub_plot_22_obj.xaxis.axis_label = 'Time'
    sub_plot_22_obj.yaxis.axis_label = 'MACD & Signal'
    # map dataframe indices to date strings and use as label overrides
    # sub_plot_22_obj.xaxis.major_label_overrides = {i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(plot_data_daily_df['date'].values))}
    # sub_plot_22_obj.xaxis.major_label_orientation = pi/4
    sub_plot_22_obj.xaxis.visible = False

    # render macd and signal lines
    sub_plot_22_obj.line(
        x = plot_data_minutely_df['date'],
        y = plot_data_minutely_df['macd'],
        legend_label = 'MACD',
        color = Spectral4[0],
        alpha = plot_alpha_flt
    )
    sub_plot_22_obj.line(
        x = plot_data_minutely_df['date'],
        y = plot_data_minutely_df['signal'],
        legend_label = 'Signal',
        color = Spectral4[1],
        alpha = plot_alpha_flt
    )

    # add capability for information display when hovered around plot
    hover_22_obj = HoverTool(
        tooltips = [
            ('Date/Time', '@x{%Y-%m-%d %H:%M:%S}'),
            ('Value', '@y{0.00}')
        ],
        formatters = {'@x': 'datetime'}
    )
    sub_plot_22_obj.add_tools(hover_22_obj)

    # configure legend location
    sub_plot_22_obj.legend.location = 'top_left'
    # ==== ====

    # ==== ==== construct sub plot #2-3
    sub_plot_23_obj = figure(
        x_axis_type = 'datetime',
        tools = plot_function_str,
        width = document_width_int,
        x_range = sub_plot_21_obj.x_range,
        height = 250,
        title = 'Relative Strength Index'
    )
    sub_plot_23_obj.grid.grid_line_alpha = 0.50
    sub_plot_23_obj.xaxis.axis_label = 'Time'
    sub_plot_23_obj.yaxis.axis_label = 'RSI'
    # map dataframe indices to date strings and use as label overrides
    sub_plot_23_obj.xaxis.major_label_overrides = {i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(plot_data_daily_df['date'].values))}
    sub_plot_23_obj.xaxis.major_label_orientation = pi/4

    # render rsi
    sub_plot_23_obj.line(
        x = plot_data_minutely_df['date'],
        y = plot_data_minutely_df['rsi'],
        legend_label = 'RSI',
        color = Spectral4[0],
        alpha = plot_alpha_flt
    )

    # add capability for information display when hovered around plot
    hover_23_obj = HoverTool(
        tooltips = [
            ('Date/Time', '@x{%Y-%m-%d %H:%M:%S}'),
            ('RSI', '@y{0.00}')
        ],
        formatters = {'@x': 'datetime'}
    )
    sub_plot_23_obj.add_tools(hover_23_obj)

    # configure legend location
    sub_plot_23_obj.legend.location = 'top_left'
    # ==== ====

    # ==== ==== construct label objects to display fundamentals data
    if fundamentals_data_dict:
        # construct metric value (Price-to-Earnings = SharePrice / EarningsPerShareBasic)
        try:
            metric_val_11_1 = round(
                float(historical_data_minutely_df['close'].iloc[-1])/
                float(fundamentals_data_dict[ticker_str][fundamentals_variable_name_str_list[0]]['val'].iloc[-1]), 
                2
            )
            # construct citation text
            citation_text_11_1 = f'''PE (< 20.0):
            {
                fundamentals_data_dict[ticker_str][fundamentals_variable_name_str_list[0]]['frame'].iloc[-1]
            }: {
                metric_val_11_1
            }'''
            # construct citation color
            citation_color_11_1 = 'green' if 0.0 < metric_val_11_1 < 20.0 else 'red'
            # generate citation label
            citation_11_obj = Label(
                border_line_color = 'white',
                border_line_alpha = plot_alpha_flt - 0.5,
                background_fill_color = citation_color_11_1,
                background_fill_alpha = plot_alpha_flt - 0.5,
                text = citation_text_11_1,
                text_font_size = '10pt',
                text_align = 'left',
                padding = 2,
                x = 5,
                y = 5,
                x_units = 'screen',
                y_units = 'screen'
            )

            # add citation to respective plot
            sub_plot_11_obj.add_layout(citation_11_obj)

        except KeyError:
            pass

        # ====

        # construct metric value (Current Ratio = AssetsCurrent / LiabilitiesCurrent)
        try:
            metric_val_12_1 = round(
                float(fundamentals_data_dict[ticker_str][fundamentals_variable_name_str_list[1]]['val'].iloc[-1])/
                float(fundamentals_data_dict[ticker_str][fundamentals_variable_name_str_list[2]]['val'].iloc[-1]), 
                2
            )
            # construct citation text
            citation_text_12_1 = f'''CR (> 1.5):
            {
                fundamentals_data_dict[ticker_str][fundamentals_variable_name_str_list[1]]['frame'].iloc[-1]
            }: {
                metric_val_12_1
            }'''
            # construct citation color
            citation_color_12_1 = 'green' if metric_val_12_1 > 1.5 else 'red'
            # generate citation label
            citation_12_obj = Label(
                border_line_color = 'white',
                border_line_alpha = plot_alpha_flt - 0.5,
                background_fill_color = citation_color_12_1,
                background_fill_alpha = plot_alpha_flt - 0.5,
                text = citation_text_12_1,
                text_font_size = '10pt',
                text_align = 'left',
                padding = 2,
                x = 5,
                y = 50,
                x_units = 'screen',
                y_units = 'screen'
            )

            # add citation to respective plot
            sub_plot_11_obj.add_layout(citation_12_obj)
        
        except KeyError:
            pass

    # ==== ====

    # save chart
    output_file(
        filename = ROOT_PATH + 'reports/analyses/' + f'{w2_generateDateStringYYYYMMDD()}_' + ticker_str + '.html'
    )
    grid_plot_obj = gridplot(
        children = [
            main_header_obj,
            sub_heading_1_obj,
            sub_plot_11_obj,
            sub_plot_12_obj,
            sub_plot_13_obj,
            sub_heading_2_obj,
            sub_plot_21_obj,
            sub_plot_22_obj,
            sub_plot_23_obj,
            report_date_obj
        ],
        ncols = 1,
        width = document_width_int
    )
    try:
        save(grid_plot_obj)
    except SerializationError:
        pass


if __name__ == '__main__':
    # specify ticker symbol
    symbol_str = 'IAUM'

    # generate analysis
    w1_generateAnalysisReport(
        ticker_str = symbol_str,
        simulated_on = True
    )