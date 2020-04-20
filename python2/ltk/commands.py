''' Python Dependencies '''
import click
import ctypes
import logging
import os
import subprocess
import sys

''' Internal Dependencies '''
from ltk import __version__
from ltk.actions import *
from ltk.constants import LOG_FN, CONF_DIR, METADATA_FIELDS
from ltk.exceptions import UninitializedError, ResourceNotFound, RequestFailedError, AlreadyExistsError
from ltk.logger import logger, API_LOG_LEVEL, API_RESPONSE_LOG_LEVEL, CustomFormatter
from ltk.utils import remove_powershell_formatting
from ltk.watch import WatchAction

''' Globals '''
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
HIDDEN_ATTRIBUTE = 0x02
python_version = sys.version
# Python 3
# # if python_version[0] < '3':
# #    print('Python 3 is required to run this version of the Lingotek Filesystem connector.\n\nFor other versions and troubleshooting, see: https://github.com/lingotek/filesystem-connector')
# #    exit()
# End Python 3


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()

def init_logger(path):
    """
    Initializes logger based on path
    """
    logger.setLevel(logging.DEBUG)
    if not path:
        file_handler = logging.FileHandler(LOG_FN)
    else:
        try:
            file_handler = logging.FileHandler(os.path.join(path, CONF_DIR, LOG_FN))

            # if on Windows system, set directory properties to hidden
            if os.name == 'nt':
                try:
                    subprocess.call(["attrib", "+H", os.path.join(path, CONF_DIR)])
                except Exception as e:
                    logger.error("Error on init: "+str(e))
                # logger.info("On Windows, make .ltk folder hidden")
                # # Python 2
                ret = ctypes.windll.kernel32.SetFileAttributesW(unicode(os.path.join(path, CONF_DIR)), HIDDEN_ATTRIBUTE)
                # # End Python 2
                # # Python 3
#                 # ret = ctypes.windll.kernel32.SetFileAttributesW(os.path.join(path, CONF_DIR), HIDDEN_ATTRIBUTE)
                # # End Python 3
                # if(ret != 1):   # return value of 1 signifies success
                #     pass
        except IOError as e:
            #logger.info(e)
            # todo error check when running init without existing conf dir
            try:
                os.mkdir(os.path.join(path, CONF_DIR))
                # if on Windows system, make directory hidden
                if os.name == 'nt':
                    logger.info("On Windows, make .ltk folder hidden")
                    # Python 2
                    ret = ctypes.windll.kernel32.SetFileAttributesW(unicode(os.path.join(path, CONF_DIR)), HIDDEN_ATTRIBUTE)
                    # End Python 2
                    # Python 3
#                     ret = ctypes.windll.kernel32.SetFileAttributesW(os.path.join(path, CONF_DIR), HIDDEN_ATTRIBUTE)
                    # End Python 3
                    if(ret != 1):   # return value of 1 signifies success
                        pass
            except IOError as e:
                print(e.errno)
                print(e)

            file_handler = logging.FileHandler(os.path.join(path, CONF_DIR, LOG_FN))

    console_handler = logging.StreamHandler(sys.stdout)
    file_handler.setLevel(API_LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter('%(asctime)s  %(levelname)s: %(message)s'))
    if quiet:
        console_handler.setLevel(logging.WARNING)
    elif verbosity:
        if verbosity > 1:
            console_handler.setLevel(API_RESPONSE_LOG_LEVEL)
        else:
            console_handler.setLevel(API_LOG_LEVEL)
    else:
        console_handler.setLevel(logging.INFO)
    custom_formatter = CustomFormatter()
    console_handler.setFormatter(custom_formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def print_log(error):
    """
    Prints the error before logger is initialized
    """
    # if not len(logger.handlers):
    print ('Error: {0}'.format(error))
    sys.exit()
    return


@click.group(context_settings=CONTEXT_SETTINGS)
# Python 2
@click.version_option(version=__version__, message='%(prog)s version %(version)s (Lingotek Filesystem Connector - Python 2)')
# End Python 2
# Python 3
# @click.version_option(version=__version__, message='%(prog)s version %(version)s (Lingotek Filesystem Connector - Python 3)')
# End Python 3
@click.option('-q', 'is_quiet', flag_value=True, help='Will only show warnings')
@click.option('-v', 'verbosity_lvl', count=True, help='Show API calls. Use -vv for API responses.')
def ltk(is_quiet, verbosity_lvl):
    global quiet, verbosity
    quiet = is_quiet
    verbosity = verbosity_lvl


@ltk.command()
@click.option('--access_token', help='Your access token')
@click.option('--host', default='myaccount.lingotek.com', # type=click.Choice(['myaccount.lingotek.com', 'cms.lingotek.com', 'clone.lingotek.com']),
              help='Default environment: myaccount.lingotek.com')
@click.option('--client_id', help='This is an advanced option that should only be used for clients that have been issued a specified client_id for analytics')
@click.option('--path', type=click.Path(exists=True),
              help='The path to the project directory to be initialized; defaults to the current directory')
@click.option('-n', '--project_name', help='The preferred project name, defaults to the current directory name')
@click.option('-w', '--workflow_id', default='c675bd20-0688-11e2-892e-0800200c9a66',
              help='The id of the workflow to use for this project; defaults to machine translate only')
@click.option('-b', '--browser', flag_value=True, help='Launches broswer for Authentication')
@click.option('-l', '--locale', default='en_US', help='The default source locale for the project; defaults to en_US')
@click.option('-d', '--delete', flag_value=True,  # expose_value=False, callback=abort_if_false,
              # prompt='Are you sure you want to delete the current project remotely and re-initialize? '
              #        'Use the -c flag if you only want to change the project.',
              help='Delete the current project remotely and re-initialize')
# todo add a 'change' option so don't delete remote project
# @click.option('-c', '--change', flag_value=True, help='Change the Lingotek project. ')
@click.option('--reset', flag_value=True, help='Reauthorize and reset any stored access tokens')
def init(host, access_token, client_id, path, project_name, workflow_id, locale, browser, delete, reset):
    """ Connects a local project to Lingotek """
    try:
        host = 'https://' + host
        if not path:
            path = os.getcwd()
        if not project_name:
            project_name = os.path.basename(os.path.normpath(path))
        init_logger(path)

        init = init_action.InitAction(os.getcwd())
        init.init_action(host, access_token, client_id, path, project_name, workflow_id, locale, browser, delete, reset)

        if(init.turn_clone_on == False):
            # set the download option in config
            config = config_action.ConfigAction(os.getcwd())
            config.set_clone_option('off', print_info=False)

    except (ResourceNotFound, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command()
#TO-DO: @click.option('-a', '--all', help='List all configuration settings (including access token)')
@click.option('-l', '--locale', help='Change the default source locale for the project')
@click.option('-w', '--workflow_id', help='Change the default workflow id for the project')
@click.option('-ld', '--latest_document', help='Toggle always get latest document option \'on\' and \'off\'')
@click.option('-c', '--clone_option', help='Toggle clone download option \'on\' and \'off\'. Turning clone \'on\': Translations will be downloaded to a cloned folder structure, where the root folder for each locale is the locale folder specified in config or a locale folder inside of the default download folder. If a default download folder is not set, then translations will be downloaded to the directory where the project was initialized.' +
                                                'Turning clone \'off\': Downloaded translations will go into their locale folder (if specified) or default download folder, but not in a cloned folder structure. If no default download folder or locale folder is specified, downloaded translations will go to the same folder as their corresponding source files.')
@click.option('-ff', '--finalized_file', help='Toggle finalized file download option \'on\' and \'off\'. Turning finalized file on downloads the finalized file instead of the raw translation.\
                                                A finalized file is typically a file that has undergone some sort of post editing like Desktop Publishing after the translation has compeleted.')
@click.option('-u', '--unzip_file', help='Toggle finalized file UNZIP option \'on\' and \'off\'. With this option \'on\' contents of the finalized file will be placed in the expected directory.')
@click.option('-d', '--download_folder',
              help='Specify a default folder for where downloaded translations should go. Use --none to remove the download folder. Using --none will cause downloaded translations to download to the same folder as their corresponding source files.')
@click.option('-t', '--target_locales', multiple=True,
              help='Specify target locales that documents in watch_folder should be assigned; may either specify '
                   'with multiple -t flags (ex: -t locale -t locale) or give a list separated by commas and no spaces '
                   '(ex: -t locale,locale)')

@click.option('-p', '--locale_folder', nargs=2, type=str, multiple=True, help='For a specific locale, specify the root folder where downloaded translations should appear. Use --none for the path to clear the download folder for a specific locale. Example: -p fr_FR translations/fr_FR. Note: This only works with clone option \'on\'')
@click.option('-r', '--remove_locales', flag_value=True, help='Remove all locale folders and use the default download location instead.')
@click.option('-g', '--git', help='Toggle Git auto-commit option on and off')
@click.option('-gu', '--git_credentials', is_flag=True, help='Open prompt for Git credentials for auto-fill (\'none\' to unset); only enabled for Mac and Linux')
@click.option('-a', '--append_option', help='Change the format of the default name given to documents on the Lingotek system.  Define file information to append to document names as none, full, number:+a number of folders down to include (e.g. number:2), or name:+a name of a directory to start after if found in file path (e.g. name:dir). Default option is none.')
@click.option('-f', '--auto_format', help='Toggle auto format option \'on\' and \'off\'. Applies formatting during download.')
@click.option('-md', '--metadata_defaults', is_flag=True, help='Launch the metadata wizard to set the default metadata that will be sent with every document.')
@click.option('-mp', '--metadata_prompt', help='Toggle prompting for metadata with every add and push.  Use the argument \'on\' to enable this prompt or \'off\' to disable it.')
@click.option('-mf', '--metadata_fields', help="Set the fields that the metadata wizard will use when adding or pushing documents.  All default metadata will still be sent.  Enter the fields to prompt for as a comma-separated list with no spaces, or enter 'all' to include all the fields.  Valid fields are: "+', '.join(str(field) for field in METADATA_FIELDS))

def config(**kwargs):
    """ View or change local configuration """
    try:
        action = config_action.ConfigAction(os.getcwd())
        init_logger(action.path)
        for f in kwargs:
            if kwargs[f]:
                temp = remove_powershell_formatting(kwargs[f])
                kwargs[f] = temp
        action.config_action(**kwargs)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command(short_help="Add files and folders")
@click.argument('file_names', required=True, nargs=-1)
@click.option('-d', '--directory', flag_value=True, help='Only add directories, not files inside directories')
@click.option('-l', '--locale', help='If source locale is different from the default configuration. Use ltk list -l to see possible locales')
@click.option('-f', '--format',
              help="Format of file; if not specified, will use extension to detect; defaults to plaintext. Use ltk list -f to see possible formats. Files may not be added to Lingotek's system if not formatted correctly according to the specified format")
@click.option('-D', '--download_folder', type=click.Path(exists=True), help='Download folder for the translations for this file.  If set, it will take precedence over locale folders and the default download folder and will ignore clone as well as the no_ext argument when pulling/downloading')
@click.option('-o', '--overwrite', flag_value=True, help='Overwrite previously added file if the file has been modified')
@click.option('-s', '--srx', type=click.Path(exists=True), help='srx file')
@click.option('-si', '--srx_id', help='srx id')
@click.option('-i', '--its', type=click.Path(exists=True), help='its file')
@click.option('-ii', '--its_id', help='its id')
@click.option('-c', '--charset', help='File encoding')
@click.option('-ff', '--fprm', type=click.Path(exists=True), help='fprm file')
@click.option('-fi', '--fprm_id', help='fprm id')
@click.option('-fs', '--fprm_subfilter', type=click.Path(exists=True), help='fprm subfilter file')
@click.option('-fsi', '--fprm_subfilter_id', help='fprm subfilter id')
@click.option('-v', '--vault_id', help='Save-to TM vault id')
@click.option('-e', '--external_url', help='Source url')
@click.option('--due_date', help='Due date (as Unix timestamp, in milliseconds)')
@click.option('--due_reason', help='Reason for due date')
@click.option('-m', '--metadata', flag_value=True, help="Launches the metadata wizard")

# # Metadata - optional parameters
# @click.option('--author_email', help='Author email')
# @click.option('--author_name', help='Author name')
# @click.option('--business_division', help='Business division')
# @click.option('--business_unit', help='Business unit')
# @click.option('--campaign_id', help='Campaign ID')
# @click.option('--campaign_rating', help='Campaign rating')
# @click.option('--channel', help='Channel')
# @click.option('--contact_email', help='Contact email')
# @click.option('--contact_name', help='Contact name')
# @click.option('--content_description', help='Content description')
# @click.option('--content_type', help='Content type')
# @click.option('--domain', help='Domain')
# @click.option('--external_application_id', help='External application ID')
# @click.option('--external_document_id', help='External document ID')
# @click.option('--external_style_id', help='External style ID')
# @click.option('--job_id', help='Job ID')
# @click.option('--purchase_order', help='Purchase Order')
# @click.option('--reference_url', help='Reference URL')
# @click.option('--region', help='Region')
# @click.option('--require_review', help='Require review')
# @click.option('--category_id', help='Category ID')
# @click.option('--note', help='Note')

# Metadata - optional parameters
@click.option('--author_email', hidden=True)
@click.option('--author_name', hidden=True)
@click.option('--business_division', hidden=True)
@click.option('--business_unit', hidden=True)
@click.option('--campaign_id', hidden=True)
@click.option('--campaign_rating', hidden=True)
@click.option('--channel', hidden=True)
@click.option('--contact_email', hidden=True)
@click.option('--contact_name', hidden=True)
@click.option('--content_description', hidden=True)
@click.option('--content_type', hidden=True)
@click.option('--domain', hidden=True)
@click.option('--external_application_id', hidden=True)
@click.option('--external_document_id', hidden=True)
@click.option('--external_style_id', hidden=True)
@click.option('--job_id', hidden=True)
@click.option('--purchase_order', hidden=True)
@click.option('--reference_url', hidden=True)
@click.option('--region', hidden=True)
@click.option('--require_review', hidden=True)
@click.option('--category_id', hidden=True)
@click.option('--note', hidden=True)

def add(file_names, **kwargs):
    #""" Add files and folders for upload to Lingotek.  Fileglobs (e.g. *.txt) can be used to add all matching files and/or folders. Added folders will automatically add the new files added or created inside of them. """
    """ Add files and folders for upload to Lingotek.  Fileglobs (e.g. *.txt) can be used to add all matching files and/or folders. Added folders will automatically add the new files added or created inside of them.
    
    Metadata can be added by launching the metadata wizard with the -m flag or by using flags for specific metadata.  The metadata flags are --author_email, --author_name, --business_division, --business_unit, --campaign_id, --campaign_rating, --channel, --contact_email, --contact_name, --content_description, --content_type, --domain, --external_application_id, --external_document_id, --external_style_id, --job_id, --purchase_order, --reference_url, --region, --require_review, --category_id, and --note """
    try:
        action = add_action.AddAction(os.getcwd())
        init_logger(action.path)

        file_names = remove_powershell_formatting(file_names)

        for f in kwargs:
            if kwargs[f]:
                temp = remove_powershell_formatting(kwargs[f])
                kwargs[f] = temp

        action.add_action(file_names, **kwargs)
    except (UninitializedError, RequestFailedError, ResourceNotFound, AlreadyExistsError) as e:
        print_log(e)
        logger.error(e)
        return

@ltk.command(short_help="Sends updated content to Lingotek for documents that have been added; defaults to the entire project.")
@click.option('-n', '--test', 'test', flag_value=True, help='Shows which files will be added or updated without actually uploading any content')
@click.option('-t', '--title', 'title', flag_value=True, help='Display document titles rather than file paths')
@click.argument('files', type=click.Path(exists=True), required=False, nargs=-1)
@click.option('--due_date', help='Due date (as Unix timestamp, in milliseconds)')
@click.option('--due_reason', help='Reason for due date')
@click.option('-m', '--metadata', flag_value=True, help="Launches the metadata wizard")
@click.option('-o', '--metadata-only', 'metadata_only', flag_value=True, help="Only updates the metadata and due date/due reason and does not update the document contents")

# # Metadata - optional parameters
# @click.option('--author_email', help='Author email')
# @click.option('--author_name', help='Author name')
# @click.option('--business_division', help='Business division')
# @click.option('--business_unit', help='Business unit')
# @click.option('--campaign_id', help='Campaign ID')
# @click.option('--campaign_rating', help='Campaign rating')
# @click.option('--channel', help='Channel')
# @click.option('--contact_email', help='Contact email')
# @click.option('--contact_name', help='Contact name')
# @click.option('--content_description', help='Content description')
# @click.option('--content_type', help='Content type')
# @click.option('--domain', help='Domain')
# @click.option('--external_application_id', help='External application ID')
# @click.option('--external_document_id', help='External document ID')
# @click.option('--external_style_id', help='External style ID')
# @click.option('--job_id', help='Job ID')
# @click.option('--purchase_order', help='Purchase Order')
# @click.option('--reference_url', help='Reference URL')
# @click.option('--region', help='Region')
# @click.option('--require_review', help='Require review')
# @click.option('--category_id', help='Category ID')
# @click.option('--note', help='Note')

# Metadata - optional parameters
@click.option('--author_email', hidden=True)
@click.option('--author_name', hidden=True)
@click.option('--business_division', hidden=True)
@click.option('--business_unit', hidden=True)
@click.option('--campaign_id', hidden=True)
@click.option('--campaign_rating', hidden=True)
@click.option('--channel', hidden=True)
@click.option('--contact_email', hidden=True)
@click.option('--contact_name', hidden=True)
@click.option('--content_description', hidden=True)
@click.option('--content_type', hidden=True)
@click.option('--domain', hidden=True)
@click.option('--external_application_id', hidden=True)
@click.option('--external_document_id', hidden=True)
@click.option('--external_style_id', hidden=True)
@click.option('--job_id', hidden=True)
@click.option('--purchase_order', hidden=True)
@click.option('--reference_url', hidden=True)
@click.option('--region', hidden=True)
@click.option('--require_review', hidden=True)
@click.option('--category_id', hidden=True)
@click.option('--note', hidden=True)

def push(test, title, files, metadata, metadata_only, **kwargs):
    #""" Sends updated content to Lingotek for documents that have been added.  Fileglobs (e.g. *.txt) can be used to push all matching files """
    """ Sends updated content to Lingotek for documents that have been added.  Fileglobs (e.g. *.txt) can be used to push all matching files

    Metadata can be updated by launching the metadata wizard with the -m flag or by using flags for specific metadata.  The metadata flags are --author_email, --author_name, --business_division, --business_unit, --campaign_id, --campaign_rating, --channel, --contact_email, --contact_name, --content_description, --content_type, --domain, --external_application_id, --external_document_id, --external_style_id, --job_id, --purchase_order, --reference_url, --region, --require_review, --category_id, and --note """
    try:
        action = push_action.PushAction(os.getcwd(), test, title)
        init_logger(action.path)
        action.push_action(files=files, set_metadata=metadata, metadata_only=metadata_only, **kwargs)
    except UninitializedError as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command(short_help="Add targets to document(s) to start translation; defaults to the entire project. Use ltk list -l to see possible locales")
@click.option('-n', '--doc_name', help='The name of the document for which to request target locale(s)')
@click.option('-p', '--path', type=click.Path(exists=True), help='The file name or directory for which to request target locale(s)')
@click.option('-c', '--cancel', 'to_cancel', flag_value=True, help='Cancels a specified target locale')
@click.option('-d', '--delete', 'to_delete', flag_value=True, help='Deletes a specified target locale')
@click.option('--due_date', help='The due date of the translation')
@click.option('-w', '--workflow', help='The workflow of the translation (Use "ltk list -w" to see available workflows)')
@click.argument('locales', required=False, nargs=-1)  # can have unlimited number of locales
def request(doc_name, path, locales, to_cancel, to_delete, due_date, workflow):
    """ Add targets to document(s) to start translation; defaults to the entire project. If no locales are specified, Filesystem Connector
        will look for target watch locales set in ltk config. Use ltk list -l to see possible locales. """
    try:
        action = request_action.RequestAction(os.getcwd(), doc_name, path, locales, to_cancel, to_delete, due_date, workflow)
        init_logger(action.path)
        if locales and isinstance(locales,str):
            locales = [locales]

        doc_name = remove_powershell_formatting(doc_name)
        path = remove_powershell_formatting(path)

        action.target_action()
    except (UninitializedError, ResourceNotFound, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

# todo add a --all option to see all document ids once only show relative to cwd is implemented
@ltk.command(name='list', short_help='Shows docs (default), workflows, locales, formats, or filters')
@click.option('-t', '--title', 'title', flag_value=True, help='List document titles and folder paths from project root instead of relative file paths')
@click.option('-c', '--hide_docs', 'hide_docs', flag_value=True, help='Collapse down to list only added directories instead of both directories and documents.')
@click.option('-w', '--workflows', 'id_type', flag_value='workflow', help='List available workflows')
@click.option('-l', '--locales', 'id_type', flag_value='locale', help='List supported locale codes')
@click.option('-f', '--formats', 'id_type', flag_value='format', help='List supported formats')
@click.option('-r', '--remote', 'id_type', flag_value='remote', help='List all project documents on Lingotek Cloud')
@click.option('--filters', 'id_type', flag_value='filter', help='List default and custom filters')
@click.option('-d', '--download_folder', 'show_dests', flag_value=True, help="Show target download folders for files that have had them set")
def list(**kwargs):
    """ Shows docs, workflows, locales, formats, or filters. By default lists added folders and docs. """
    try:
        action = list_action.ListAction(os.getcwd())
        init_logger(action.path)
        action.list_action(**kwargs)

    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command(short_help="Gets the status of a specific document or all documents")
@click.option('-n', '--doc_name', help='Specific document name to get status of')
@click.option('-d', '--detailed', flag_value=True, help='Detailed status of each locale for the document')
@click.option('-a', '--all', flag_value=True, help='List all project documents on Lingotek Cloud')
def status(**kwargs):
    """ Gets the status of a specific document or all documents """
    try:
        action = status_action.StatusAction(os.getcwd())
        init_logger(action.path)

        for f in kwargs:
            if kwargs[f]:
                temp = remove_powershell_formatting(kwargs[f])
                kwargs[f] = temp

        action.get_status(**kwargs)
    except (UninitializedError, ResourceNotFound) as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command(short_help='Download specified translations')
@click.option('-a', '--auto_format', flag_value=True, help='Flag to auto apply formatting during download')
@click.option('-l', '--locales', help="Specify locales to download (defaults to all target locales for the document). For multiple locales give a list separated by commas and no spaces (ex: en_US,en_GB).")
@click.option('-e', '--locale_ext', flag_value=True, help="Specifies to add the name of the locale as an extension to the file name (ex: doc1.fr_FR.docx). This is the default unless the clone download option is active.")
@click.option('-n', '--no_ext', flag_value=True, help="Specifies to not add the name of the locale as an extension to the file name. This is the default if the clone download option is active.")
@click.option('-x', '--xliff', flag_value=True, help="Download xliff version of the specified translation")
@click.argument('file_names', type=click.Path(exists=True), required=True, nargs=-1)
def download(auto_format, locales, locale_ext, no_ext, xliff, file_names):
    """ Downloads translated content specified by filename for specified locales, or all locales if none are specified. Change download options and folders using ltk config."""
    try:
        action = download_action.DownloadAction(os.getcwd())
        init_logger(action.path)

        for name in file_names:
            action.download_by_path(name, locales, locale_ext, no_ext, auto_format, xliff)
            print("\n")

    except (UninitializedError, ResourceNotFound, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command(short_help='Pulls translations for all added documents for all locales or by specified locales')
@click.option('-a', '--auto_format', flag_value=True, help='Flag to auto apply formatting during download')
@click.option('-e', '--locale_ext', flag_value=True, help="Specifies to add the name of the locale as an extension to the file name (ex: doc1.fr_FR.docx). This is the default unless the clone download option is active.")
@click.option('-n', '--no_ext', flag_value=True, help="Specifies to not add the name of the locale as an extension to the file name. This is the default if the clone download option is active.")
@click.argument('locales', nargs=-1)
def pull(auto_format, locale_ext, no_ext, locales):
    """ Pulls translations for all added documents for all locales or by specified locales """
    try:
        download = download_action.DownloadAction(os.getcwd())
        action = pull_action.PullAction(os.getcwd(), download)
        init_logger(action.path)
        if locales:
            for locale in locales:
                action.pull_translations(locale, locale_ext, no_ext, auto_format)
        else:
            action.pull_translations(None, locale_ext, no_ext, auto_format)
    except UninitializedError as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command(name="rm", short_help="Disassociates local doc(s) from Lingotek Cloud and cancels the remote copy")
@click.argument('file_names', required=False, nargs=-1)
@click.option('-d', '--directory', flag_value=True, help='Only remove directories, not files inside directories')
@click.option('-i', '--id', flag_value=True, help='Cancels documents with the specified ids (instead of file names) on Lingotek Cloud.  Can be used to cancel documents that are not locally tracked.')
@click.option('-n', '--name', flag_value=True, help='Cancels documents with the specified names (instead of file names or paths) on Lingotek Cloud')
@click.option('-a', '--all', flag_value=True, help='Cancels all documents from Lingotek Cloud that are found locally')
@click.option('-l', '--local', flag_value=True, help='Deprecated.  Use \'ltk rm -f -a\' for all documents or \'ltk rm -f\' for specific documents.  (Legacy Usage: deletes all documents locally and cancels them in the Lingotek Cloud. Can be used in association with --name to delete a specified document locally.)')
@click.option('-r', '--remote', flag_value=True, help='Deletes specified documents from Lingotek Cloud instead of cancelling them')
@click.option('-f', '--force', flag_value=True, help='Delete local copy when cancelling remote source documents')
def rm(file_names, **kwargs):
    """
    Disassociates local doc(s) from Lingotek Cloud and removes them from the project by cancelling them.  If the remote copy should be deleted, use the -r flag.
    """
    try:
        action = rm_action.RmAction(os.getcwd())
        init_logger(action.path)
        if not file_names and not (('all' in kwargs and kwargs['all']) or ('local' in kwargs and kwargs['local'])):
            logger.info("Usage: ltk rm [OPTIONS] FILE_NAMES...")
            return

        if len(file_names) > 0:
            file_names = remove_powershell_formatting(file_names)

        action.rm_action(file_names, **kwargs)
    except (UninitializedError, ResourceNotFound, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@ltk.command(short_help="Move file or directory at the specified location to a specified destination folder.")
@click.argument('source_path', type=click.Path(exists=True), required=True, nargs=-1)
@click.argument('destination_path', required=True, nargs=1)
def mv(source_path, destination_path):
    """
    Moves specified local doc to a specified destination directory, moving both the file itself and file location stored in the local database.
    If SOURCE_PATH is a directory, all added files in the directory will be moved.
    """
    try:
        # action = actions.Action(os.getcwd())
        add = add_action.AddAction(os.getcwd())
        action = move_action.MoveAction(add, os.getcwd())
        init_logger(action.path)

        source_path = remove_powershell_formatting(source_path)
        #print("Source path " + str(source_path))
        destination_path = remove_powershell_formatting(destination_path)
        #print("Destination path "+str(destination_path))

        action.mv_action(source_path, destination_path)
    except(UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@ltk.command(name='import', short_help="Import docs from Lingotek")
@click.option('-a', '--all', 'import_all', flag_value=True, help='Import all documents from Lingotek Cloud')
@click.option('-f', '--force', flag_value=True, help='Overwrites existing documents without prompt')
@click.option('-p', '--path', type=click.Path(exists=True), help='Import documents to a specified path')
@click.option('-t', '--track', flag_value=True, help='Automatically add the imported documents to local tracking if they were not already being tracked.  Will not track cancelled documents.  Note: They will be added without extra options (no srx id, no download folder, etc.)')
@click.option('-c', '--no-cancel', flag_value=True, help='Don\'t include documents that have been cancelled.')
def import_command(import_all, force, path, track, no_cancel):
    """
    Import documents from Lingotek Cloud, by default downloading to the project's root folder
    """
    # todo import should show all documents
    # add a force option so can import all force -- overwrites all existing documents without prompting
    # check if doc id
    # if exist, prompt for overwrite
    # else automatically re-name
    # possibly have to patch title in Lingotek Cloud?
    try:
        # action = actions.Action(os.getcwd())
        action = import_action.ImportAction(os.getcwd())
        init_logger(action.path)

        if path != None:
            path = remove_powershell_formatting(path)

        action.import_action(import_all, force, path, track, no_cancel)
    except(UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return


@ltk.command(short_help="Cleans up the associations between local documents and documents in Lingotek")
@click.option('-a', '--all', 'dis_all', flag_value=True, help='Removes all associations between local and remote documents and cancels those documents')
@click.argument('file_paths', required=False, nargs=-1)
@click.option('-f', '--force', flag_value=True, help='Deletes locally tracked documents that have been cancelled or no longer exist in Lingotek')
def clean(force, dis_all, file_paths):
    """
    Cleans up the associations between local documents and documents in Lingotek.
    By default, removes documents from local tracking that have been cancelled or no longer exist locally or in the Lingotek Cloud.
    Enter file or directory names to cancel those documents and remove local associations of specific files or directories.
    """
    try:
        action = clean_action.CleanAction(os.getcwd())
        init_logger(action.path)

        if len(file_paths) > 0:
            file_paths = remove_powershell_formatting(file_paths)

        action.clean_action(force, dis_all, file_paths)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@ltk.command(short_help="Copies added source folders for each locale")
@click.argument('folders', required=False, nargs=-1)
@click.option('-c', '--copy_root', flag_value=True, help='Copies the root source folder as a subfolder inside the locale folder, even if there is only one source folder being cloned.')
def clone(folders, copy_root):
    """
    Copies the folder structure of added folders or specified folders
    for each target locale as specified in config.
    Folders are added to the locale folder specified if one has been specified,
    or by default a new folder will be created with the name of the locale. If
    only one root folder is being cloned, then the locale folder is used
    (instead of creating a new folder inside of the locale folder).
    """
    try:
        action = clone_action.CloneAction(os.getcwd())
        init_logger(action.path)
        if isinstance(folders,str):
            folders = [folders]

        if len(folders) > 0:
            folders = remove_powershell_formatting(folders)

        action.clone_action(folders, copy_root)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@ltk.command(short_help="Watches local and remote files")
# @click.option('-p', '--path', type=click.Path(exists=True), multiple=True, help='Specify a folder to watch. Use option multiple times to specify multiple folders.')
@click.option('--ignore', multiple=True, help='Specify types of files to ignore.  For multiple types, specify this flag multiple times.  For example, to ignore pdf and html files, use "ltk watch --ignore .pdf --ignore .html"')
@click.option('--auto', 'delimiter', help='Automatically detects locale from the file name; specify locale delimiter')
@click.option('-t', '--timeout', type=click.INT, default=60,
              help='The amount of time watch will sleep between polls, in seconds. Defaults to 1 minute')
@click.option('-n','--no_folders', flag_value=True, help='Ignore files added to watch folders and only watch documents that have already been added.')
@click.option('-f','--force_poll', flag_value=True, help='Force API calls to Lingotek system at every poll for every document')
def watch(ignore, delimiter, timeout, no_folders, force_poll): # path, ignore, delimiter, timeout, no_folders):
    """
    Watches local files added by ltk, and sends a PATCH when a document is changed.
    Also watches remote files, and automatically downloads finished translations.
    Automatically adds documents that are added to the watchfolder.  Note: The add is performed without extra options (no srx id, no download folder, etc.)
    """
    try:
        action = WatchAction(os.getcwd(), timeout)
        init_logger(action.path)
        action.watch_action(ignore, delimiter, no_folders, force_poll) #path, ignore, delimiter, no_folders)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

# Filters (Split into files, see http://bit.ly/2jArTRm)

@click.group(short_help="List, create, update, or delete Lingotek filters")
def filters():
    pass

@filters.command(name='add',short_help="Create a filter on Lingotek.")
@click.argument('filename')
@click.option('-t', '--type', 'filter_type', type=click.Choice(['FPRM','SRX','ITS']), help="The filter type being added.  Must be one of the following: FPRM, SRX, ITS.  When not explicitly specified, the file extension is used to attempt to detect the type.")
def filter_add(filename, filter_type):
    """Create filter on Lingotek."""
    try:
        action = filters_action.FiltersAction(os.getcwd())
        init_logger(action.path)
        action.filter_add_action(filename, filter_type)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@filters.command(name='save',short_help="Update filter on Lingotek.")
@click.argument('filter_id')
@click.argument('filename')
def filter_add(filter_id, filename):
    """Update filter on Lingotek."""
    try:
        action = filters_action.FiltersAction(os.getcwd())
        init_logger(action.path)
        action.filter_save_action(filter_id, filename)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@filters.command(name="get", short_help="Retrieve filter contents from Lingotek.")
@click.argument('filter_id')
@click.argument('filename', required=False)
@click.option('--info','info',flag_value=True, help="Retrieve filter info only.")
@click.option('--overwrite',flag_value=True, help="Overwrite local file when it already exists.")
def filter_get(filter_id, filename, info, overwrite):
    """Retrieve the filter specified by FILTER_ID from Lingotek and store it in the current working directly as the title (or as as the optional_filename when specified) of the filter"""
    try:
        action = filters_action.FiltersAction(os.getcwd())
        init_logger(action.path)
        if info == True:
            action.filter_info_action(filter_id)
        else:
            action.filter_get_action(filter_id, filename, overwrite)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@filters.command(name="list")
def filter_list():
    """List default and custom filters."""
    try:
        action = filters_action.FiltersAction(os.getcwd())
        init_logger(action.path)
        action.filter_list_action()
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@filters.command(name="rm", short_help="Remove filter from Lingotek.")
@click.argument('filter_id')
def filter_rm(filter_id):
    """Remove the filter specified by FILTER_ID."""
    try:
        action = filters_action.FiltersAction(os.getcwd())
        init_logger(action.path)
        action.filter_rm_action(filter_id)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

ltk.add_command(filters)

@click.group(short_help="Manages reference material attached to documents.")
def reference():
    pass

@reference.command(name='add', short_help="Uploads reference material and attaches it to the specified document.")
@click.argument('filename')
@click.option('-i', '--id', 'doc_id', flag_value=True, help="Adds reference material to the specified document ID instead of the specified filename.")
def reference_add(filename, doc_id):
    """Adds reference material to a document on Lingotek."""
    try:
        action = reference_action.ReferenceAction(os.getcwd())
        init_logger(action.path)
        action.reference_add_action(filename, doc_id)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@reference.command(name='list', short_help="Lists the reference material that is currently attached to the specified document.")
@click.argument('filename')
@click.option('-i', '--id', 'doc_id', flag_value=True, help="Lists reference material attached to the specified document ID instead of the specified filename.")
def reference_list(filename, doc_id):
    """Lists reference material attached to a document on Lingotek."""
    try:
        action = reference_action.ReferenceAction(os.getcwd())
        init_logger(action.path)
        action.reference_list_action(filename, doc_id)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@reference.command(name='get', short_help="Downloads reference material that is currently attached to the specified document.")
@click.argument('filename')
@click.option('-i', '--id', 'doc_id', flag_value=True, help="Downloads reference material attached to the specified document ID instead of the specified filename.")
@click.option('-a', '--all', 'get_all', flag_value=True, help="Skips the prompt and downloads all the reference material that is attached to the document.")
@click.option('-p', '--path', type=click.Path(exists=True), help='Download reference material to a specified path')
def reference_get(filename, doc_id, get_all, path):
    """Downloads reference material attached to a document on Lingotek.  Defaults to downloading them to the root of the project"""
    try:
        action = reference_action.ReferenceAction(os.getcwd())
        init_logger(action.path)
        action.reference_download_action(filename, doc_id, get_all, path)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

@reference.command(name='rm', short_help="Removes reference material that is currently attached to the specified document")
@click.argument('filename')
@click.option('-i', '--id', 'doc_id', flag_value=True, help="Removes reference material from the specified document ID instead of the specified filename.")
@click.option('-a', '--all', 'remove_all', flag_value=True, help="Skips the prompt and removes all the reference material from the document.")
def reference_remove(filename, doc_id, remove_all):
    """Deletes reference material attached to a document on Lingotek."""
    try:
        action = reference_action.ReferenceAction(os.getcwd())
        init_logger(action.path)
        action.reference_remove_action(filename, doc_id, remove_all)
    except (UninitializedError, RequestFailedError) as e:
        print_log(e)
        logger.error(e)
        return

ltk.add_command(reference)

if __name__ == '__main__':
    ltk()
