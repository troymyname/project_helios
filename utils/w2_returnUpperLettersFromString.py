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


def w2_returnUpperLettersFromString(sample_str):
    """
        description:
            Extracts and returns the uppercase letters contained in a string while preserving
            their original order.
        args:
            sample_str: str
                Input string to scan.
        returns:
            str
                A string containing only uppercase characters found in the input.
    """
    upper_letters_str = ''
    for char in sample_str:
        if char.isupper():
            upper_letters_str = upper_letters_str + char
    return upper_letters_str