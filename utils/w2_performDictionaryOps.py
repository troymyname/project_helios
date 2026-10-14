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


def w2_appendToDictionary(data_dict: dict, new_data_dict: dict):
    """
        description:
            Updates a dictionary in place by merging the contents of another dictionary.
        args:
            data_dict: dict
                The dictionary to update.
            new_data_dict: dict
                The dictionary whose key-value pairs should be merged into `data_dict`.
        returns:
            None
                The function mutates `data_dict` in place and returns the result of `dict.update`.
    """
    return data_dict.update(new_data_dict)


def w2_recursivelyConvertFloatToString(data_unknown):
    """
        description:
            Recursively converts nested values to strings so they can be safely serialized to JSON.
            This is particularly useful for values such as NumPy float32 scalars that are not
            directly JSON serializable.
        args:
            data_unknown: object
                A nested dictionary or scalar value to convert.
        returns:
            dict or str
                A recursively converted dictionary or a string representation of the input value.
    """
    data_dict = {}
    if isinstance(data_unknown, dict):
        # iterate through the keys and recursively call function
        for key in data_unknown.keys():
            data_dict.update({key: w2_recursivelyConvertFloatToString(data_unknown[key])})
        return data_dict
    else:
        # return in string format to avoid errors related to float32 not being json serializable if json.dumps is used later down the pipeline
        return str(data_unknown)


def w2_filterDictionary(data_dict, allowed_types_tpl = (), allowed_types_strict_tpl = (), allowed_types_strict_size_bytes_int = None):
    """
        description:
            Filters the contents of a dictionary based on allowed types and optional size constraints.
            Values that match the relaxed allowed-type criteria are kept as-is, while values that match
            the strict-type criteria and fit the size threshold are converted to strings for safer serialization.
        args:
            data_dict: dict
                The dictionary to filter.
            allowed_types_tpl: tuple, default ()
                Tuple of acceptable types to retain directly.
            allowed_types_strict_tpl: tuple, default ()
                Tuple of types that should be retained only if they also satisfy the size constraint.
            allowed_types_strict_size_bytes_int: int, default None
                Maximum allowed size in bytes for values in the strict-type filter.
        returns:
            dict
                A filtered dictionary containing the retained key-value pairs.
    """
    new_data_dict = {}
    for _, key in enumerate(data_dict):
        # filter by allowed types
        if isinstance(data_dict[key], allowed_types_tpl):
            new_data_dict.update({key: data_dict[key]})
        # filter by strict types based on size of the object
        if isinstance(data_dict[key], allowed_types_strict_tpl) and allowed_types_strict_size_bytes_int is not None:
            if sys.getsizeof(data_dict[key]) <= allowed_types_strict_size_bytes_int:
                new_data_dict.update({key: w2_recursivelyConvertFloatToString(data_dict[key])})

    return new_data_dict


def w2_writeDictionaryToJSON(data_dict, save_path_str):
    """
        description:
            Writes a dictionary to disk as a formatted JSON file.
        args:
            data_dict: dict
                The dictionary to serialize.
            save_path_str: str
                Destination path where the JSON file should be written.
        returns:
            None
    """
    with open(save_path_str, 'w') as write_obj:
        json.dump(data_dict, write_obj, indent = 4)