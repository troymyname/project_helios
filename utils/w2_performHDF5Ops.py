# ----// HEADER // -------------------------------------------------------------
# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://docs.h5py.org/en/latest/strings.html
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import h5py
import os


def w2_writeDataToHDF5(save_path_str, data_shape_tpl, data_list, data_name_str = 'default'):
    """
        description:
            Writes a list-like dataset to an HDF5 file using variable-width string storage.
        args:
            save_path_str: str
                Path where the HDF5 file should be created.
            data_shape_tpl: tuple
                Shape descriptor for the dataset.
            data_list: list
                Values to persist in the HDF5 file.
            data_name_str: str, default 'default'
                Name of the dataset inside the HDF5 file.
        returns:
            None
        references:
            [1] https://docs.h5py.org/en/latest/strings.html
    """
    with h5py.File(name = save_path_str, mode = 'w') as f:
        # save data using NumPy variable-width string dtypes, also known as NpyStrings
        f.create_dataset(
            name = data_name_str,
            shape = data_shape_tpl,
            dtype = h5py.string_dtype(),
            data = data_list
        )


def w2_readDataFromHDF5(save_path_str, data_name_str = 'default'):
    """
        description:
            Reads a dataset from an HDF5 file and returns it as a Python list.
            If the target file does not yet exist, an empty dataset is created and returned.
        args:
            save_path_str: str
                Path to the HDF5 file to read from.
            data_name_str: str, default 'default'
                Name of the dataset inside the HDF5 file.
        returns:
            list
                The dataset contents as a list of strings or empty values.
        references:
            [1] https://docs.h5py.org/en/latest/strings.html
    """
    if os.path.isfile(save_path_str):
        # read an existing data file and convert to list
        # NOTE: astype('T') is used because the goal is to read an array of native variable-width NumPy strings.
        with h5py.File(name = save_path_str, mode = 'r') as f:
            data_unknown = list(f[data_name_str].astype('T'))
        return data_unknown

    else:
        # create an empty data list and save
        data_list = []
        w2_writeDataToHDF5(
            save_path_str = save_path_str,
            data_shape_tpl = (0,),
            data_list = data_list,
            data_name_str = data_name_str
        )
        return data_list