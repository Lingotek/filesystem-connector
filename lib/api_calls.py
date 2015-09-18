import requests
import api_uri
import config

# class api_calls():
#     def __init__(self):
#         pass

def list_communities():
    """ gets the communities that a user is in """
    uri = config.HOST + api_uri.API_CALLS['community']
    headers = {'Authorization': 'bearer ' + config.ACCESS_TOKEN}
    r = requests.get(uri, headers=headers)
    return r.json()

def list_projects():
    """ gets the projects a user has """
    pass

def add_project(project_name, communtiy_id):
    """ adds a project and returns the project id """
    uri = config.HOST + api_uri.API_CALLS['project']
    headers = {'Authorization': 'bearer ' + config.ACCESS_TOKEN}
    payload = {'title': project_name, 'community_id': communtiy_id, 'workflow_id': config.WORKFLOW_ID}
    r = requests.post(uri, headers=headers, data=payload)
    return r.json()

def get_community_ids():
    json = list_communities()
    entities = json['entities']
    ids = []
    for entity in entities:
        ids.append(entity['properties']['id'])
    return ids


# if __name__ == '__main__':
#     list_communities()
