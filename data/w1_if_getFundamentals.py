# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] athena_generateSECCCompanyStatusReport.ipynb
# ------------------------------------------------------------------------------

# import dependencies
import sys
sys.path.append("..")

import pandas as pd
import requests

from time import sleep

# import custom configs and utils
from config import ROOT_PATH, WAIT_TIME_POINT_ONE
from utils.w2_performDataFrameOps import w2_writeDataFrameToCSV
from utils.w2_returnUpperLettersFromString import w2_returnUpperLettersFromString


def w1_if_requestData(
        cik_str,
        account_type_str,
        variable_name_str,
        request_head_str = 'tonmoyroy@duck.com'
):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # construct request head
    request_head_dict = {'User-Agent': request_head_str}

    # make request
    if str(account_type_str) == 'gaap':
        return requests.get(
            url = 'https://data.sec.gov/api/xbrl/companyconcept/' + 'CIK' + cik_str + '/us-gaap/' + variable_name_str + '.json',
            headers = request_head_dict
        )
    elif str(account_type_str) == 'ifrs':
        return requests.get(
            url = 'https://data.sec.gov/api/xbrl/companyconcept/' + 'CIK' + cik_str + '/ifrs-full/' + variable_name_str + '.json',
            headers = request_head_dict
        )
    else:
        return 0


def w1_if_processResponse(
        response_obj,
        ticker_str,
        save_suffix_str,
        data_path_str
):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # derive currency units
    currency_unit_str = 'USD'
    currency_unit_list = list(response_obj.json()['units'].keys())
    if len(currency_unit_list) == 1:
        currency_unit_str = str(currency_unit_list[0])
    else:
        for item in currency_unit_list:
            if str(item) == 'USD':
                currency_unit_str = item
                break
            else:
                currency_unit_str = str(currency_unit_list[0])

    # derive data
    try:
        data_df = pd.json_normalize(response_obj.json()['units'][currency_unit_str])
        data_df['filed'] = pd.to_datetime(data_df['filed'])
        data_df = data_df.sort_values('end')
    except KeyError:
        try:
            data_df = pd.json_normalize(response_obj.json()['units'][currency_unit_str + '/shares'])
            data_df['filed'] = pd.to_datetime(data_df['filed'])
            data_df = data_df.sort_values('end')
        except KeyError:
            data_df = pd.json_normalize(response_obj.json()['units']['shares'])
            data_df['filed'] = pd.to_datetime(data_df['filed'])
            data_df = data_df.sort_values('end')
    # save fundamentals data
    w2_writeDataFrameToCSV(
        df = data_df,
        file_path = ROOT_PATH + data_path_str + ticker_str + '_' + save_suffix_str + '.csv'
    )

    return data_df


def w1_if_getFundamentals(
        ticker_str,
        variable_name_str_list,
        request_head_str = 'tonmoyroy@duck.com',
        safe_mode_on = True,
        data_path_str = 'data/fundamentals/'
):
    """
        description:
            A function/class that ...
        args:
            ...
        returns:
            ...
    """
    # construct request head
    request_head_dict = {'User-Agent': request_head_str}

    # make request to get CIK JSON response and pre-process
    response_obj1 = requests.get(
        url = 'https://www.sec.gov/files/company_tickers.json',
        headers = request_head_dict
    )
    response_obj1 = pd.json_normalize(
        pd.json_normalize(
            response_obj1.json(),
            max_level = 0
        ).values[0]
    )
    response_obj1['cik_str'] = response_obj1['cik_str'].astype(str).str.zfill(10)
    response_obj1.set_index(keys = 'ticker', inplace = True)

    # take a break between requests
    sleep(WAIT_TIME_POINT_ONE)

    # make request(s) to get (a list of available variable names and) required variable data
    variable_data_dict = {
        ticker_str: {}
    }
    for i in range(len(response_obj1)):
        if str(response_obj1.index[i]) == ticker_str:
            # derive CIK
            cik_str = str(response_obj1['cik_str'].iloc[i])
            ticker_title_str = str(response_obj1['title'].iloc[i])

            # store title in dictionary
            variable_data_dict[ticker_str].update(
                {
                    'title': ticker_title_str
                }
            )

            # NOTE: With this option, an extra request is made to first derive the list of available variable names.
            if safe_mode_on:
                # derive a list of available variable names
                try:
                    variable_list = (
                        requests.get(
                            url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK'+ cik_str + '.json',
                            headers = request_head_dict
                        )
                    ).json()['facts']['us-gaap'].keys()
                    variable_list = list(variable_list)
                except (KeyError, requests.exceptions.JSONDecodeError):
                    try:
                        variable_list = (
                            requests.get(
                                url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + cik_str + ".json",
                                headers = request_head_dict
                            )
                        ).json()['facts']['ifrs-full'].keys()
                        variable_list = list(variable_list)
                    except (KeyError, requests.exceptions.JSONDecodeError):
                        # gracefully set variable_list to empty list
                        variable_list = []

                # take a break between requests
                sleep(WAIT_TIME_POINT_ONE)

                # derive required variable data
                if variable_list:
                    for variable_name_str in variable_name_str_list:
                        if variable_name_str in variable_list:
                            response_obj2 = w1_if_requestData(
                                cik_str = cik_str,
                                account_type_str = 'gaap',
                                variable_name_str = variable_name_str
                            )
                            if int(response_obj2.status_code) != 200:
                                response_obj2 = w1_if_requestData(
                                    cik_str = cik_str,
                                    account_type_str = 'ifrs',
                                    variable_name_str = variable_name_str
                                )

                            # process response and store response in dictionary
                            variable_data_dict[ticker_str].update(
                                {
                                    variable_name_str: w1_if_processResponse(
                                        response_obj = response_obj2,
                                        ticker_str = ticker_str,
                                        save_suffix_str = w2_returnUpperLettersFromString(variable_name_str),
                                        data_path_str = data_path_str
                                    )
                                }
                            )
                            
                else:
                    variable_data_dict = {}
            
            # NOTE: With this option, it is assumed that certain variables will be present in the request.
            else:
                for variable_name_str in variable_name_str_list:
                    response_obj2 = w1_if_requestData(
                        cik_str = cik_str,
                        account_type_str = 'gaap',
                        variable_name_str = variable_name_str
                    )
                    if int(response_obj2.status_code) != 200:
                        response_obj2 = w1_if_requestData(
                            cik_str = cik_str,
                            account_type_str = 'ifrs',
                            variable_name_str = variable_name_str
                        )

                    # process response and store response in dictionary
                    variable_data_dict[ticker_str].update(
                        {
                            variable_name_str: w1_if_processResponse(
                                response_obj = response_obj2,
                                ticker_str = ticker_str,
                                save_suffix_str = w2_returnUpperLettersFromString(variable_name_str),
                                data_path_str = data_path_str
                            )
                        }
                    )

            # break out of loop
            break

    return variable_data_dict


if __name__ == '__main__':
    # specify ticker symbol
    symbol_str = 'TSLA'

    data_dict = w1_if_getFundamentals(
        ticker_str = symbol_str,
        variable_name_str_list = ['EarningsPerShareBasic']
    )
    print(data_dict[symbol_str]['EarningsPerShareBasic'])