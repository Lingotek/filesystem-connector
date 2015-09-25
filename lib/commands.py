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
@click.option('-f', '--file_path', type=click.Path(exists=True), help='path to your file')
@click.option('-p', '--file_pattern', help='name or pattern of files to look for')
@click.argument('locale', required=True, nargs=1)
@click.option('-n', '--name', help='the title of the document, defaults to file name')
def add(file_path, locale, name, file_pattern):
    """ add content """
    if not file_path:
        file_path = os.getcwd()
    try:
        action = actions.Action(file_path)
        action.add_action(locale, file_pattern, file_path, name)
    except UninitializedError as e:
        # todo log the error somewhere
        print e
        return
        # processes.add_action(locale, file_path, file_pattern)


@ltk.command()
def push():
    """ push all your added content to Lingotek """
    pass


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
@click.option('-l', '--locale', help='specific locale to download, defaults to all added locale')
@click.argument('ids', required=True, nargs=-1)
def download():
    pass

def pull():
    pass


def delete():
    pass

if __name__ == '__main__':
    # init_parser()
    # request_parser()
    ltk()
