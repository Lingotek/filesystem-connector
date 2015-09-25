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

    def list_projects(self, community_id):
        """ gets the projects a user has """
        uri = self.host + api_uri.API_URI['project']
        payload = {'community_id': community_id}
        r = requests.get(uri, headers=self.headers, params=payload)
        return r

    def add_project(self, project_name, community_id, workflow_id):
        """ adds a project and returns the project id """
        uri = self.host + api_uri.API_URI['project']
        payload = {'title': project_name, 'community_id': community_id, 'workflow_id': workflow_id}
        r = requests.post(uri, headers=self.headers, data=payload)
        return r

    def add_target_project(self, project_id, locale, due_date):
        """ adds a target to all documents within a project """
        uri = self.host + (api_uri.API_URI['project_translation'] % locals())
        payload = {'id': project_id, 'locale_code': locale}
        if due_date:
            payload['due_date'] = due_date
        r = requests.post(uri, headers=self.headers, data=payload)
        return r

    def project_status(self, project_id):
        """ gets the status of a project """
        uri = self.host + (api_uri.API_URI['project_status'] % locals())
        r = requests.get(uri, headers=self.headers)
        return r

    def delete_project(self, project_id):
        """ deletes a project """
        uri = self.host + (api_uri.API_URI['project_id'] % locals())
        r = requests.delete(uri, headers=self.headers)
        return r.status_code

    def add_document(self, document_name, file_name, locale, project_id):  # todo add all those optional params
        """ adds a document """
        uri = self.host + api_uri.API_URI['document']
        payload = {'title': document_name, 'locale_code': locale, 'project_id': project_id}
        files = {'content': (file_name, open(file_name, 'rb'))}
        r = requests.post(uri, headers=self.headers, data=payload, files=files)
        return r

    def add_target_document(self, document_id, locale, workflow_id=None, due_date=None):
        """ adds a target to existing document, starts the workflow """
        uri = self.host + (api_uri.API_URI['document_translation'] % locals())
        payload = {'locale_code': locale, 'id': document_id}
        if workflow_id:
            payload['workflow_id'] = workflow_id
        if due_date:
            payload['due_date'] = due_date
        r = requests.post(uri, headers=self.headers, data=payload)
        return r

    def list_documents(self, project_id):
        """ lists all documents a user has access to, could be filtered by project id """
        uri = self.host + api_uri.API_URI['document']
        payload = {}
        if project_id:
            payload = {'project_id': project_id}
        r = requests.get(uri, headers=self.headers, params=payload)
        return r

    def document_status(self, document_id):
        """ gets the status of a document """
        uri = self.host + (api_uri.API_URI['document_status'] % locals())
        payload = {'document_id': document_id}
        r = requests.get(uri, headers=self.headers, params=payload)
        return r

    def document_content(self, document_id, locale_code, auto_format):
        """ downloads the translated document """
        uri = self.host + (api_uri.API_URI['document_content'] % locals())
        payload = {}
        if locale_code:
            payload['locale_code'] = locale_code
        # todo find out how auto format flag is requested
        # if auto_format:
        #     payload['auto_format'] = auto_format
        r = requests.get(uri, headers=self.headers, params=payload)
        return r

    def list_workflows(self, community_id):
        uri = self.host + api_uri.API_URI['workflow']
        payload = {'community_id': community_id}
        r = requests.get(uri, headers=self.headers, params=payload)
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
