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

from utils.w2_performDataFrameOps import w2_renameColumns


def w2_preprocessIBKRResponseDataFrame(df):
    """
    description:
        Standardizes the column names of a DataFrame returned by IBKR so it can be used
        consistently by the rest of the trading pipeline. The function renames common
        OHLCV-style columns such as 'Date', 'Open', 'High', 'Low', 'Close', and 'Volume'
        to the lowercase names expected by the project utilities.
    args:
        df: pandas.DataFrame
            DataFrame containing IBKR response data with one or more of the standard
            OHLCV column names.
    returns:
        pandas.DataFrame
            The input DataFrame with recognized IBKR columns renamed to the project's
            canonical lowercase names. Columns that are not present are left unchanged.
    """
    if 'Date' in list(df.columns):
        df = w2_renameColumns(
            df = df,
            column_mapping_dict = {'Date': 'date'}
        )
    if 'Open' in list(df.columns):
        df = w2_renameColumns(
            df = df,
            column_mapping_dict = {'Open': 'open'}
        )
    if 'High' in list(df.columns):
        df = w2_renameColumns(
            df = df,
            column_mapping_dict = {'High': 'high'}
        )
    if 'Low' in list(df.columns):
        df = w2_renameColumns(
            df = df,
            column_mapping_dict = {'Low': 'low'}
        )
    if 'Close' in list(df.columns):
        df = w2_renameColumns(
            df = df,
            column_mapping_dict = {'Close': 'close'}
        )
    if 'Volume' in list(df.columns):
        df = w2_renameColumns(
            df = df,
            column_mapping_dict = {'Volume': 'volume'}
        )

    return df