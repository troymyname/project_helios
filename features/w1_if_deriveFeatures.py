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

import warnings
from config import WARNING_IGNORE_CLASS_FUTURE
warnings.simplefilter(action = 'ignore', category = WARNING_IGNORE_CLASS_FUTURE)

import numpy as np
import time

from concurrent.futures import as_completed, ProcessPoolExecutor
from packages.tti_snapshot.indicators import AccumulationDistributionLine
from packages.tti_snapshot.indicators import AverageTrueRange
from packages.tti_snapshot.indicators import BollingerBands
from packages.tti_snapshot.indicators import ChaikinMoneyFlow
from packages.tti_snapshot.indicators import ChaikinOscillator
from packages.tti_snapshot.indicators import ChandeMomentumOscillator
from packages.tti_snapshot.indicators import DetrendedPriceOscillator
from packages.tti_snapshot.indicators import DirectionalMovementIndex
from packages.tti_snapshot.indicators import DoubleExponentialMovingAverage
from packages.tti_snapshot.indicators import EaseOfMovement
from packages.tti_snapshot.indicators import Envelopes
from packages.tti_snapshot.indicators import FibonacciRetracement
from packages.tti_snapshot.indicators import ForecastOscillator
from packages.tti_snapshot.indicators import IchimokuCloud
from packages.tti_snapshot.indicators import IntradayMovementIndex
from packages.tti_snapshot.indicators import KlingerOscillator
from packages.tti_snapshot.indicators import LinearRegressionIndicator
from packages.tti_snapshot.indicators import LinearRegressionSlope
from packages.tti_snapshot.indicators import MarketFacilitationIndex
from packages.tti_snapshot.indicators import MassIndex
from packages.tti_snapshot.indicators import MedianPrice
from packages.tti_snapshot.indicators import Momentum
from packages.tti_snapshot.indicators import MovingAverage
from packages.tti_snapshot.indicators import MovingAverageConvergenceDivergence
from packages.tti_snapshot.indicators import NegativeVolumeIndex
from packages.tti_snapshot.indicators import OnBalanceVolume
from packages.tti_snapshot.indicators import ParabolicSAR
from packages.tti_snapshot.indicators import Performance
from packages.tti_snapshot.indicators import PositiveVolumeIndex
from packages.tti_snapshot.indicators import PriceAndVolumeTrend
from packages.tti_snapshot.indicators import PriceChannel
from packages.tti_snapshot.indicators import PriceOscillator
from packages.tti_snapshot.indicators import PriceRateOfChange
from packages.tti_snapshot.indicators import ProjectionBands
from packages.tti_snapshot.indicators import ProjectionOscillator
from packages.tti_snapshot.indicators import Qstick
from packages.tti_snapshot.indicators import RangeIndicator
from packages.tti_snapshot.indicators import RelativeMomentumIndex
from packages.tti_snapshot.indicators import RelativeStrengthIndex
from packages.tti_snapshot.indicators import RelativeVolatilityIndex
from packages.tti_snapshot.indicators import StandardDeviation
from packages.tti_snapshot.indicators import StochasticMomentumIndex
from packages.tti_snapshot.indicators import StochasticOscillator
from packages.tti_snapshot.indicators import SwingIndex
from packages.tti_snapshot.indicators import TimeSeriesForecast
from packages.tti_snapshot.indicators import TripleExponentialMovingAverage
from packages.tti_snapshot.indicators import TypicalPrice
from packages.tti_snapshot.indicators import UltimateOscillator
from packages.tti_snapshot.indicators import VerticalHorizontalFilter
from packages.tti_snapshot.indicators import VolatilityChaikins
from packages.tti_snapshot.indicators import VolumeOscillator
from packages.tti_snapshot.indicators import VolumeRateOfChange
from packages.tti_snapshot.indicators import WeightedClose
from packages.tti_snapshot.indicators import WildersSmoothing
from packages.tti_snapshot.indicators import WilliamsAccumulationDistribution
from packages.tti_snapshot.indicators import WilliamsR
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, RobustScaler

# import custom configs and utils
from config import RAY_DATA_TYPE
from config import DATA_LENGTH_MIN, PCA_DIM_REDUCTION, PCA_NUM_PRINCIPAL_COMPONENTS, ROOT_PATH, TRADE_RECENT_DATA_CHUNK_RL_INFERENCE, WAIT_TIME_ONE
from data.w1_if_getHistoricalData import w1_if_getHistoricalData_D, w1_if_getHistoricalDataInThreadsMain
from utils.w2_performDataFrameOps import (
    w2_castToPreferredDataType,
    w2_dropColumns,
    w2_dropRowsWithInfResetIndex,
    w2_dropRowsWithNANResetIndex,
    w2_extractColumns,
    w2_generateDataFrame,
    w2_mergeDataFrames,
    w2_replaceNANWithValue,
    w2_roundByDecimals,
    w2_writeDataFrameToCSV
)
from utils.w2_performDataFrameOps import w2_customCastToDataTypeByColumns, w2_customFillForward


def w1_if_deriveUnitFeatures(
        ticker_str,
        data_df,
        data_path_str,
        scaling_method_str,
        dim_reduction_pca_on = True,
        inspection_scree_plot_save_on = False,
        inspection_feature_data_save_on = False
):
    """
    Generate feature and support datasets for a single ticker symbol.

    The function computes a wide variety of technical indicators using the
    `tti_snapshot` library, merges them into a single feature DataFrame, applies
    optional scaling and PCA-based dimensionality reduction, and returns both the
    feature matrix and cleaned support data.

    Parameters:
        ticker_str (str): Ticker symbol for the current feature extraction.
        data_df (pd.DataFrame): Historical price and volume data for the ticker.
        data_path_str (str): Relative path where feature inspection CSVs may be saved.
        scaling_method_str (str): Scaling method to use, e.g. 'standard' or 'robust'.
        dim_reduction_pca_on (bool): Whether to apply PCA dimensionality reduction.
        inspection_scree_plot_save_on (bool): If True, save a scree plot for PCA.
        inspection_feature_data_save_on (bool): If True, save the generated feature DataFrame to CSV.

    Returns:
        dict: Dictionary containing the feature DataFrame under `ticker_str` and
            support data under `ticker_str + '_support'`.
    """
    # fill forward (NOTE: 'date' column comes in datetime format.)
    data_df = w2_customFillForward(
        df = w2_customCastToDataTypeByColumns(
            df = w2_dropRowsWithNANResetIndex(
                df = data_df
            )
        ),
        interval_str = '1d'
    )

    # ====
    # extract out raw data
    support_data_df = w2_extractColumns(
        df = data_df.copy(deep = True),
        column_list = ['open', 'high', 'low', 'close', 'volume']
    )

    # ====
    
    # create adl indicator (contains 'adl' column)
    adl_df = AccumulationDistributionLine(input_data = data_df, fill_missing_values = False).getTiData()
    # create atr indicator (contains 'atr' columns)
    atr_df = AverageTrueRange(input_data = data_df, fill_missing_values = False).getTiData()
    # create bb indicator (contains 'middle_band', 'upper_band_x', 'lower_band_x' columns)
    bb_df = BollingerBands(input_data = data_df, fill_missing_values = False).getTiData()
    # create cmf indicator (contains 'cmf' column)
    cmf_df = ChaikinMoneyFlow(input_data = data_df, fill_missing_values = False).getTiData()
    # create co indicator (contains 'co' column)
    co_df = ChaikinOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create cmo indicator (contains 'cmo' column)
    cmo_df = ChandeMomentumOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create dpo indicator (contains 'dpo' column)
    dpo_df = DetrendedPriceOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create dmi indicator (contains '+di', '-di', 'dx', 'adx', 'adxr' columns)
    dmi_df = DirectionalMovementIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create dema indicator (contains 'dema' column)
    dema_df = DoubleExponentialMovingAverage(input_data = data_df, fill_missing_values = False).getTiData()
    # create emv indicator (contains 'emv', 'emv_ma' columns)
    eom_df = EaseOfMovement(input_data = data_df, fill_missing_values = False).getTiData()

    # create env indicator (contains 'upper_band_y', 'lower_band_y' columns)
    env_df = Envelopes(input_data = data_df, fill_missing_values = False).getTiData()
    # create fr indicator (contains 'rl_0.0', 'rl_23.6', 'rl_38.2', 'rl_50.0', 'rl_61.8', 'rl_100.0' columns)
    fr_df = FibonacciRetracement(input_data = data_df, fill_missing_values = False).getTiData()
    # create fo indicator (contains 'fosc' column)
    fo_df = ForecastOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create fo indicator (contains 'tenkan-sen', 'kijun-sen', 'senkou-a', 'senkou-b' columns)
    ic_df = IchimokuCloud(input_data = data_df, fill_missing_values = False).getTiData()
    # create fo indicator (contains 'imi' column)
    imi_df = IntradayMovementIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create ko indicator (contains 'ko' column)
    ko_df = KlingerOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create lri indicator (contains 'lri' column)
    lri_df = LinearRegressionIndicator(input_data = data_df, fill_missing_values = False).getTiData()
    # create lrs indicator (contains 'lrs' column)
    lrs_df = LinearRegressionSlope(input_data = data_df, fill_missing_values = False).getTiData()
    # create mfi indicator (contains 'mfi' column)
    mfi_df = MarketFacilitationIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create mi indicator (contains 'mi' column)
    mi_df = MassIndex(input_data = data_df, fill_missing_values = False).getTiData()

    # create mp indicator (contains 'mp' column)
    mp_df = MedianPrice(input_data = data_df, fill_missing_values = False).getTiData()
    # create mom indicator (contains 'mom' column)
    mom_df = Momentum(input_data = data_df, fill_missing_values = False).getTiData()
    # create ema indicator (contains 'ma-exponential' column)
    ema_df = MovingAverage(input_data = data_df, ma_type = 'exponential', fill_missing_values = False).getTiData()
    # create sma indicator (contains 'ma-simple' column)
    sma_df = MovingAverage(input_data = data_df, ma_type = 'simple', fill_missing_values = False).getTiData()
    # create tsma indicator (contains 'ma-time_series' column)
    tsma_df = MovingAverage(input_data = data_df, ma_type = 'time_series', fill_missing_values = False).getTiData()
    # create tma indicator (contains 'ma-triangular' column)
    tma_df = MovingAverage(input_data = data_df, ma_type = 'triangular', fill_missing_values = False).getTiData()
    # create vma indicator (contains 'ma-variable' column)
    vma_df = MovingAverage(input_data = data_df, ma_type = 'variable', fill_missing_values = False).getTiData()
    # create macd indicator (contains 'macd', 'signal_line' columns)
    macd_df = MovingAverageConvergenceDivergence(input_data = data_df, fill_missing_values = False).getTiData()
    # create nvi indicator (contains 'nvi' column)
    nvi_df = NegativeVolumeIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create obv indicator (contains 'obv' column)
    obv_df = OnBalanceVolume(input_data = data_df, fill_missing_values = False).getTiData()

    # create obv indicator (contains 'sar' column)
    psar_df = ParabolicSAR(input_data = data_df, fill_missing_values = False).getTiData()
    # create per indicator (contains 'prf', target_LONG columns)
    per_df = Performance(input_data = data_df, fill_missing_values = False).getTiData()
    # create pvi indicator (contains 'pvi' column)
    pvi_df = PositiveVolumeIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create pvt indicator (contains 'pvt' column)
    pvt_df = PriceAndVolumeTrend(input_data = data_df, fill_missing_values = False).getTiData()
    # create pc indicator (contains 'highest_high', 'lowest_low' columns)
    pc_df = PriceChannel(input_data = data_df, fill_missing_values = False).getTiData()
    # create po indicator (contains 'posc' column)
    po_df = PriceOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create prc indicator (contains 'prc' column)
    prc_df = PriceRateOfChange(input_data = data_df, fill_missing_values = False).getTiData()
    # create pb indicator (contains 'upper_band', 'lower_band' columns)
    pb_df = ProjectionBands(input_data = data_df, fill_missing_values = False).getTiData()
    # create pro indicator (contains 'posc', 'trigger_line' columns)
    pro_df = ProjectionOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create qs indicator (contains 'qstick' column)
    qs_df = Qstick(input_data = data_df, fill_missing_values = False).getTiData()

    # create ri indicator (contains 'ri' column)
    ri_df = RangeIndicator(input_data = data_df, fill_missing_values = False).getTiData()
    # create rmi indicator (contains 'rmi' column)
    rmi_df = RelativeMomentumIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create rsi indicator (contains 'rsi' column)
    rsi_df = RelativeStrengthIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create rvi indicator (contains 'rvi' column)
    rvi_df = RelativeVolatilityIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create sd indicator (contains 'sd' column)
    sd_df = StandardDeviation(input_data = data_df, fill_missing_values = False).getTiData()
    # create sd indicator (contains 'smi' column)
    smi_df = StochasticMomentumIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create so indicator (contains '%K_x', '%D_x' columns)
    sos_df = StochasticOscillator(input_data = data_df, d_method = 'simple', fill_missing_values = False).getTiData()
    # create so indicator (contains '%K_y', '%D_y' columns)
    soe_df = StochasticOscillator(input_data = data_df, d_method = 'exponential', fill_missing_values = False).getTiData()
    # create si indicator (contains 'swi' column)
    si_df = SwingIndex(input_data = data_df, fill_missing_values = False).getTiData()
    # create tsf indicator (contains 'tsf' column)
    tsf_df = TimeSeriesForecast(input_data = data_df, fill_missing_values = False).getTiData()

    # create tema indicator (contains 'tema' column)
    tema_df = TripleExponentialMovingAverage(input_data = data_df, fill_missing_values = False).getTiData()
    # create tp indicator (contains 'tp' column)
    tp_df = TypicalPrice(input_data = data_df, fill_missing_values = False).getTiData()
    # create uo indicator (contains 'uosc' column)
    uo_df = UltimateOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create vhf indicator (contains 'vhf' column)
    vhf_df = VerticalHorizontalFilter(input_data = data_df, fill_missing_values = False).getTiData()
    # create vc indicator (contains 'vch' column)
    vc_df = VolatilityChaikins(input_data = data_df, fill_missing_values = False).getTiData()
    # create vo indicator (contains 'vosc' column)
    vo_df = VolumeOscillator(input_data = data_df, fill_missing_values = False).getTiData()
    # create vrc indicator (contains 'vrc' column)
    vrc_df = VolumeRateOfChange(input_data = data_df, fill_missing_values = False).getTiData()
    # create wc indicator (contains 'wc' column)
    wc_df = WeightedClose(input_data = data_df, fill_missing_values = False).getTiData()
    # create ws indicator (contains 'ws' column)
    ws_df = WildersSmoothing(input_data = data_df, fill_missing_values = False).getTiData()
    # create wad indicator (contains 'wad' column)
    wad_df = WilliamsAccumulationDistribution(input_data = data_df, fill_missing_values = False).getTiData()

    # create wr indicator (contains 'wr' column)
    wr_df = WilliamsR(input_data = data_df, fill_missing_values = False).getTiData()

    # merge indicators to data
    data_df = w2_mergeDataFrames(data_df, adl_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, atr_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, bb_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, cmf_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, co_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, cmo_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, dpo_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, dmi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, dema_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, eom_df, merge_column_str = 'date')

    data_df = w2_mergeDataFrames(data_df, env_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, fr_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, fo_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, ic_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, imi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, ko_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, lri_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, lrs_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, mfi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, mi_df, merge_column_str = 'date')

    data_df = w2_mergeDataFrames(data_df, mp_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, mom_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, ema_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, sma_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, tsma_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, tma_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, vma_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, macd_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, nvi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, obv_df, merge_column_str = 'date')

    data_df = w2_mergeDataFrames(data_df, psar_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, per_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, pvi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, pvt_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, pc_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, po_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, prc_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, pb_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, pro_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, qs_df, merge_column_str = 'date')

    data_df = w2_mergeDataFrames(data_df, ri_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, rmi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, rsi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, rvi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, sd_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, smi_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, sos_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, soe_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, si_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, tsf_df, merge_column_str = 'date')

    data_df = w2_mergeDataFrames(data_df, tema_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, tp_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, uo_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, vhf_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, vc_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, vo_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, vrc_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, wc_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, ws_df, merge_column_str = 'date')
    data_df = w2_mergeDataFrames(data_df, wad_df, merge_column_str = 'date')

    data_df = w2_mergeDataFrames(data_df, wr_df, merge_column_str = 'date')

    # ==== ==== ====

    # drop the specific columns as needed
    support_data_df = w2_dropColumns(
        df = support_data_df.reset_index(drop = False),
        column_list = ['date']
    )
    data_df = w2_dropColumns(
        df = data_df.reset_index(drop = False),
        column_list = ['date']
    )

    # keep track of columns
    feature_x_columns = list(data_df.columns.values)

    # ==== ==== ====

    # standardize the data
    # NOTE: Because principal components are meant to capture variation among existing variables, 
    # it is generally best practice to standardize all variables before implementing PCA so that 
    # everything is on the same scale. 
    feature_x_nparr = np.array([])
    if scaling_method_str == 'standard':
        # reference: https://scikit-learn.org/stable/modules/preprocessing.html#standardization-or-mean-removal-and-variance-scaling
        feature_x_nparr = w2_dropRowsWithInfResetIndex(
            df = w2_replaceNANWithValue(
                df = data_df,
                value = 0.0
            )
        ).values
        feature_x_nparr = StandardScaler(copy = False).fit_transform(feature_x_nparr)
    elif scaling_method_str == 'robust':
        # reference: https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html#sklearn.preprocessing.RobustScaler
        feature_x_nparr = w2_dropRowsWithInfResetIndex(
            df = w2_replaceNANWithValue(
                df = data_df,
                value = 0.0
            )
        ).values
        feature_x_nparr = RobustScaler(copy = False).fit_transform(feature_x_nparr)
    else:
        pass

    if dim_reduction_pca_on:
        # generate principal components and fit the model with x data
        # reference: https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html#sklearn.decomposition.PCA
        pca_obj = PCA(
            n_components = PCA_NUM_PRINCIPAL_COMPONENTS,
            copy = False
        )
        principal_components_nparr = pca_obj.fit_transform(feature_x_nparr)
        # generate columns list based on number of principal components desired
        columns_list = []
        for i in range(PCA_NUM_PRINCIPAL_COMPONENTS):
            columns_list.append(f'pc{i}')
        # generate dataframe out of array
        feature_x_df = w2_generateDataFrame(
            data = principal_components_nparr,
            columns_list = columns_list
        )

        if inspection_scree_plot_save_on:
            # import plotting function
            from utils.w2_plot import w2_plotQuickly

            # plot data
            w2_plotQuickly(
                x_data_arr = np.arange(pca_obj.n_components_) + 1,
                x_axis_label_str = 'Principal Component Number',
                y_data_arr_list = [pca_obj.explained_variance_ratio_],
                y_data_label_str_list = ['Principal Components'],
                y_axis_label_str = 'Principal Component Value',
                plot_title_str = f'Scree Plot | {PCA_NUM_PRINCIPAL_COMPONENTS} Components | Features from {ticker_str} Daily Data',
                save_on = True,
                save_file_name_str = f'ScreePlot_{ticker_str}',
                save_path_str = ROOT_PATH + 'reports/plots/',
                show_on = False
            )

    else:
        # generate dataframe out of array
        feature_x_df = w2_generateDataFrame(
            data = feature_x_nparr,
            columns_list = feature_x_columns
        )

    # clean, round and save features data
    # NOTE: Features data is saved for inspection purposes only.
    feature_x_df = w2_roundByDecimals(
        df = w2_dropRowsWithInfResetIndex(
            df = w2_castToPreferredDataType(
                df = feature_x_df,
                data_type = RAY_DATA_TYPE
            ),
        ),
        decimals_int = 8
    )
    if inspection_feature_data_save_on:
        w2_writeDataFrameToCSV(
            df = feature_x_df,
            file_path = ROOT_PATH + data_path_str + ticker_str + '.csv'
        )

    # clean support data
    support_data_df = w2_dropRowsWithInfResetIndex(
        df = w2_customCastToDataTypeByColumns(
            df = support_data_df
        )
    )
    
    return {ticker_str: feature_x_df, ticker_str + '_support': support_data_df}


def w1_if_deriveFeatures(
        tickers_str_list,
        data_path_str = 'data/features/',
        scaling_method_str = 'robust',
        dim_reduction_pca_on = PCA_DIM_REDUCTION,
        inspection_scree_plot_save_on = False,
        inspection_feature_data_save_on = False,
        simulated_on = True
):
    """
    Derive feature datasets for a list of tickers using parallel processing.

    This function downloads or loads historical data for each ticker, filters out
    insufficient data series, and then generates unit-level feature datasets in
    parallel using `w1_if_deriveUnitFeatures`.

    Parameters:
        tickers_str_list (list): List of ticker symbols to derive features for.
        data_path_str (str): Relative path where feature CSV files may be saved.
        scaling_method_str (str): Feature scaling method ('standard' or 'robust').
        dim_reduction_pca_on (bool): If True, apply PCA to reduce feature dimensionality.
        inspection_scree_plot_save_on (bool): Save PCA scree plot if True.
        inspection_feature_data_save_on (bool): Save feature CSV files if True.
        simulated_on (bool): Use simulated data sources when True.

    Returns:
        dict: Dictionary mapping each ticker to its derived feature DataFrame and
            the corresponding support DataFrame under ticker + '_support'.
    """
    data_dict = {}
    # derive historical prices (daily)
    # NOTE: no_stale_on is set to True because w1_if_deriveFeatures is used in trade_v#.py, and this is called after daily data is downloaded once.
    data_dict = w1_if_getHistoricalDataInThreadsMain(
        ticker_str_list = tickers_str_list,
        no_stale_on = True,
        simulated_on = simulated_on
    )

    # refine ticker data dictionary and ticker list and ensure that a data length of at least DATA_LENGTH_MIN (stage 1)
    refined_data_dict = {}
    for ticker_str in data_dict.keys():
        if data_dict[ticker_str] is None or len(data_dict[ticker_str]) == 0 or len(data_dict[ticker_str]) < TRADE_RECENT_DATA_CHUNK_RL_INFERENCE: # DATA_LENGTH_MIN
            pass
        else:
            refined_data_dict.update({ticker_str: data_dict[ticker_str]})

    # ^^^ apply assertion check to ensure refined data dictionary is not empty
    assert refined_data_dict
    
    # start the process pool
    features_data_dict = {}
    with ProcessPoolExecutor() as executor:
        # submit tasks and collect future objects
        futures = [
            executor.submit(
                w1_if_deriveUnitFeatures, 
                ticker_str, 
                refined_data_dict[ticker_str], 
                data_path_str, 
                scaling_method_str, 
                dim_reduction_pca_on, 
                inspection_scree_plot_save_on, 
                inspection_feature_data_save_on
            ) for ticker_str in refined_data_dict.keys()
        ]
        # process task results as they are available
        for future in as_completed(futures):
            result = future.result()
            features_data_dict.update(result)

    # refine features data dictionary and ensure that a data length of at least DATA_LENGTH_MIN (stage 2)
    refined_features_data_dict = {}
    for ticker_str in features_data_dict.keys():
        # check if dictionary contains data for the ticker and data length is sufficient
        if features_data_dict[ticker_str] is None or len(features_data_dict[ticker_str]) == 0 or len(features_data_dict[ticker_str]) < TRADE_RECENT_DATA_CHUNK_RL_INFERENCE: # DATA_LENGTH_MIN
            pass
        else:
            refined_features_data_dict.update({ticker_str: features_data_dict[ticker_str]})

    # ^^^ apply assertion check to ensure refined features data dictionary is not empty
    assert refined_features_data_dict

    return refined_features_data_dict


if __name__ == "__main__":
    # capture start time
    startTime = time.time()

    # execute the function on a list of 20 tickers
    tickers_str_list = ['NVDA', 'AAPL', 'MU', 'AMD', 'AVGO', 'TXN', 'T', 'KO', 'WMT', 'TSLA', 'LLY', 'STLA', 'F', 'GM', 'HMC', 'PLUG', 'LCID', 'ADBE', 'UBER', 'KLAC']
    refined_features_data_dict = w1_if_deriveFeatures(tickers_str_list = tickers_str_list)

    # display results
    print(refined_features_data_dict)

    # capture end time
    endTime = time.time()

    # display execution details
    print()
    print(f"INFO: Stress-test execution time for {len(tickers_str_list)} stocks: {endTime - startTime}")
    print()