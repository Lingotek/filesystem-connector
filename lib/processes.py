import ConfigParser
import os
import shutil
import config
import api_calls as api

def init_config(host, access_token, community_id, project_id):
    config.HOST = host
    config.ACCESS_TOKEN = access_token
    config.COMMUNITY_ID = community_id
    config.PROJECT_ID = project_id

def init_process(host, access_token, project_path, project_name):
    # check if Lingotek directory already exists
    if os.path.isdir(os.path.join(project_path, '.Lingotek')):
        # todo: re-initialize
        confirm = False
        # confirm if would like to delete existing folder
        if not confirm:
            return
        else:
            # delete existing folder
            # todo delete corresponding project in cms?
            to_remove = os.path.join(project_path, '.Lingotek')
            shutil.rmtree(to_remove)

    # create a directory
    os.mkdir(os.path.join(project_path, '.Lingotek'))

    config_file_name = os.path.join(project_path, '.Lingotek', 'conf')
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

        # todo handle when project already exists in host
        # create project / get project id
        response = api.add_project(project_name, community_id)
        project_id = response['properties']['id']
        config_parser.set('main', 'project_id', project_id)

        config_parser.write(config_file)
        config_file.close()
        init_config(host, access_token, community_id, project_id)
