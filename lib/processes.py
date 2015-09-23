import ConfigParser
import os
import shutil
import config
from apicalls import ApiCalls


def init_config(host, access_token, community_id, project_id):
    config.HOST = host
    config.ACCESS_TOKEN = access_token
    config.COMMUNITY_ID = community_id
    config.PROJECT_ID = project_id


def init_process(host, access_token, project_path, project_name):
    api = ApiCalls(host, access_token)
    # check if Lingotek directory already exists
    if os.path.isdir(os.path.join(project_path, '.Lingotek')):
        # todo: re-initialize
        confirm = 'not confirmed'
        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
            confirm = raw_input("Do you want to delete the existing project and create a new one? This will also delete the project in your community. [y/n]: ")
        # confirm if would like to delete existing folder
        if not confirm or confirm in ['n', 'N']:
            return
        else:
            # delete the corresponding project online
            config_file_name = os.path.join(project_path, '.Lingotek', 'Lingotek.cfg')
            if os.path.isfile(config_file_name):
                old_config = ConfigParser.ConfigParser()
                old_config.read(config_file_name)
                project_id = old_config.get('main', 'project_id')
                del_status = api.delete_project(project_id)
                if del_status != 204:
                    # todo raise error
                    print 'not successfully deleted'
                # delete existing folder
                to_remove = os.path.join(project_path, '.Lingotek')
                shutil.rmtree(to_remove)
            else:
                # todo raise error
                print 'no config file'

    # create a directory
    os.mkdir(os.path.join(project_path, '.Lingotek'))

    config_file_name = os.path.join(project_path, '.Lingotek', 'Lingotek.cfg')
    if not os.path.exists(config_file_name):
        # create the config file and add info
        config_file = open(config_file_name, 'w')

        config_parser = ConfigParser.ConfigParser()
        config_parser.add_section('main')
        config_parser.set('main', 'access_token', access_token)
        config_parser.set('main', 'host', host)

        # get community id
        community_ids = api.get_community_ids()
        if len(community_ids) > 1:
            # todo handle when user in multiple communities
            community_id = ''
            pass
        else:
            community_id = community_ids[0]
        config_parser.set('main', 'community_id', community_id)

        # todo handle when project already exists online
        response = api.add_project(project_name, community_id)
        if response.status_code != 201:
            # todo raise error
            pass
        project_id = response.json()['properties']['id']
        config_parser.set('main', 'project_id', project_id)

        config_parser.write(config_file)
        config_file.close()
        init_config(host, access_token, community_id, project_id)
