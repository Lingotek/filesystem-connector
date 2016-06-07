import os
from ltk.locales import default_locales
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
