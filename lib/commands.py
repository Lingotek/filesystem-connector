import click
import actions
# from actions import Action
import os
from exceptions import UninitializedError, ResourceNotFound, RequestFailedError


@click.group()
def ltk():
    pass


@ltk.command()
@click.option('--access_token', prompt='Enter your access token', help='your access token')
@click.option('--host', type=click.Choice(['myaccount.lingotek.com', 'cms.lingotek.com']), default='cms.lingotek.com',
              help='defaults to cms.lingotek.com')
@click.option('--path', type=click.Path(exists=True),
              help='the path to the project directory to be initialized, defaults to current directory')
@click.option('-n', '--project_name', help='the preferred project name, defaults to current directory name')
@click.option('-w', '--workflow_id',
              help='the id of the workflow to use for this project, defaults to machine translate only.')
def init(host, access_token, path, project_name, workflow_id):
    """ initializes a Lingotek project """
    host = 'https://' + host
    if not path:
        path = os.getcwd()
    if not project_name:
        project_name = os.path.basename(os.path.normpath(path))
    if not workflow_id:
        workflow_id = 'c675bd20-0688-11e2-892e-0800200c9a66'
    actions.init_action(host, access_token, path, project_name, workflow_id)


@ltk.command()
@click.argument('file_names', required=True, nargs=-1)
@click.argument('locale', required=True, nargs=1)
@click.option('--path', type=click.Path(exists=True), help='path to your file')
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
def add(path, file_names, locale, **kwargs):
    """ adds content, could be one file or multiple files specified by Unix shell pattern """
    if not path:
        path = os.getcwd()
    try:
        action = actions.Action(path)
        action.add_action(locale, file_names, **kwargs)
    except (UninitializedError, RequestFailedError) as e:
        # todo log the error somewhere
        print e
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
        print e
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
        print e
        return


@ltk.command()
@click.option('-d', 'id_type', flag_value='document', help='list document ids')
@click.option('-w', 'id_type', flag_value='workflow', help='list available workflow ids')
def ids(id_type):
    """ lists ids and titles of documents added with tool, or available workflows """
    try:
        action = actions.Action(os.getcwd())
        if id_type == 'workflow':
            action.list_ids_action('workflows')
        else:
            action.list_ids_action('documents')
    except (UninitializedError, RequestFailedError) as e:
        print e
        return


@ltk.command()
@click.option('-n', '--doc_name', help='specific document name to get status of')
def status(doc_name):
    """ gets the status of a specific document or all documents """
    try:
        action = actions.Action(os.getcwd())
        action.status_action(doc_name)
    except (UninitializedError, ResourceNotFound) as e:
        print e
        return


@ltk.command()
@click.option('-a', '--auto_format', flag_value=True, help='flag to auto apply formatting during download')
@click.option('-l', '--locale', help='specific locale to download, defaults to source document')
@click.argument('document_names', required=True, nargs=-1)
def download(auto_format, locale, document_names):
    """ downloads translated content of document(s) """
    try:
        action = actions.Action(os.getcwd())
        for name in document_names:
            action.download_by_name(name, locale, auto_format)
    except (UninitializedError, ResourceNotFound, RequestFailedError) as e:
        print e
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
        print e
        return


def delete():
    pass


if __name__ == '__main__':
    ltk()
