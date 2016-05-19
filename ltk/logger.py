import logging

# add a custom level to show API calls
API_LOG_LEVEL = 15
logging.addLevelName(API_LOG_LEVEL, 'API')

# add another custom level to show API responses
API_RESPONSE_LOG_LEVEL = 12
logging.addLevelName(API_RESPONSE_LOG_LEVEL, 'API Response')

def log_api(self, message, *args, **kwargs):
    if self.isEnabledFor(API_LOG_LEVEL):
        self._log(API_LOG_LEVEL, message, args, **kwargs)

def log_api_response(self, message, *args, **kwargs):
    if self.isEnabledFor(API_RESPONSE_LOG_LEVEL):
        self._log(API_RESPONSE_LOG_LEVEL, message, args, **kwargs)

logging.Logger.api_call = log_api
logging.Logger.api_response = log_api_response

logger = logging.getLogger('lib')

class CustomFormatter(logging.Formatter):
    # default_format = '%(levelname)s: %(message)s'
    default_format = '%(levelname)s: %(message)s'
    info_format = '%(message)s'

    # previous default: "%(levelno)s: %(message)s"
    def __init__(self, fmt="%(message)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.INFO:
            self._fmt = CustomFormatter.info_format
        else:
            self._fmt = CustomFormatter.default_format

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result
