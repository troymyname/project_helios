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

import json
import numpy as np
import pandas as pd


# ==== ==== generic functions


def w2_generateDataFrame(data, columns_list = None):
    """
        description:
            Constructs a pandas DataFrame from a dictionary or list-like input, optionally
            assigning explicit column names.
        args:
            data: dict or list-like
                Input data used to build the DataFrame.
            columns_list: list, default None
                Optional column names for the resulting DataFrame.
        returns:
            pandas.DataFrame
                The constructed DataFrame.
    """
    if columns_list is None:
        index = [0]
    else:
        index = None
    df = pd.DataFrame(data = data, index = index, columns = columns_list)

    return df


def w2_resetIndex(df):
    """
        description:
            Resets the index of a DataFrame while preserving the row order.
        args:
            df: pandas.DataFrame
                DataFrame whose index should be reset.
        returns:
            pandas.DataFrame
                A copy of the input DataFrame with a default integer index.
    """
    return df.reset_index()


def w2_readJSONToDataFrame(file_path):
    """
        description:
            Reads a JSON payload into a pandas DataFrame and resets the index.
        args:
            file_path: str
                Path to the JSON file.
        returns:
            pandas.DataFrame
                The parsed DataFrame.
    """
    with open(file_path, 'r') as f:
        df = pd.DataFrame(data = json.load(f)).dropna().reset_index(drop = True)
    return df


def w2_writeDataFrameToJSON(df, file_path):
    """
        description:
            Writes a DataFrame to a JSON file on disk.
        args:
            df: pandas.DataFrame
                DataFrame to serialize.
            file_path: str
                Destination file path.
        returns:
            None
    """
    with open(file_path, 'w') as f:
        pd.DataFrame(data = df).to_json(f)
    

def w2_readCSVToDataFrame(file_path, index_col_str = None):
    """
        description:
            Reads a CSV file into a pandas DataFrame, optionally using a column as the index.
        args:
            file_path: str
                Path to the CSV file.
            index_col_str: str, default None
                Optional column name to use as the DataFrame index.
        returns:
            pandas.DataFrame
                The loaded DataFrame.
    """
    with open(file_path, 'rb') as f:
        if index_col_str is not None:
            df = pd.read_csv(filepath_or_buffer = f, index_col = index_col_str)
        else:
            df = pd.read_csv(filepath_or_buffer = f)
    return df


def w2_writeDataFrameToCSV(df, file_path):
    """
        description:
            Writes a DataFrame to CSV format without preserving the index as a column.
        args:
            df: pandas.DataFrame
                DataFrame to serialize.
            file_path: str
                Destination file path.
        returns:
            None
    """
    df.to_csv(path_or_buf = file_path, index = False)
    

def w2_concatenateDataFramesInRows(df1, df2):
    """
        description:
            Appends two DataFrames vertically and resets the resulting index.
        args:
            df1: pandas.DataFrame
                First DataFrame.
            df2: pandas.DataFrame
                Second DataFrame.
        returns:
            pandas.DataFrame
                The concatenated DataFrame.
    """
    if len(df1) == 0:
        return df2
    elif len(df2) == 0:
        return df1
    else:
        return pd.concat(objs = [df1, df2], axis = 0, ignore_index = True)


def w2_concatenateDataFramesInColumns(df1, df2):
    """
        description:
            Appends two DataFrames horizontally along their columns.
        args:
            df1: pandas.DataFrame
                First DataFrame.
            df2: pandas.DataFrame
                Second DataFrame.
        returns:
            pandas.DataFrame
                The column-wise concatenated DataFrame.
    """
    if len(df1) == 0:
        return df2
    elif len(df2) == 0:
        return df1
    else:
        return pd.concat(objs = [df1, df2], axis = 1)
    

def w2_addNewColumnWithConstantData(df, column_str = 'col', data_str = 'data'):
    """
        description:
            Adds a new column filled with a constant value to an existing DataFrame.
        args:
            df: pandas.DataFrame
                DataFrame to update.
            column_str: str, default 'col'
                Name of the new column.
            data_str: str, default 'data'
                Constant value assigned to the new column.
        returns:
            pandas.DataFrame
                The updated DataFrame.
    """
    df[column_str] = data_str
    return df


def w2_dropRowsWithNAN(df):
    """
        description:
            Removes rows containing any missing values.
        args:
            df: pandas.DataFrame
                DataFrame to clean.
        returns:
            pandas.DataFrame
                A DataFrame without rows that contain NaN values.
        references:
            [1] https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.dropna.html
    """
    return df.dropna(
        axis = 0,
        how = 'any',
        inplace = False
    )


def w2_dropRowsWithEmptyCells(df):
    """
        description:
            Converts empty strings to NaN values and removes any rows that contain them.
        args:
            df: pandas.DataFrame
                DataFrame to clean.
        returns:
            pandas.DataFrame
                A cleaned DataFrame with empty-cell rows removed.
        references:
            [1] https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.dropna.html
    """
    for key in list(df.keys()):
        df[key].replace('', np.nan, inplace = True)
    return w2_dropRowsWithNAN(df)


def w2_dropRowsWithNANResetIndex(df):
    """
        description:
            Removes rows that contain missing values and resets the index of the result.
        args:
            df: pandas.DataFrame
                DataFrame to clean.
        returns:
            pandas.DataFrame
                A cleaned DataFrame with a fresh integer index.
        references:
            [1] https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.dropna.html
            [2] https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.reset_index.html
    """
    return df.dropna(
        axis = 0,
        how = 'any',
        inplace = False
    ).reset_index(
        drop = True,
        inplace = False
    )


def w2_dropRowsWithInfResetIndex(df):
    """
        description:
            Removes rows containing infinite or missing values and resets the index.
        args:
            df: pandas.DataFrame
                DataFrame to clean.
        returns:
            pandas.DataFrame
                A cleaned DataFrame with infinite values removed and the index reset.
        references:
            [1] https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.replace.html
    """
    return w2_dropRowsWithNANResetIndex(
        df = df.replace(
            to_replace = [np.inf, -np.inf],
            value = np.nan,
            inplace = False
        )
    )


def w2_dropRowsByIndices(df, indices_list):
    """
        description:
            Drops rows by their positional indices from a DataFrame.
        args:
            df: pandas.DataFrame
                DataFrame to filter.
            indices_list: list
                Row indices to remove.
        returns:
            pandas.DataFrame
                A filtered DataFrame with the selected rows removed.
        references:
            [1] https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop.html
    """
    return df.drop(
        axis = 0,
        index = indices_list,
        inplace = False
    )


def w2_extractColumns(df, column_list):
    """
        description:
            Returns a subset of columns from a DataFrame.
        args:
            df: pandas.DataFrame
                DataFrame to subset.
            column_list: list
                Names of the columns to keep.
        returns:
            pandas.DataFrame
                A DataFrame containing only the requested columns.
        references:
            [1] https://numpy.org/doc/stable/reference/arrays.scalars.html
    """
    return df[column_list]


def w2_dropColumns(df, column_list):
    """
        description:
            Removes one or more columns from a DataFrame.
        args:
            df: pandas.DataFrame
                DataFrame to update.
            column_list: list
                Column names to drop.
        returns:
            pandas.DataFrame
                A DataFrame without the specified columns.
        references:
            [1] https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop.html
    """
    return df.drop(
        columns = column_list,
        inplace = False
    )


def w2_mergeDataFrames(df1, df2, merge_column_str):
    """
        description:
            Merges two DataFrames on a shared column or, when that fails, on their indexes.
        args:
            df1: pandas.DataFrame
                Left DataFrame.
            df2: pandas.DataFrame
                Right DataFrame.
            merge_column_str: str
                Column name used for the merge attempt.
        returns:
            pandas.DataFrame
                The merged DataFrame.
        references:
            [1] https://numpy.org/doc/stable/reference/arrays.scalars.html
    """
    if len(df1) == 0:
        return df2
    elif len(df2) == 0:
        return df1
    else:
        try:
            # merge on column name
            return pd.merge(
                left = df1,
                right = df2,
                on = merge_column_str
            )
        except KeyError:
            # merge on both join keys from both right and left dataframes
            return pd.merge(
                left = df1,
                right = df2,
                how = 'outer',
                left_index = True,
                right_index = True
            )


def w2_calculatePercentageChange(df):
    """
        description:
            Calculates percentage changes between successive rows in a DataFrame.
        args:
            df: pandas.DataFrame
                Input DataFrame of numeric values.
        returns:
            pandas.DataFrame
                A DataFrame of percentage-change values.
    """
    return df.pct_change(periods = 1)


def w2_calculateRollingWindowMinMax(one_column_df, type_str, window_int, min_periods_int = 1):
    """
        description:
            Computes rolling minimum or maximum values over a window for a single column.
        args:
            one_column_df: pandas.DataFrame or pandas.Series
                Series-like input data.
            type_str: str
                Either 'min' or 'max' to select the rolling operation.
            window_int: int
                Rolling window size.
            min_periods_int: int, default 1
                Minimum number of observations required for a valid result.
        returns:
            pandas.DataFrame or pandas.Series
                The rolling min/max output.
    """
    if type_str == 'min':
        return one_column_df.rolling(window = window_int, min_periods = min_periods_int).min()
    elif type_str == 'max':
        return one_column_df.rolling(window = window_int, min_periods = min_periods_int).max()
    else:
        return 0


def w2_replaceNANWithValue(df, value = 0.0):
    """
        description:
            Replaces NaN values in a DataFrame with a provided scalar.
        args:
            df: pandas.DataFrame
                DataFrame to clean.
            value: float, default 0.0
                Replacement value for NaN entries.
        returns:
            pandas.DataFrame
                A DataFrame with NaN values replaced.
        references:
            [1] https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.replace.html
    """
    return df.replace(
        to_replace = np.nan,
        value = value,
        inplace = False
    )


def w2_renameColumns(df, column_mapping_dict):
    """
        description:
            Renames DataFrame columns using a mapping dictionary.
        args:
            df: pandas.DataFrame
                DataFrame to update.
            column_mapping_dict: dict
                Mapping from old column names to new names.
        returns:
            pandas.DataFrame
                The renamed DataFrame.
        references:
            [1]
    """
    return df.rename(
        columns = column_mapping_dict,
        inplace = False
    )


def w2_setColumnAsIndex(df, column_to_index_name_str, drop_column = True):
    """
        description:
            Sets a specified column as the index of a DataFrame.
        args:
            df: pandas.DataFrame
                DataFrame to update.
            column_to_index_name_str: str
                Column name to use as the new index.
            drop_column: bool, default True
                Whether to remove the column from the DataFrame after setting it as the index.
        returns:
            pandas.DataFrame
                The DataFrame with the requested column as its index.
        references:
            [1]
    """
    return df.set_index(
        keys = column_to_index_name_str,
        drop = drop_column,
        inplace = False
    )


def w2_keepOnlySelectedColumns(df, selected_columns_str_list):
    """
        description:
            Keeps only the specified columns and validates that each is present.
        args:
            df: pandas.DataFrame
                DataFrame to filter.
            selected_columns_str_list: list
                Column names to retain.
        returns:
            pandas.DataFrame
                A DataFrame limited to the selected columns.
        references:
            [1]
    """
    for column_str in selected_columns_str_list:
        assert column_str in list(df.columns)
    return df[selected_columns_str_list]


def w2_castToPreferredDataType(df, data_type):
    """
        description:
            Casts the DataFrame to a preferred pandas data type.
        args:
            df: pandas.DataFrame
                DataFrame to convert.
            data_type: type
                The target dtype to apply.
        returns:
            pandas.DataFrame
                The casted DataFrame.
        references:
            [1] https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.astype.html
    """
    return df.astype(
        dtype = data_type,
        copy = True
    )


def w2_roundByDecimals(df, decimals_int):
    """
        description:
            Rounds numeric values in a DataFrame to the requested precision.
        args:
            df: pandas.DataFrame
                DataFrame to round.
            decimals_int: int
                Number of decimal places to retain.
        returns:
            pandas.DataFrame
                The rounded DataFrame.
        references:
            [1] https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.round.html
    """
    return df.round(decimals = decimals_int)


# ==== ==== custom functions


def w2_customCastToDataTypeByColumns(df):
    """
        description:
            Applies a custom dtype conversion to OHLCV-style columns for consistency.
        args:
            df: pandas.DataFrame
                DataFrame to transform.
        returns:
            pandas.DataFrame
                The DataFrame with columns cast to the preferred numeric types.
        references:
            [1] https://numpy.org/doc/stable/reference/arrays.scalars.html
    """
    df = df.astype({
        'open': np.float32,
        'high': np.float32,
        'low': np.float32,
        'close': np.float32,
        'volume': np.uint32
        })

    return df


def w2_customConvertDateToDatetime(df):
    """
        description:
            Converts the date column to a pandas datetime type using a small set of common formats.
        args:
            df: pandas.DataFrame
                DataFrame containing a date-like column.
        returns:
            pandas.DataFrame
                The DataFrame with the date column converted to datetime values.
        notes:
            TODO: A better way needs to be found eventually.
    """
    try:
        df['date'] = pd.to_datetime(
            df['date'],
            format = '%Y%m%d'
        )
    except ValueError:
        try:
            df['date'] = pd.to_datetime(
                df['date'],
                format = '%Y-%m-%d'
            )
        except ValueError:
            try:
                df['date'] = pd.to_datetime(
                    df['date'],
                    format = '%Y%m%d %H:%M:%S'
                )
            except ValueError:
                try:
                    df['date'] = pd.to_datetime(
                        df['date'],
                        format = '%Y-%m-%d %H:%M:%S'
                    )
                except ValueError:
                    try:
                        df['date'] = pd.to_datetime(
                            df['date'],
                            format = '%Y%m%d %H:%M:%S America/Detroit'
                        )
                    except ValueError:
                        try:
                            df['date'] = pd.to_datetime(
                                df['date'],
                                format = '%Y%m%d %H:%M:%S America/New_York'
                            )
                        except ValueError:
                            df['date'] = pd.to_datetime(
                                df['date'],
                                format = '%Y%m%d %H:%M:%S US/Eastern'
                            )

    return df


def w2_customFillForward(df, interval_str):
    """
        description:
            Sorts the DataFrame by date, sets the date column as the index, and forward-fills
            missing values at a daily, hourly, or minutely interval.
        args:
            df: pandas.DataFrame
                DataFrame containing a date column and one or more numeric values.
            interval_str: str
                Time interval string such as '1d', '1h', or '1m'.
        returns:
            pandas.DataFrame
                The forward-filled DataFrame with a datetime index.
    """
    # convert 'date' column to datetime format, sort, set index to 'date', and fill gaps using forward strategy
    if interval_str == '1d':
        df = df.sort_values(by = ['date']).set_index('date')
        df = df.resample('D').first().ffill()
    elif interval_str == '1h':
        df = df.sort_values(by = ['date']).set_index('date')
        df = df.resample('h').first().ffill()
    elif interval_str == '1m':
        df = df.sort_values(by = ['date']).set_index('date')
        df = df.resample('min').first().ffill()
    else:
        print("ERROR: ...")
        return 0

    return df