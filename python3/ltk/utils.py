import os, sys
from ltk.locales import default_locales, locale_list
from ltk.logger import logger
import time
try:
    from blessings import Terminal
    term = Terminal()
except ImportError:
    term = False
# from constants import APP_ID

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

# def get_access_token(host, username, password):
#     auth_uri = host + '/auth/authorize.html'
#     auth_params = {'client_id': APP_ID, 'redirect_uri': '', 'response_type': 'token'}

# todo possibly put dictionary outside so not built with every function call
def detect_format(file_name, get_mapper=False):
    format_mapper = {
        '.csv': 'CSV',
        '.dita': 'DITA',
        '.ditamap': 'DITAMAP',
        '.docx': 'DOCX_OKAPI',
        '.dtd': 'DTD',
        '.xslx': 'EXCEL_OKAPI',  # xslx, xltx
        '.idml': 'IDML',
        '.properties': 'JAVA_PROPERTIES_OKAPI',
        '.json': 'JSON',
        '.pdf': 'PDF',
        '.txt': 'PLAINTEXT_OKAPI',
        '.po': 'PO',
        '.ppt': 'PPT_OKAPI',
        '.pptx': 'PPTX_OKAPI',
        '.resx': 'RESX',
        '.regex': 'REGEX',
        '.rtf': 'RTF_OKAPI',
        '.srt': 'SUBTITLE_RIP',
        '.tsv': 'TABLE',  # catkeys?
        '.ts': 'TS',
        '.xml': 'XML_OKAPI'
    }

    format_mapper.update(dict.fromkeys(['.dox', '.c', '.h', '.cpp'], 'DOXYGEN'))
    format_mapper.update(dict.fromkeys(['.html', '.htm'], 'HTML_OKAPI'))
    format_mapper.update(dict.fromkeys(['.odp', '.otp'], 'ODP'))
    format_mapper.update(dict.fromkeys(['.ods', '.ots'], 'ODS'))
    format_mapper.update(dict.fromkeys(['.odt', '.ott'], 'ODT'))
    format_mapper.update(dict.fromkeys(['.yaml', '.yml'], 'RAILS_YAML'))
    format_mapper.update(dict.fromkeys(['.xliff', '.xlf'], 'XLIFF_OKAPI'))
    if get_mapper:
        return format_mapper
    name, extension = os.path.splitext(file_name)
    return format_mapper.get(extension, 'PLAINTEXT_OKAPI')

def map_locale(locale):
    """
    maps incorrectly formatted locales to valid locales for use with Lingotek API
    :param locale: incorrectly formatted locale
    :return: valid locale
    """
    # import json
    # valid_locales = []
    # unsupported_locales = []
    # with open('data/language-default-locales.json') as json_file:
    #     default_locales = json.load(json_file)
    try:
        return default_locales[locale]
    except KeyError:
        return None
    # for locale in locales:
    #     try:
    #         valid_locales.append(default_locales[locale])
    #     except KeyError:
    #         unsupported_locales.append(locale)
    # return valid_locales, unsupported_locales

def restart(message="Restarting watch", interval=5):
    """Restarts the program. Used after exceptions. Otherwise, watch doesn't work anymore."""
    time.sleep(interval)
    print(message)
    python = sys.executable
    os.execl(python, python, * sys.argv)

def is_valid_locale(api, locale):
    """Returns true if the locale is found in Lingotek's remote list of locales or, if the api call fails, if the locale is found in the local list of locales."""
    valid_locales = []
    response = api.list_locales()
    remote_check = False
    if response.status_code == 200:
        remote_check = True
    locale_json = response.json()
    for entry in locale_json:
        valid_locales.append(locale_json[entry]['locale'])
    locales = []
    locale = locale.replace("-","_")
    if remote_check and locale not in valid_locales or not remote_check and not locale in locale_list:
        return False
    else:
        return True

def get_valid_locales(api, entered_locales):
    """Return the list of valid locales, checking locales either remotely or using a local list of locales."""
    valid_locales = []
    response = api.list_locales()
    remote_check = False
    if response.status_code == 200:
        remote_check = True
    locale_json = response.json()
    for entry in locale_json:
        valid_locales.append(locale_json[entry]['locale'])
    locales = []
    for locale in entered_locales:
        locale = locale.replace("-","_")
        if remote_check and locale not in valid_locales or not remote_check and not locale in locale_list:
            logger.warning('The locale code "'+str(locale)+'" failed to be added since it is invalid (see "ltk list -l" for the list of valid codes).')
        else:
            locales.append(locale)
    return locales

def raise_error(json, error_message, is_warning=False, doc_id=None, file_name=None):
    try:
        error = json['messages'][0]
        file_name = file_name.replace("Status of ", "")
        if file_name is not None and doc_id is not None:
            error = error.replace(doc_id, file_name+" ("+doc_id+")")
        # Sometimes api returns vague errors like 'Unknown error'
        if error == 'Unknown error':
            error = error_message
        if not is_warning:
            raise exceptions.RequestFailedError(error)
        # warnings.warn(error)
        logger.error(error)
    except (AttributeError, IndexError):
        if not is_warning:
            raise exceptions.RequestFailedError(error_message)
        # warnings.warn(error_message)
        logger.error(error_message)

def error(error_message):
    logger.error(error_message+"\n")

def underline(text):
    if term:
        with term.location(0, term.height - 1):
            print(term.underline(text))
    else:
        # print("Recommended to install blessings module for better formatting")
        print(text)