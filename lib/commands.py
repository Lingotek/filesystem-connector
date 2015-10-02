import click
import actions
# from actions import Action
import os
from exceptions import UninitializedError, ResourceNotFound, NoIdSpecified


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
    click.echo("project name: %s" % project_name)
    # action = actions.Action(path)
    # action.init_action(host, access_token, project_name)
    # processes.init_action(host, access_token, path, project_name)
    actions.init_action(host, access_token, path, project_name, workflow_id)


@ltk.command()
@click.argument('file_names', required=True, nargs=-1)
@click.argument('locale', required=True, nargs=1)
@click.option('--path', type=click.Path(exists=True), help='path to your file')
@click.option('-t', '--title', help='the title of the document, defaults to file name')
@click.option('-f', '--format', help='format of uploaded file(s), defaults to plaintext')
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
    except UninitializedError as e:
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
@click.option('-p', '--is_project', flag_value=True, help='whether or not this is a project')
@click.option('-d', '--document_id', help='the id of the document. please specify if project flag not set')
@click.option('--due_date', help='the due date of the translation')
@click.option('-w', '--workflow', help='the workflow of the translation')
@click.argument('locales', required=True, nargs=-1)  # can have unlimited number of locales
def request(document_id, locales, is_project, due_date, workflow):
    """ add targets to document or project to start translation """
    try:
        action = actions.Action(os.getcwd())
        action.request_action(document_id, is_project, locales, due_date, workflow)
    except (UninitializedError, ResourceNotFound, NoIdSpecified) as e:
        print e
        return

@ltk.command()
@click.option('-p', '--projects', flag_value=True, help='list project ids')
@click.option('-pid', '--project_id', help='project id to filter document ids by')
@click.option('-d', '--documents', flag_value=True, help='list document ids')
@click.option('-w', '--workflows', flag_value=True, help='list available workflow ids')
def ids(projects, documents, workflows, project_id):
    """ lists ids and titles of resources """
    # todo possibly add communities
    try:
        action = actions.Action(os.getcwd())
        if projects:
            # get projects
            action.list_ids_action('projects', project_id)
        if documents:
            # get documents
            action.list_ids_action('documents')
        if workflows:
            action.list_ids_action('workflows')
    except UninitializedError as e:
        print e
        return

@ltk.command()
@click.option('-p', 'status_type', flag_value='project', help='gets status of project')
@click.option('-d', 'status_type', flag_value='document', help='gets status of document')
@click.argument('ids', required=True, nargs=-1)
def status(status_type, ids):
    """ gets the status of a project or document """
    try:
        action = actions.Action(os.getcwd())
        for curr_id in ids:
            if status_type == 'project':
                action.status_action('project', curr_id)
            if status_type == 'document':
                action.status_action('document', curr_id)
    except UninitializedError as e:
        print e
        return

@ltk.command()
@click.option('-a', '--auto_format', flag_value=True, help='flag to auto apply formatting during download')
@click.option('-l', '--locale', help='specific locale to download, defaults to source document')
@click.argument('ids', required=True, nargs=-1)
def download(auto_format, locale, ids):
    """ downloads translated content of document(s) """
    try:
        action = actions.Action(os.getcwd())
        for curr_id in ids:
            action.download_action(curr_id, locale, auto_format)
    except UninitializedError as e:
        print e
        return

@ltk.command()
@click.option('-a', '--auto_format', flag_value=True, help='flag to auto apply formatting during download')
@click.option('-l', '--locale', help='specific locale to download, defaults to source document')
def pull(auto_format, locale):
    """ pulls all translations for added documents """
    try:
        action = actions.Action(os.getcwd())
        action.pull_action(locale, auto_format)
    except UninitializedError as e:
        print e
        return

def delete():
    pass

if __name__ == '__main__':
    # init_parser()
    # request_parser()
    ltk()
