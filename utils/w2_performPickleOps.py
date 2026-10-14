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

import pickle


def w2_writePickle(data, file_path):
    """
        description:
            Serializes a Python object to disk using the pickle format.
        args:
            data: object
                The Python object to persist.
            file_path: str
                Destination file path for the serialized object.
        returns:
            None
    """
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def w2_readPickle(file_path):
    """
        description:
            Loads a previously pickled Python object from disk.
        args:
            file_path: str
                Path to the pickle file to read.
        returns:
            object
                The deserialized Python object stored in the file.
    """
    with open(file_path, 'rb') as f:
        data = pickle.load(f)

    return data