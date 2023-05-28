"""
## SimPM Logging Module

---

### Module-level variables
 `logger` : This logger holds a `logging.Logger` object for logging messages in the "simpm" package.

---

### Functions
 `current_config()`: Returns the last instance of `LogConfig` wich its properties can change
 
---

## LogConfig Class
 This module provides a  `LogConfig`  class that can be used to configure logging settings in a simpm.
 ### Overview
 The  `LogConfig`  class allows developers to configure logging settings such as log output destination, log level, and log formatting. It provides a way to customize the logging behavior of an application based on specific requirements.
 ### Class level variable:
 -  `_last_instance` : A class level variable to hold the last instance created.
 ### Properties:
 -  `enabled` : A boolean property indicating whether the logging feature is enabled or disabled.
-  `logger` : A  `logging.Logger`  object which can be used to log messages.
-  `console_level` : A property used to get the console level as an integer.
-  `file_level` : A property to get or set the log level of the file handler.
-  `file_path` : A property to get the file path for the log file.
 ### Methods:
 -  `__init__(...)` : A constructor that initializes the  `LogConfig`  instance.
-  `_configure_logger()` : A function that configures a logger to allow for logging of messages from the application.
-  `last_instance(...)` : A class method that returns the last instance of the  `LogConfig`  class if one exists, otherwise it creates a new  `LogConfig`  with default parameters (enabled set to False, console_level set to logging.DEBUG, file_level set to logging.DEBUG, and file_path set to "simpm.log").
-  `current_config()` : A function that returns the last instance of  `LogConfig`  so that its properties can be changed.
 ## Usage
 To use the  `LogConfig`  class, simply create an instance with the desired parameters, such as:
from log_cfg import LogConfig
 log_cfg = LogConfig(enabled=True, console_level=logging.INFO, file_level=logging.WARNING, file_path="my_log.log")
Once created, you can access the  `logger`  property to log messages, as well as use the other properties to get or set log levels and file paths as necessary.
log_cfg.logger.info("This is an information message.")
log_cfg.console_level = logging.WARNING
log_cfg.file_path = "new_log_file.log"
If you need to obtain the last instance of  `LogConfig`  that was created, you can use the  `last_instance()`  method:
log_cfg = LogConfig.last_instance()
Alternatively, you can use the  `current_config()`  function to obtain and modify the last instance:
log_cfg = current_config()
log_cfg.enabled = True

---

## Dependencies
 This module requires the following modules:
 -  `logging` 
-  `colorlog`  (optional, for colorized console output)
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
        
        self._console_level = console_level
        self._file_level = file_level
        self._file_path = file_path

        # Configure the logger to write to the console
        self._console_handler = logging.StreamHandler()

        # Configure the logger to write to a file
        self._file_handler = logging.FileHandler(self.file_path)
        
        self._configure_logger()
        LogConfig._last_instance = self
    
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
        file_handler = self._file_handler
        file_handler.setLevel(self.file_level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
        file_handler.addFilter(filt)
        self.logger.addHandler(file_handler)
    
    @classmethod
    def last_instance(cls) -> LogConfig:
        """This function returns the last instance of the LogConfig class if one exists, otherwise it creates a new LogConfig with enabled set to False, console_level set to logging.DEBUG, file_level set to logging.DEBUG, and file_path set to "simpm.log"."""
        if cls._last_instance is None:
            return LogConfig(enabled=False, console_level=logging.DEBUG, file_level=logging.DEBUG,
                       file_path='simpm.log')
        return cls._last_instance

def current_config() -> LogConfig:
    """ 
    Returns the last instance of `LogConfig` that its properties can change
    """
    return LogConfig.last_instance()

logger = logging.getLogger("simpm")
"""This logger holds a `logging.Logger` object for logging messages in the "simpm" package."""