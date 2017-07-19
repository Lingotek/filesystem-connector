import os, sys
from ltk.locales import default_locales, locale_list
from ltk.logger import logger
import time
import logging
import traceback

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
        '.doc' : 'WORD_OKAPI',
        '.dtd': 'DTD',
        '.xlsx': 'XLSX_OKAPI',
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
        '.strings': 'APPLE_STRINGS',
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
    return format_mapper.get(extension.lower(), 'PLAINTEXT_OKAPI')

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
    cmd = "ltk"
    for arg in sys.argv[1:]:
        cmd = cmd + " " + arg
    os.system(cmd)

    ''' This way (below) works for Linux, but does not work on Windows '''
    #python = sys.executable
    #os.execl(python, python, * sys.argv)

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
    if(len(entered_locales) == 0 or (len(entered_locales) == 1 and entered_locales[0] == "[]")):
        logger.warning('No locales have been assigned to this document.  Please add them using \'ltk request\'.')
    else:
        for locale in entered_locales:
            locale = locale.replace("-","_")
            if remote_check and locale not in valid_locales or not remote_check and not locale in locale_list:
                logger.warning('The locale code "'+str(locale)+'" failed to be added since it is invalid (see "ltk list -l" for the list of valid codes).')
            else:
                locales.append(locale)
    return locales

def get_translation_files(file_name, path, download_option, doc_manager):
    translation_files = []

    if download_option == "same":
        downloads = doc_manager.get_doc_downloads(file_name)
        translation_files = find_translations(file_name, path, downloads)

    elif download_option == "folder" :
        downloads = doc_manager.get_doc_downloads(file_name)

        entry = doc_manager.get_doc_by_prop("file_name", file_name)
        if entry:
            file_name = entry['name']

        translation_files = find_translations(file_name, path, downloads)

    elif download_option == "clone":
        entry = doc_manager.get_doc_by_prop("file_name", file_name)
        if entry:
            file_name = entry['name']

        if os.path.isfile(os.path.join(path, file_name)):
            translation_files.append(os.path.join(path, file_name))

    return translation_files

def find_translations(file_name, path, downloads):
    translation_files = []
    trans_file_name = ""
    for d in downloads:
        temp = file_name.split(".")
        trans_file_name = ""
        for idx, val in enumerate(temp):
            if idx == len(temp)-2:
                trans_file_name = trans_file_name +val+"."
                trans_file_name = trans_file_name+d+"."
            else:
                trans_file_name += val
                if idx != len(temp)-1:
                    trans_file_name += "."

            if os.path.isfile(os.path.join(path, trans_file_name)):
                translation_files.append(os.path.join(path, trans_file_name))

    return translation_files


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
        print(term.underline(text))
    else:
        # print("Recommended to install blessings module for better formatting")
        print(text)

def check_response(response):
    try:
        if response and response.text:
            if response.json():
                return True
    except ValueError:
        logger.warning("Could not connect to Lingotek")
        return
    # Python 3
#     except json.decoder.JSONDecodeError:
#         logger.warning("Could not connect to Lingotek")
#         return
    # End Python 3

def remove_begin_slashes(path):
    index = 0
    for letter in path:
        if letter != os.sep:
            break
        index += 1
    if len(path) > index + 1:
        return path[index:]
    else:
        return ''
    return path


def remove_end_slashes(path):
    index = len(path) - 1
    for letter in reversed(path):
        if letter != os.sep:
            break
        index -= 1
    if index > 0:
        return path[:index - 1]
    else:
        return ''
    return path

def remove_last_folder_in_path(path):
    if len(path):
        split_path = path.split(os.sep)
        split_path = split_path[:len(split_path) - 1]
        return os.path.join(*split_path)
    else:
        return path

# Takes a path normalized relative to the project root (path) and returns the path relative to the current directory.
def get_relative_path(path_to_project_root, path):
    abs_path = os.path.dirname(os.path.join(path_to_project_root,path))
    # print("abs_path: "+abs_path)
    relative_path = os.path.relpath(abs_path,os.getcwd())
    # print("relative path: "+relative_path)
    if relative_path == '..' and os.path.join(path_to_project_root,path) == os.getcwd():
        return '.'
    relative_file_path = os.path.join(relative_path,os.path.basename(path))
    split_path = relative_file_path.split(os.sep)
    # print("cwd: "+os.getcwd())
    # print("joined path: "+os.path.join(abs_path,os.path.basename(path)))

    if len(split_path) and split_path[0] == '.' or os.path.join(abs_path,os.path.basename(path)) in os.getcwd():
        relative_file_path = os.path.join(*split_path[1:])
    return relative_file_path

def log_traceback(ex, ex_traceback=None):
    # Python 2
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_str = ""
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in tb_lines:
            tb_str += line+"\n"
    finally:
       """Assigning the traceback return value to a local variable in a function that is handling an exception will cause a circular reference,
          preventing anything referenced by a local variable in the same function or by the traceback from being garbage collected.
          Must explicitly delete. """
       del exc_traceback
       return tb_str
    # End Python 2
    # Python 3
#     if ex_traceback is None:
#         ex_traceback = ex.__traceback__
#     tb_str = ""
#     tb_lines = traceback.format_exception(ex.__class__, ex, ex_traceback)
#     for line in tb_lines:
#         tb_str += line+"\n"
#     return tb_str
    # End Python 3

def log_error(error_file_name, e):
    try:
        with open(error_file_name, 'a') as error_file:
                error_file.write(str(time.strftime("%Y-%m-%d %H:%M:%S") + ": "+str(log_traceback(e))))
    except IOError as e:
        print(e.errno)
        print(e)
    return

def remove_powershell_formatting(args):
    if args != None:
        if isinstance(args, tuple):
            myTuple = ()
            if len(args) > 1:
                if isinstance(args, tuple):
                    for k in args:
                        k = remove_formatting(k)
                        myTuple = myTuple+(k,)

                    return myTuple
                else:
                    for k,v  in args:
                        k = (remove_formatting(k),)
                        v = remove_formatting(v)
                        tup1 = k+(v,)

                        return myTuple+(tup1,)
                return myTuple+(tup1,)
            else:
                for tup in args:
                    if isinstance(tup, tuple):
                        for k in tup:
                            k = remove_formatting(k)
                            myTuple = myTuple+(k,)

                        myTuple = (myTuple),
                        return myTuple
                    else:
                        for k in args:
                            k = remove_formatting(k)
                            myTuple = (k,)

                        return myTuple

                return args

        elif isinstance(args, list):
            temp = []
            for k in args:
                k = remove_formatting(k)
                temp.append(k)

            return tuple(temp)

        elif isinstance(args, str):
            temp = remove_formatting(args)
            return temp
        # Python 2
        elif isinstance(args, bool):
           return args
        # End Python 2
        else:
            # Python 2
          temp = remove_formatting(args)
          return temp
            # End Python 2
            # Python 3
#             return args
            # End Python 3

def remove_formatting(f):
    if f.startswith(".\\"):
        f = f[2:]

        if f.endswith("\\"):
            f = f[:-1]

        if f.endswith("\""):
            f = f[:-1]

        return f

    else:
        return f
