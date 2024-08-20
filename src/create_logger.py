"""
This file contains function to easy create programming loggers and alarm loggers.

Version: 0.9.0 First Stable Beta Release
"""

__version__ = "0.9.0"
__author__ = "Roberts Balulis, robert.balulis@hotmail.com"


import logging
import logging.handlers
import os
import sys

def setup_logger(logger_name:str) -> logging.Logger:

    """
    Creates and configures a logging instance for the specified module.

    This function creates a logger with the provided logger_name, sets its level to DEBUG,
    and associates it with a file handler that writes to a log file. The log file is stored
    in a 'logs' directory or 'alarms' directory depending on the logger_name.

    This will create a logger that writes messages to the 'module_name.log' file in the 'logs'
    directory. If the logger_name is 'alarms', it will write to the 'alarms' directory instead.

    Args:
        logger_name (str): The name of the logger to be created.

    Usage for programming logs:
    ----------
    >>> logger = setup_logger(__name__)

    Usage for alarm logs:
    ----------
    >>> logger = setup_logger("alarms")
    """

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        if getattr(sys, 'frozen', False): # If the program is running in a PyInstaller bundle
            app_path = sys._MEIPASS # Ignore the warning, its valid
            parent_dir = os.path.dirname(app_path)
        else:
            app_path = os.path.dirname(os.path.abspath(__file__)) # Else the program is running in a normal Python environment
            parent_dir = os.path.dirname(app_path)

        log_folder = "logs" if logger_name != "alarms" else "alarms"
        log_dir = os.path.abspath(os.path.join(parent_dir, log_folder))
        try:
            os.makedirs(log_dir, exist_ok=True)
        except PermissionError:
            print(f"Permission denied to create log directory: {log_dir}")
            sys.exit(1)
        log_file_path = os.path.join(log_dir, f"{logger_name}.log")

        formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s', datefmt='%Y:%m:%d %H:%M:%S')

        maxBytes = 10 * 1024 * 1024  # 10MB
        backupCount = 3

        file_handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=maxBytes, backupCount=backupCount)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        logger.addHandler(file_handler)

    return logger