# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://github.com/ranaroussi/quantstats/blob/main/quantstats/stats.py
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import numpy as np
import numpy.random as npr


def w2_simulatePriceInBrownianMotion(
        initial_value_flt,
        samples_int = 1000,
        timespan_int = 1,
        mu_flt = 0.1,
        sigma_flt = 0.05
):
    """
        description:
            A function that simulates the Geometric Brownian Motion
        args:
            initial_value_flt: starting point of the simulation
            timespan_int: timespan value
            samples_int: number of samples to simulate
            mu_flt: deterministic component, i.e. drift
            sigma_flt: stochastic component, i.e. risk/volatility associated with the Weiner process
        returns:
            timesteps_arr: array of timesteps
            simulated_values_arr: array of simulated values
        references:
            [1] https://en.wikipedia.org/wiki/Geometric_Brownian_motion
    """

    # calculate timestep dt
    dt = timespan_int / samples_int

    # initialize W(t)
    W = np.zeros(samples_int + 1)

    # create samples_int timesteps
    timesteps_arr = np.linspace(
        start = 0,
        stop = timespan_int,
        num = samples_int + 1
    )

    # use the cumulative sum for calculating W at every timestep
    W[1:samples_int+1] = np.cumsum(
        npr.normal(
            loc = 0,
            scale = np.sqrt(dt),
            size = samples_int
        )
    )

    # calculate simulated values at each timestep
    simulated_values_arr = initial_value_flt * np.exp((mu_flt - (0.5 * (sigma_flt ** 2))) * timesteps_arr + (sigma_flt * W))

    return timesteps_arr, simulated_values_arr


if __name__ == '__main__':
    from utils.w2_plot import w2_plotQuickly
    [timesteps_arr, simulated_values_arr] = w2_simulatePriceInBrownianMotion(initial_value_flt = 1.0)
    w2_plotQuickly(
        x_data_arr = timesteps_arr,
        x_axis_label_str = 'Time Step',
        y_data_arr_list = [simulated_values_arr],
        y_data_label_str_list = ['Simulated Values'],
        y_axis_label_str = 'Simulated Values',
        plot_title_str = 'Brownian Motion',
        show_on = True
    )