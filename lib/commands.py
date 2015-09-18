import click
import processes
import os

@click.group()
def ltk():
    pass

@ltk.command()
@click.option('--access_token', prompt='Enter your access token', help='your access token')
@click.option('--host', type=click.Choice(['myaccount.lingotek.com', 'cms.lingotek.com']), default='cms.lingotek.com',
              help='defaults to cms.lingotek.com')
@click.option('--path', type=click.Path(exists=True), help='the path to the project directory to be initialized, defaults to current directory')
@click.option('-n', '--project_name', help='the preferred project name, defaults to current directory name')
def init(host, access_token, path, project_name):
    """ initializes a Lingotek project """
    host = 'https://' + host
    click.echo("token: %s" % access_token)
    click.echo("path: %s" % path)
    click.echo("project name: %s" % project_name)
    click.echo("host: %s" % host)
    if not path:
        path = os.getcwd()
    if not project_name:
        project_name = os.path.basename(os.path.normpath(path))
    click.echo("project name: %s" % project_name)
    # processes.init_process(host, access_token, path, project_name)

@ltk.command()
@click.option('-f', '--file_path', type=click.Path(exists=True), help='path to your file(s)')
def add(file_path):
    """ command to add content """
    pass

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
