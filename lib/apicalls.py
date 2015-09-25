import requests
import api_uri
import config

# todo: handle errors

class ApiCalls:
    def __init__(self, host, access_token):
        self.host = host
        self.headers = {'Authorization': 'bearer ' + access_token}

    def list_communities(self):
        """ gets the communities that a user is in """
        uri = self.host + api_uri.API_URI['community']
        r = requests.get(uri, headers=self.headers)
        return r

    def list_projects(self):
        """ gets the projects a user has """
        pass

    def add_project(self, project_name, community_id, workflow_id):
        """ adds a project and returns the project id """
        uri = self.host + api_uri.API_URI['project']
        payload = {'title': project_name, 'community_id': community_id, 'workflow_id': workflow_id}
        r = requests.post(uri, headers=self.headers, data=payload)
        return r

    def add_target_project(self, project_id, locale):
        """ adds a target to all documents within a project """
        uri = self.host + (api_uri.API_URI['project_translation'] % locals())
        payload = {'id': project_id, 'locale_code': locale}
        r = requests.post(uri, headers=self.headers, data=payload)

    def delete_project(self, project_id):
        """ deletes a project """
        uri = self.host + (api_uri.API_URI['project_id'] % locals())
        r = requests.delete(uri, headers=self.headers)
        return r.status_code

    def add_document(self, document_name, file_name, locale, project_id):  # todo add all those optional params
        uri = self.host + api_uri.API_URI['document']
        payload = {'title': document_name, 'locale_code': locale, 'project_id': project_id}
        files = {'content': (file_name, open(file_name, 'rb'))}
        r = requests.post(uri, headers=self.headers, data=payload, files=files)
        return r

    def get_community_ids(self):
        response = self.list_communities()
        if response.status_code != 200:
            print response.json()
            print 'error getting community ids'
            # todo raise error
        entities = response.json()['entities']
        ids = []
        for entity in entities:
            ids.append(entity['properties']['id'])
        return ids


# def test(project_id):
    # project_id = "123"
    # print (api_uri.API_CALLS['project_id'] % locals())

# if __name__ == '__main__':
#     code = delete_project('5daa76ff-3a88-4466-a970-812edc79cb66')
#     print code
    # test('9873249283')
#     list_communities()
