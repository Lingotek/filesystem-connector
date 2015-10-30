import click
import actions
# from actions import Action
import os
from exceptions import UninitializedError, ResourceNotFound, RequestFailedError, AlreadyExistsError
from constants import LOG_FN
import logging
from logger import logger, API_LOG_LEVEL, API_RESPONSE_LOG_LEVEL
import sys
from lib import __version__

@click.group()
@click.version_option(version=__version__, message='%(prog)s version %(version)s (Lingotek CLT)')
@click.option('-q', 'quiet', flag_value=True, help='will only show warnings')
@click.option('-v', 'verbosity', count=True, help='show API calls. -vv for API responses.')
def ltk(quiet, verbosity):
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(LOG_FN)  # todo maybe have path to where logs stored
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
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # actions.set_logger(logger)
    # logger.info('Starting Lingotek tool..')


@ltk.command()
@click.option('--access_token', help='your access token')
@click.option('--host', type=click.Choice(['myaccount.lingotek.com', 'cms.lingotek.com']), default='cms.lingotek.com',
              help='environment: myaccount for production, cms for sandbox; default is sandbox')
# @click.option('--host', help='host')
@click.option('--path', type=click.Path(exists=True),
              help='the path to the project directory to be initialized, defaults to current directory')
@click.option('-n', '--project_name', help='the preferred project name, defaults to current directory name')
@click.option('-w', '--workflow_id', default='c675bd20-0688-11e2-892e-0800200c9a66',
              help='the id of the workflow to use for this project, defaults to machine translate only.')
@click.option('-l', '--locale', default='en_US', help='the default source locale for the project; defaults to en_US')
@click.option('-d', '--delete', flag_value=True, help='delete the current project and re-initialize')
def init(host, access_token, path, project_name, workflow_id, locale, delete):
    """ initializes a Lingotek project """
    try:
        host = 'https://' + host
        if not path:
            path = os.getcwd()
        if not project_name:
            project_name = os.path.basename(os.path.normpath(path))
        # if not access_token:
        #     # get access token from username/password
        #     access_token = run_oauth(host)
        actions.init_action(host, access_token, path, project_name, workflow_id, locale, delete)
    except (ResourceNotFound, RequestFailedError) as e:
        logger.error(e)
        return

@ltk.command()
@click.option('-l', '--locale', help='change the default source locale for project')
@click.option('-w', '--workflow_id', help='change the default workflow id for project')
def config(locale, workflow_id):
    """ view or change project configurations """
    try:
        action = actions.Action(os.getcwd())
        action.config_action(locale, workflow_id)
    except (UninitializedError, RequestFailedError) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return

@ltk.command()
@click.argument('file_names', required=True, nargs=-1)
@click.option('-l', '--locale', help='if source locale is different from the default configuration')
@click.option('-f', '--format',
              help='format of file; if not specified, will use extension to detect; defaults to plaintext')
@click.option('-s', '--srx', type=click.Path(exists=True), help='srx file')
@click.option('-si', '--srx_id', help='srx id')
@click.option('-i', '--its', type=click.Path(exists=True), help='its file')
@click.option('-ii', '--its_id', help='its id')
@click.option('-c', '--charset', help='file encoding')
@click.option('-ff', '--fprm', type=click.Path(exists=True), help='fprm file')
@click.option('-fi', '--fprm_id', help='fprm id')
@click.option('-fs', '--fprm_subfilter', type=click.Path(exists=True), help='fprm subfilter file')
@click.option('-fsi', '--fprm_subfilter_id', help='fprm subfilter id')
@click.option('-v', '--vault_id', help='save-to TM vault id')
@click.option('-e', '--external_url', help='source url')
def add(file_names, locale, **kwargs):
    """ adds content, could be one file or multiple files specified by Unix shell pattern """
    try:
        action = actions.Action(os.getcwd())
        action.add_action(locale, file_names, **kwargs)
    except (UninitializedError, RequestFailedError, ResourceNotFound, AlreadyExistsError) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return


# @ltk.command()
# @click.argument('-p', 'update_type', flag_value='project', prompt='Update type?', help='update a project')
# @click.argument('-d', 'update_type', flag_value='document', help='update a document')
# def update(update_type, title, update_id, due_date, workflow, callback, **kwargs):
#     pass

@ltk.command()
def push():
    """ patch all documents that have been added to TMS through tool """
    try:
        action = actions.Action(os.getcwd())
        action.push_action()
    except UninitializedError as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return


@ltk.command()
@click.option('-n', '--doc_name', help='the name of the document, specify for one document')
@click.option('--due_date', help='the due date of the translation')
@click.option('-w', '--workflow', help='the workflow of the translation')
@click.argument('locales', required=True, nargs=-1)  # can have unlimited number of locales
def request(doc_name, locales, due_date, workflow):
    """ add targets to document(s) to start translation, defaults to all """
    try:
        action = actions.Action(os.getcwd())
        action.request_action(doc_name, locales, due_date, workflow)
    except (UninitializedError, ResourceNotFound, RequestFailedError) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return


# todo add a --all option to see all document ids once only show relative to cwd is implemented
@ltk.command(name='list')
@click.option('-d', 'id_type', flag_value='document', help='list document ids')
@click.option('-w', 'id_type', flag_value='workflow', help='list available workflow ids')
@click.option('-l', 'id_type', flag_value='locale', help='list supported locale codes')
def list_ids(id_type):
    """ lists ids and titles of documents added with tool, or available workflows """
    try:
        action = actions.Action(os.getcwd())
        if id_type == 'workflow':
            action.list_ids_action('workflows')
        elif id_type == 'locale':
            action.list_locale_action()
        else:
            action.list_ids_action('documents')
    except (UninitializedError, RequestFailedError) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return


@ltk.command()
@click.option('-n', '--doc_name', help='specific document name to get status of')
@click.option('-d', '--detailed', flag_value=True, help='detailed status of each locale for document')
def status(doc_name, detailed):
    """ gets the status of a specific document or all documents """
    try:
        action = actions.Action(os.getcwd())
        action.status_action(detailed, doc_name)
    except (UninitializedError, ResourceNotFound) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return


@ltk.command()
@click.option('-a', '--auto_format', flag_value=True, help='flag to auto apply formatting during download')
@click.argument('locale', required=True, nargs=1)
@click.argument('document_names', required=True, nargs=-1)
def download(auto_format, locale, document_names):
    """ downloads translated content of document(s) """
    try:
        action = actions.Action(os.getcwd())
        for name in document_names:
            action.download_by_name(name, locale, auto_format)
    except (UninitializedError, ResourceNotFound, RequestFailedError) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return


@ltk.command()
@click.option('-a', '--auto_format', flag_value=True, help='flag to auto apply formatting during download')
@click.argument('locales', nargs=-1)
def pull(auto_format, locales):
    """ pulls all translations for added documents """
    try:
        action = actions.Action(os.getcwd())
        if locales:
            for locale in locales:
                action.pull_action(locale, auto_format)
        else:
            action.pull_action(None, auto_format)
    except UninitializedError as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return

@ltk.command()
@click.argument('document_names', required=True, nargs=-1)
def delete(document_names):
    """
    deletes document(s)
    """
    try:
        action = actions.Action(os.getcwd())
        for name in document_names:
            action.delete_action(name)
    except (UninitializedError, ResourceNotFound, RequestFailedError) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return

# possibly some option to delete or keep local docs?
@ltk.command()
@click.option('-f', 'force', flag_value=True, help='delete any local documents out of sync with TMS')
@click.option('-u', 'update', flag_value=True, help='overwrites any local files with content from TMS')
def sync(force, update):
    """
    syncs the current project with project in TMS -- deletes and downloads documents.
    """
    try:
        action = actions.Action(os.getcwd())
        action.sync_action(force, update)
    except (UninitializedError, RequestFailedError) as e:
        # print e
        # logging.error(e)
        logger.error(e)
        return

if __name__ == '__main__':
    ltk()
