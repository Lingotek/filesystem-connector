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
# logger = logging.getLogger('requests')
