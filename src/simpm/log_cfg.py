"""Configure logging for SimPM.

The module exposes a shared :data:`logger` and the :class:`LogConfig` helper
to tweak console/file logging for the ``simpm`` package.

Logging levels
==============
* ``logging.DEBUG`` = 10
* ``logging.INFO`` = 20
* ``logging.WARNING`` = 30
* ``logging.ERROR`` = 40
* ``logging.CRITICAL`` = 50
"""
from __future__ import annotations
import logging
import colorlog

class LogConfig:
    """
    `LogConfig` is a class that allows developers to configure logging settings. It can be used to set parameters such as log output destination, log level, and log formatting. LogConfig provides a way to customize the logging behavior of an application based on specific requirements.
    """
    # Class level variable to hold the last instance created
    _last_instance = None
    
    # Define a custom filter to check if logging is enabled
    class _LoggingEnabledFilter(logging.Filter):
        def __init__(self, log_instance:LogConfig):
            super().__init__()
            self.log_instance = log_instance

        def filter(self, record):
            return self.log_instance.enabled
        
    def __init__(self, enabled=False, console_level=logging.DEBUG, file_level=logging.DEBUG,
                 file_path='simpm.log'):

        self.enabled = enabled
        """This boolean property indicates whether the feature is enabled or disabled."""

        # simpm logger instance
        self._logger = logging.getLogger("simpm")
        self._clear_existing_handlers()

        self._console_level = console_level
        self._file_level = file_level
        self._file_path = file_path

        # Configure the logger to write to the console
        self._console_handler = logging.StreamHandler()

        # Configure the logger to write to a file only when enabled and a file path is provided
        self._file_handler = None
        if self.enabled and self._file_path:
            self._file_handler = logging.FileHandler(self.file_path)

        self._configure_logger()
        LogConfig._last_instance = self

    def _clear_existing_handlers(self) -> None:
        """Remove handlers from the shared logger to prevent duplicates across instances."""
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)
            handler.close()
    
    @property
    def logger(self) -> logging.Logger:
        """This property holds a `logging.Logger` object which can be used to log messages."""
        return self._logger

    @property
    def console_level(self) -> int:
        """This property is used to get the console level as an integer."""
        return self._console_level

    @console_level.setter
    def console_level(self, value) -> None:
        """ 
        Setter to set the console_level variable. 
        Args: 
            value (int): The level to be assigned to the console handler. 
        Raises: 
            None 
        """
        self._console_level = value
        self._console_handler.setLevel(value)

    @property
    def file_level(self) -> int:
        """This property gets the file level of the instance."""
        return self._file_level

    @file_level.setter
    def file_level(self,value) -> None:
        """Setter function to set the log level of the file handler.
        Args: 
        value (int): Level of the log message to be recorded.
        example: `logging.DEBUG`
        """
        self._file_level = value
        if self._file_handler:
            self._file_handler.setLevel(value)

    @property
    def file_path(self) -> str:
        """Return the file path"""
        return self._file_path

    def _configure_logger(self):
        """This function configures a logger to allow for logging of messages from the application."""
        # Set the logger level to include all levels
        self.logger.setLevel(logging.DEBUG)

        # logging enabled filter
        filt = self._LoggingEnabledFilter(self)

        # Configure the logger to write to the console
        console_handler = self._console_handler
        console_handler.setLevel(self.console_level)
        console_handler.addFilter(filt)

        # Set the color scheme for the logger
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)s:%(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red'
            }
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Configure the logger to write to a file
        if self._file_handler:
            file_handler = self._file_handler
            file_handler.setLevel(self.file_level)
            file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
            file_handler.addFilter(filt)
            self.logger.addHandler(file_handler)
    
    @classmethod
    def last_instance(cls) -> LogConfig:
        """Return the latest :class:`LogConfig` instance or create a default one."""
        if cls._last_instance is None:
            return LogConfig(
                enabled=False,
                console_level=logging.DEBUG,
                file_level=logging.DEBUG,
                file_path="simpm.log",
            )
        return cls._last_instance

def log_config() -> LogConfig:
    """Return the current :class:`LogConfig` instance."""
    return LogConfig.last_instance()


logger = logging.getLogger("simpm")
