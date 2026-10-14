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


def w2_readJSON(json_path_str):
    """
        description:
            Reads a JSON file from disk and returns its contents as a Python dictionary.
        args:
            json_path_str: str
                Path to the JSON file to load.
        returns:
            dict
                The parsed JSON data.
    """
    data_dict = {}
    with open(json_path_str, 'r') as file:
        data_dict = json.load(file)

    return data_dict


def w2_readJSONIteratively(json_path_str):
    """
        description:
            Reads a JSON file line by line and returns each JSON object as a separate entry
            in a list. This is useful for files that contain multiple JSON documents.
        args:
            json_path_str: str
                Path to the JSON file to read.
        returns:
            list
                A list of parsed JSON objects from the file.
    """
    data_dict_list = []
    with open(json_path_str, 'r') as file:
        for portion in file:
            data_dict_list.append(json.loads(portion))

    return data_dict_list


def w2_writeToJSON(data_dict, json_path_str):
    """
        description:
            Writes a Python dictionary to disk as a formatted JSON file.
        args:
            data_dict: dict
                The dictionary to serialize to JSON.
            json_path_str: str
                Destination path for the JSON file.
        returns:
            None
    """
    with open(json_path_str, 'w') as file:
        json.dump(data_dict, file, indent = 4)