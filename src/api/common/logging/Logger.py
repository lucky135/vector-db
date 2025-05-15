"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

import logging
import inspect
import traceback
from logging.handlers import TimedRotatingFileHandler


class Logger:
    """
    Class to handle log messages.
    """

    def __init__(self, name=None, log_file=None):
        self.logger = logging.getLogger(name)
        # self.log_file = log_file
        self._configure_logging()

    def _configure_logging(self):
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add timeroating file handler with daily rollover
        # file_handler = TimedRotatingFileHandler(
        #    self.log_file, when="midnight", interval=1, backupCount=7
        # )
        # file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        # self.logger.addHandler(file_handler)

    def _get_method_name(self):
        return inspect.stack()[2].function

    def _get_class_name(self):
        return inspect.stack()[2].filename

    def _get_line_number(self):
        return inspect.stack()[2].lineno

    def log_stack_trace(self, exc_traceback=None):
        if exc_traceback:
            exc_frames = traceback.extract_tb

    def log_stack_trace(self, exc_traceback=None):
        if exc_traceback:
            exc_frames = traceback.extract_tb(exc_traceback)
            stack_frames = traceback.extract_stack(limit=6)[:-1]
            frames = exc_frames + stack_frames
        else:
            frames = traceback.extract_stack(limit=6)[:-1]

        log_message = "Stack trace:\n"

        for frame in frames:
            filename = frame.filename
            lineno = frame.lineno
            name = frame.name

            class_name = filename.split("/")[-1].replace(".py", "")

            log_message = f"{class_name}: {name}: Line {lineno}\n"

        self.logger.error(log_message)

    def debug(self, message):
        class_name = self._get_class_name()
        method_name = self._get_method_name
        line_number = self._get_line_number

        self.logger.debug(f"{class_name}:{method_name}:({line_number}): {message}")

    def info(self, message):
        class_name = self._get_class_name()
        method_name = self._get_method_name
        line_number = self._get_line_number

        self.logger.info(f"{class_name}:{method_name}:({line_number}): {message}")

    def warning(self, message):
        class_name = self._get_class_name()
        method_name = self._get_method_name
        line_number = self._get_line_number

        self.logger.warning(f"{class_name}:{method_name}:({line_number}): {message}")

    def error(self, message, exc_traceback=None):
        if exc_traceback is None:
            class_name = self._get_class_name()
            method_name = self._get_method_name
            line_number = self._get_line_number

            self.logger.error(f"{class_name}:{method_name}:({line_number}): {message}")

        else:
            frames = traceback.extract_tb(exc_traceback)
            last_frame = frames[-1]
            file_name = last_frame.filename
            line_number = last_frame.lineno
            function_name = last_frame.name

            self.logger.error(f"{file_name}:{function_name}:({line_number}): {message}")
            self.log_stack_trace(exc_traceback)

    def critical(self, message):
        class_name = self._get_class_name
        method_name = self._get_method_name
        line_number = self._get_line_number

        self.logger.warning(f"{class_name}:{method_name}:({line_number}): {message}")


# Create a global logger object
log = Logger()
