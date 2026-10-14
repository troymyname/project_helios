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

import os
import random

from matplotlib import pyplot as plt
from matplotlib.colors import TABLEAU_COLORS
from pandas.plotting import register_matplotlib_converters

# register time series converters with matplotlib library
register_matplotlib_converters()

# extract color identifiers (10 total colors)
color_identifier_list = list(TABLEAU_COLORS.keys())


def w2_plotQuickly(
        x_data_arr,
        x_axis_label_str,
        y_data_arr_list,
        y_data_label_str_list,
        y_axis_label_str,
        plot_title_str = None,
        save_on = False,
        save_file_name_str = None,
        save_path_str = None,
        show_on = False
):
    """
        description:
            Plots one or more series against a common x-axis with a simple Matplotlib layout.
            The function can optionally save the figure and display it interactively.
        args:
            x_data_arr: array-like
                Shared x-axis values for the plotted series.
            x_axis_label_str: str
                Label for the x-axis.
            y_data_arr_list: list
                List of y-series values to plot.
            y_data_label_str_list: list
                Labels corresponding to each y-series.
            y_axis_label_str: str
                Label for the y-axis.
            plot_title_str: str, default None
                Optional title for the plot.
            save_on: bool, default False
                Whether to save the figure.
            save_file_name_str: str, default None
                Filename to use when saving.
            save_path_str: str, default None
                Directory to write the saved figure into.
            show_on: bool, default False
                Whether to display the figure after plotting.
        returns:
            None
    """
    if isinstance(y_data_arr_list, list):
        # close previous opened matplotlib figures
        plt.close()

        # plot data
        for index_int in range(len(y_data_arr_list)):
            plt.plot(x_data_arr, y_data_arr_list[index_int], label = y_data_label_str_list[index_int])

        # configure and show plot
        plt.xlabel(x_axis_label_str)
        plt.ylabel(y_axis_label_str)
        plt.title(plot_title_str)
        plt.grid(
            visible = True,
            which = 'both',
            axis = 'both'
        )
        plt.legend()

        # save plot if flag is turned on
        if save_on and save_file_name_str is not None and save_path_str is not None:
            plt.savefig(
                fname = os.path.join(save_path_str, save_file_name_str),
                dpi = 300,
                bbox_inches = 'tight'
            )

        # show plot if flag is turned on
        if show_on:
            plt.show()

    else:
        print('ERROR: Function expected y data to be provided in a list format...')


def w2_plotInOneScale(
        x_data_df,
        x_axis_label_str,
        y_data_df_list,
        y_data_label_str_list,
        y_axis_label_str,
        plot_title_str = None,
        recent_data_chunk_int = None,
        save_on = False,
        save_file_name_str = None,
        save_path_str = None,
        show_on = False
):
    """
        description:
            Plots multiple series on a single y-axis and can optionally restrict the
            view to a recent data window for easier inspection.
        args:
            x_data_df: pandas.Series or array-like
                Shared x-axis values.
            x_axis_label_str: str
                Label for the x-axis.
            y_data_df_list: list
                List of y-axis series to plot.
            y_data_label_str_list: list
                Labels for each plotted series.
            y_axis_label_str: str
                Label for the y-axis.
            plot_title_str: str, default None
                Optional title for the plot.
            recent_data_chunk_int: int, default None
                Number of recent observations to display.
            save_on: bool, default False
                Whether to save the figure.
            save_file_name_str: str, default None
                Filename to use when saving.
            save_path_str: str, default None
                Directory to write the saved figure into.
            show_on: bool, default False
                Whether to display the figure after plotting.
        returns:
            None
    """
    if isinstance(y_data_df_list, list):
        # close previous opened matplotlib figures
        plt.close()

        # make a figure and a set of subplots
        fig, ax = plt.subplots(nrows = 1, ncols = 1, figsize = (10,6))

        # rotate major tick labels by 45 degrees
        plt.setp(ax.xaxis.get_majorticklabels(), rotation = 45)

        # set plot title
        if plot_title_str is not None:
            ax.set_title(label = plot_title_str)

        # select the most recent data for plotting
        if recent_data_chunk_int is not None:
            # assert and apply indexing on x data
            assert recent_data_chunk_int < len(x_data_df)
            x_data_df = x_data_df[-recent_data_chunk_int:]
            # assert and apply indexing on y data
            for index_int in range(len(y_data_df_list)):
                assert recent_data_chunk_int < len(y_data_df_list[index_int])
                y_data_df_list[index_int] = y_data_df_list[index_int][-recent_data_chunk_int:]

        # configure colors
        ax.set_prop_cycle(color = color_identifier_list)

        # configure plot (color set automatically)
        ax.set_xlabel(xlabel = x_axis_label_str)
        ax.set_ylabel(ylabel = y_axis_label_str)
        for index_int in range(len(y_data_df_list)):
            ax.plot(x_data_df, y_data_df_list[index_int], label = y_data_label_str_list[index_int])

        # show grid lines
        ax.grid(
            visible = True,
            which = 'both',
            axis = 'both'
        )

        # save plot if flag is turned on
        if save_on and save_file_name_str is not None and save_path_str is not None:
            plt.savefig(
                fname = os.path.join(save_path_str, save_file_name_str),
                dpi = 300,
                bbox_inches = 'tight'
            )

        # adjust the spacing between/around subplots and show plot if flag is turned on
        fig.tight_layout()
        if show_on:
            plt.legend()
            plt.show()

    else:
        print('ERROR: Function expected y data to be provided in a list format...')


def w2_plotInTwoScales(
        x_data_df,
        x_axis_label_str,
        y_data_df_list,
        y_axes_label_str_list,
        y_axes_limits_bool_list,
        y_axes_limits_list,
        datetime_on = True,
        plot_title_str = None,
        recent_data_chunk_int = None,
        save_on = False,
        save_file_name_str = None,
        save_path_str = None,
        show_on = False
):
    """
        description:
            Plots two related series on separate y-axes, which is useful when the
            data ranges differ significantly and need to be compared visually.
        args:
            x_data_df: pandas.Series or array-like
                Shared x-axis values.
            x_axis_label_str: str
                Label for the x-axis.
            y_data_df_list: list
                Two series to visualize on the primary and secondary axes.
            y_axes_label_str_list: list
                Labels for the left and right y-axes.
            y_axes_limits_bool_list: list
                Flags indicating whether each axis should have custom limits.
            y_axes_limits_list: list
                Custom y-axis limits for each scale.
            datetime_on: bool, default True
                Whether the x-axis values are datetime-like.
            plot_title_str: str, default None
                Optional title for the plot.
            recent_data_chunk_int: int, default None
                Number of recent observations to display.
            save_on: bool, default False
                Whether to save the figure.
            save_file_name_str: str, default None
                Filename to use when saving.
            save_path_str: str, default None
                Directory to write the saved figure into.
            show_on: bool, default False
                Whether to display the figure after plotting.
        returns:
            None
    """
    if isinstance(y_data_df_list, list):
        # close previous opened matplotlib figures
        plt.close()

        # make a figure and a set of subplots
        fig, ax1 = plt.subplots(nrows = 1, ncols = 1, figsize = (10,6))

        # rotate major tick labels by 45 degrees
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation = 45)

        # set plot title
        if plot_title_str is not None:
            ax1.set_title(label = plot_title_str)

        # select the most recent data for plotting
        if recent_data_chunk_int is not None:
            # assert and apply indexing on x data
            assert recent_data_chunk_int < len(x_data_df)
            if datetime_on:
                x_data_df = x_data_df[-recent_data_chunk_int:]
            else:
                x_data_df = x_data_df.astype(float)[-recent_data_chunk_int:]
            # assert and apply indexing on y data
            for index_int in range(len(y_data_df_list)):
                assert recent_data_chunk_int < len(y_data_df_list[index_int])
                y_data_df_list[index_int] = y_data_df_list[index_int].astype(float)[-recent_data_chunk_int:]

        # configure first plot
        color = color_identifier_list[random.randint(a = 0, b = 4)]
        ax1.set_xlabel(xlabel = x_axis_label_str)
        ax1.set_ylabel(ylabel = y_axes_label_str_list[0], color = color)
        ax1.plot(x_data_df, y_data_df_list[0], color = color)

        # adjust y-axis limits
        if y_axes_limits_bool_list[0]:
            ax1.set_ylim(
                bottom = y_axes_limits_list[0][0],
                top = y_axes_limits_list[0][1]
            )

        # show grid lines
        ax1.grid(
            visible = True,
            which = 'major',
            axis = 'x'
        )

        # instantiate a second axes that shares the same x-axis
        ax2 = ax1.twinx()

        # configure second plot
        color = color_identifier_list[random.randint(a = 5, b = 9)]
        ax2.set_ylabel(ylabel = y_axes_label_str_list[1], color = color)
        ax2.plot(x_data_df, y_data_df_list[1], color = color)

        # adjust y-axis limits
        if y_axes_limits_bool_list[1]:
            ax2.set_ylim(
                bottom = y_axes_limits_list[1][0],
                top = y_axes_limits_list[1][1]
            )

        # show grid lines (since x-axis is common between ax1 and ax2, enable for y in ax2)
        ax2.grid(
            visible = True,
            which = 'major',
            axis = 'y'
        )

        # save plot if flag is turned on
        if save_on and save_file_name_str is not None and save_path_str is not None:
            plt.savefig(
                fname = os.path.join(save_path_str, save_file_name_str),
                dpi = 300,
                bbox_inches = 'tight'
            )

        # adjust the spacing between/around subplots and show plot if flag is turned on
        fig.tight_layout()
        if show_on:
            plt.legend()
            plt.show()

    else:
        print('ERROR: Function expected y data to be provided in a list format...')


def w2_plotInSubplots(
        x_data_df,
        x_axis_label_str,
        y_data_df_list,
        y_data_label_str_list,
        y_axes_label_str_list,
        custom_heights_on = False,
        custom_heights_ratios_list = [1, 1, 1],
        plot_title_str = None,
        recent_data_chunk_int = None,
        save_on = False,
        save_file_name_str = None,
        save_path_str = None,
        show_on = False
):
    """
        description:
            Creates a multi-panel plot layout where each subplot can visualize a separate
            set of data series and custom heights can be applied to emphasize certain panels.
        args:
            x_data_df: pandas.Series or array-like
                Shared x-axis values.
            x_axis_label_str: str
                Label for the x-axis.
            y_data_df_list: list
                Nested list of data to place into each subplot.
            y_data_label_str_list: list
                Labels corresponding to each data series inside the subplot panels.
            y_axes_label_str_list: list
                Y-axis labels for each subplot.
            custom_heights_on: bool, default False
                Whether to use custom subplot heights.
            custom_heights_ratios_list: list, default [1, 1, 1]
                Relative heights for each subplot when custom heights are enabled.
            plot_title_str: str, default None
                Optional title for the figure.
            recent_data_chunk_int: int, default None
                Number of recent observations to display.
            save_on: bool, default False
                Whether to save the figure.
            save_file_name_str: str, default None
                Filename to use when saving.
            save_path_str: str, default None
                Directory to write the saved figure into.
            show_on: bool, default False
                Whether to display the figure after plotting.
        returns:
            None
    """
    if isinstance(y_data_df_list, list):
        # close previous opened matplotlib figures
        plt.close()

        # make a figure and a set of subplots
        if not custom_heights_on:
            fig_obj, axs_obj = plt.subplots(
                nrows = len(y_data_df_list), 
                ncols = 1, 
                sharex = True, 
                figsize = (10,6)
            )
        else:
            fig_obj, axs_obj = plt.subplots(
                nrows = len(y_data_df_list), 
                ncols = 1, 
                sharex = True, 
                figsize = (10,6),
                gridspec_kw = {'height_ratios': custom_heights_ratios_list}
            )

        # rotate major tick labels by 45 degrees
        plt.setp(axs_obj[-1].xaxis.get_majorticklabels(), rotation = 45)

        # set plot title
        if plot_title_str is not None:
            fig_obj.suptitle(t = plot_title_str)

        # select the most recent data for plotting
        if recent_data_chunk_int is not None:
            # assert and apply indexing on x data
            assert recent_data_chunk_int < len(x_data_df)
            x_data_df = x_data_df[-recent_data_chunk_int:]
            # assert and apply indexing on y data
            for index_int in range(len(y_data_df_list)):
                assert recent_data_chunk_int < len(y_data_df_list[index_int])
                y_data_df_list[index_int] = y_data_df_list[index_int][-recent_data_chunk_int:]

        # set x label
        axs_obj[-1].set_xlabel(xlabel = x_axis_label_str)
        for index_int in range(len(y_data_df_list)):
            if isinstance(y_data_df_list[index_int], list):
                # set y label
                axs_obj[index_int].set_ylabel(ylabel = y_axes_label_str_list[index_int])
                for inner_index_int in range(len(y_data_df_list[index_int])):
                    # generate plot with grid
                    if not 'Trade Signal' in y_data_label_str_list[index_int][inner_index_int]:
                        # generate plots for signals with grid
                        axs_obj[index_int].plot(
                            x_data_df,
                            y_data_df_list[index_int][inner_index_int],
                            label = y_data_label_str_list[index_int][inner_index_int]
                        )
                        axs_obj[index_int].grid(
                            visible = True,
                            which = 'both',
                            axis = 'both'
                        )
                    else:
                        # plot acquisition signals
                        # NOTE: Below, the marker is placed shifted from the first element of the list, which is the closing price.
                        axs_obj[index_int].scatter(
                            x = x_data_df[y_data_df_list[index_int][inner_index_int] == 1.0].index,
                            y = (y_data_df_list[0][0] - y_data_df_list[0][0] * 0.05)[y_data_df_list[index_int][inner_index_int] == 1.0],
                            s = 75,
                            marker = '^',
                            color = 'g',
                            label = 'Buy'
                        )
                        # plot disposal signals
                        # NOTE: Below, the marker is placed shifted from the first element of the list, which is the closing price.
                        axs_obj[index_int].scatter(
                            x = x_data_df[y_data_df_list[index_int][inner_index_int] == -1.0].index,
                            y = (y_data_df_list[0][0] + y_data_df_list[0][0] * 0.05)[y_data_df_list[index_int][inner_index_int] == -1.0],
                            s = 75,
                            marker = 'v',
                            color = 'r',
                            label = 'Sell'
                        )

            else:
                # set y label
                axs_obj[index_int].set_ylabel(ylabel = y_axes_label_str_list[index_int])
                # generate plot with grid
                axs_obj[index_int].plot(
                    x_data_df,
                    y_data_df_list[index_int],
                    label = y_data_label_str_list[index_int]
                )
                axs_obj[index_int].grid(
                    visible = True,
                    which = 'both',
                    axis = 'both'
                )

        # save plot if flag is turned on
        if save_on and save_file_name_str is not None and save_path_str is not None:
            plt.savefig(
                fname = os.path.join(save_path_str, save_file_name_str),
                dpi = 300,
                bbox_inches = 'tight'
            )

        # adjust the spacing between subplots and show plot if flag is turned on
        fig_obj.tight_layout()
        fig_obj.subplots_adjust(hspace = 0)
        if show_on:
            for index_int in range(len(y_data_df_list)):
                axs_obj[index_int].legend(loc = 'lower right')
            plt.show()

    else:
        print('ERROR: Function expected y data to be provided in a list format...')