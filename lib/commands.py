import click
import actions
# from actions import Action
import os
from exceptions import UninitializedError


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
    """ command to add content """
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
@click.option('-p', '--is_project', is_flag=True, flag_value=True, help='whether or not this is a project')
@click.argument('id', nargs=1)
@click.argument('locales', required=True, nargs=-1)  # can have unlimited number of locales
@click.option('-d', '--due_date', help='the due date of the translation')
@click.option('-w', '--workflow', help='the workflow of the translation')
def request(id, locales, is_project, due_date, workflow):
    # possibly want to be able to request multiple docs/locales at once?
    print 'is project? ' + str(is_project)
    for locale in locales:
        click.echo("locale: %s" % locale)
    click.echo("id: %s" % id)


# todo come up with a better word for this
# def list():
#     pass

def pull():
    pass


def delete():
    pass


def status():
    pass


if __name__ == '__main__':
    # init_parser()
    # request_parser()
    ltk()
