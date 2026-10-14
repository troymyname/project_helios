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

import logging

from datetime import datetime

# import custom configs and utils
from config import PROGRAM_NAME
from config import ROOT_PATH


class CustomLogger:
    def __init__(self, debug_on):
        """
            description:
                Initializes the logger configuration and storage path for the current project.
            args:
                debug_on: bool
                    Whether the logger should emit debug-level messages.
            returns:
                None
        """
        self.debug_on = debug_on
        self.logger_name_str = PROGRAM_NAME
        self.logs_path_str = ROOT_PATH + 'logs/'

    @staticmethod
    def w2_generateLogFileName():
        """
            description:
                Returns the current date string used as the log filename suffix.
            args:
                None
            returns:
                str
                    The date string formatted as YYYY-MM-DD.
        """
        return datetime.strftime(datetime.today(), '%Y-%m-%d')

    def w2_generateCustomLogger(
            self,
            default_format_str = r'%(asctime)s: %(levelname)s: %(message)s',
            time_format_str = r'%Y-%m-%d %H:%M:%S'
    ):
        """
            description:
                Builds and configures a Python logger that writes to both the console and
                a date-stamped log file for the current session.
            args:
                default_format_str: str, default '%(asctime)s: %(levelname)s: %(message)s'
                    Formatting pattern for regular log output.
                time_format_str: str, default '%Y-%m-%d %H:%M:%S'
                    Date/time format used in log entries.
            returns:
                logging.Logger
                    The configured logger instance.
        """
        # configure logging with specified name
        custom_logger_obj = logging.getLogger(self.logger_name_str)
        if self.debug_on:
            custom_logger_obj.setLevel(level = logging.DEBUG)
        else:
            custom_logger_obj.setLevel(level = logging.INFO)

        # construct message formatter string
        if self.debug_on:
            formatter_str = logging.Formatter(
                fmt = r'%(asctime)s: %(levelname)s: %(filename)s: %(module)s: %(funcName)s: %(lineno)d: %(message)s',
                datefmt = time_format_str,
                style = '%'
            )
        else:
            formatter_str = logging.Formatter(
                fmt = default_format_str,
                datefmt = time_format_str,
                style = '%'
            )

        # configure console handler object
        console_handler_obj = logging.StreamHandler()
        if self.debug_on:
            console_handler_obj.setLevel(logging.DEBUG)
        else:
            console_handler_obj.setLevel(logging.INFO)
        console_handler_obj.setFormatter(formatter_str)

        # configure file handler object
        file_handler_obj = logging.FileHandler(
            filename = self.logs_path_str + self.w2_generateLogFileName() + '.log',
            mode = 'a',
            encoding = 'utf-8'
        )
        file_handler_obj.setFormatter(formatter_str)

        # add handlers to custom logger
        custom_logger_obj.addHandler(console_handler_obj)
        custom_logger_obj.addHandler(file_handler_obj)

        # print starting message
        custom_logger_obj.info('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
        custom_logger_obj.info('---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
        custom_logger_obj.info('Started log on {}...'.format(datetime.strftime(datetime.today(), '%Y-%m-%d')))

        return custom_logger_obj