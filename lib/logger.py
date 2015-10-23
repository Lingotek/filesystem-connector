import logging

# add a custom level to show API calls
API_LOG_LEVEL = 15
logging.addLevelName(API_LOG_LEVEL, 'API')

def log_api(self, message, *args, **kwargs):
    if self.isEnabledFor(API_LOG_LEVEL):
        self._log(API_LOG_LEVEL, message, args, **kwargs)

logging.Logger.api_call = log_api

logger = logging.getLogger('lib')
# logger = logging.getLogger('requests')
