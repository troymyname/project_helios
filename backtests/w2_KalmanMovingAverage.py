# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://www.backtrader.com/
# [2] https://www.backtrader.com/blog/posts/2017-02-14-kalman-et-al/kalman-et-al/
# [3] https://www.quantstart.com/articles/kalman-filter-based-pairs-trading-strategy-in-qstrader/
# [4] https://github.com/pykalman/pykalman
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import backtrader as bt
import pykalman


class KalmanMovingAverage(bt.indicators.MovingAverageBase):
    lines = ('kma',)
    params = (
        ('initial_state_covariance', 1.0), # NOTE: Reducing the value tracks the signal more closely.
        ('observation_covariance', 1.0), # NOTE: Reducing the value tracks the signal more closely.
        ('transition_covariance', 0.05), # NOTE: Increasing the value tracks the signal more closely.
    )

    def __init__(self):
        # determine when to deliver values
        self.addminperiod(self.p.period)
        # derive previous day value
        self._dlast = self.data(-1)

    def nextstart(self):
        self._k1 = self._dlast[0]
        self._c1 = self.p.initial_state_covariance

        self._kf = pykalman.KalmanFilter(
            transition_matrices = [1],
            observation_matrices = [1],
            observation_covariance = self.p.observation_covariance,
            transition_covariance = self.p.transition_covariance,
            initial_state_mean = self._k1,
            initial_state_covariance = self._c1,
        )

        self.next()

    def next(self):
        k1, self._c1 = self._kf.filter_update(self._k1, self._c1, self.data[0])
        self.lines.kma[0] = self._k1 = k1