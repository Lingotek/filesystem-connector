import requests
from ltk.api_uri import API_URI
import ltk.utils
from ltk.exceptions import RequestFailedError
from ltk.logger import logger


class ApiCalls:
    def __init__(self, host, access_token):
        self.host = host
        self.headers = {'Authorization': 'bearer ' + access_token}
        # self.cert = ('lingotek.crt', 'lingotek.key')

    def list_communities(self):
        """ gets the communities that a user is in """
        uri = API_URI['community']
        payload = {'limit': 100}
        r = requests.get(self.host + uri, headers=self.headers, params=payload)
        log_api('GET', uri, r)
        return r

    def list_projects(self, community_id):
        """ gets the projects a user has """
        uri = API_URI['project']
        payload = {'community_id': community_id, 'limit': 100}
        r = requests.get(self.host + uri, headers=self.headers, params=payload)
        log_api('GET', uri, r)
        return r

    def add_project(self, project_name, community_id, workflow_id):
        """ adds a project """
        uri = API_URI['project']
        payload = {'title': project_name, 'community_id': community_id, 'workflow_id': workflow_id}
        r = requests.post(self.host + uri, headers=self.headers, data=payload)
        log_api('POST', uri, r)
        return r

    def patch_project(self, project_id, workflow_id):
        """ updates a project """
        uri = (API_URI['project_id'] % locals())
        payload = {'project_id': project_id}
        if workflow_id:
            payload['workflow_id'] = workflow_id
        r = requests.patch(self.host + uri, headers=self.headers, data=payload)
        log_api('PATCH', uri, r)
        return r

    def project_add_target(self, project_id, locale, due_date):
        """ adds a target to all documents within a project """
        uri = (API_URI['project_translation'] % locals())
        payload = {'id': project_id, 'locale_code': locale}
        if due_date:
            payload['due_date'] = due_date
        r = requests.post(self.host + uri, headers=self.headers, data=payload)
        log_api('POST', uri, r)
        return r

    def project_status(self, project_id):
        """ gets the status of a project """
        uri = (API_URI['project_status'] % locals())
        r = requests.get(self.host + uri, headers=self.headers)
        log_api('GET', uri, r)
        return r

    def project_delete_target(self, project_id, locale):
        uri = (API_URI['project_translation_locale'] % locals())
        r = requests.delete(self.host + uri, headers=self.headers)
        log_api('DELETE', uri, r)
        return r

    def delete_project(self, project_id):
        """ deletes a project """
        uri = (API_URI['project_id'] % locals())
        r = requests.delete(self.host + uri, headers=self.headers)
        log_api('DELETE', uri, r)
        return r

    def get_document(self, document_id):
        """ gets a document by id """
        uri = (API_URI['document_id'] % locals())
        r = requests.get(self.host + uri, headers=self.headers)
        log_api('GET', uri, r)
        return r

    def add_document(self, file_name, locale, project_id, title, **kwargs):
        """ adds a document """
        uri = API_URI['document']
        payload = {'locale_code': locale, 'project_id': project_id, 'title': title}
        for key in kwargs:
            if kwargs[key]:
                payload[key] = kwargs[key]
        detected_format = ltk.utils.detect_format(file_name)
        if 'format' not in kwargs and detected_format != 'PLAINTEXT_OKAPI':
            payload['format'] = detected_format
        document = open(file_name, 'rb')
        files = {'content': (file_name, document)}
        r = requests.post(self.host + uri, headers=self.headers, data=payload, files=files)
        log_api('POST', uri, r)
        document.close()
        return r

    def document_add_target(self, document_id, locale, workflow_id=None, due_date=None):
        """ adds a target to existing document, starts the workflow """
        uri = (API_URI['document_translation'] % locals())
        payload = {'locale_code': locale, 'id': document_id}
        if workflow_id:
            payload['workflow_id'] = workflow_id
        if due_date:
            payload['due_date'] = due_date
        r = requests.post(self.host + uri, headers=self.headers, data=payload)
        log_api('POST', uri, r)
        return r

    def list_documents(self, project_id):
        """ lists all documents a user has access to, could be filtered by project id """
        uri = API_URI['document']
        payload = {}
        if project_id:
            payload = {'project_id': project_id, 'limit': 1000}
        r = requests.get(self.host + uri, headers=self.headers, params=payload)
        log_api('GET', uri, r)
        return r

    def document_status(self, document_id):
        """ gets the status of a document """
        uri = (API_URI['document_status'] % locals())
        payload = {'document_id': document_id}
        r = requests.get(self.host + uri, headers=self.headers, params=payload)
        # logger.debug(r.url)
        log_api('GET', uri, r)
        return r

    def document_translation_status(self, document_id):
        """ gets the status of document translations """
        uri = (API_URI['document_translation'] % locals())
        r = requests.get(self.host + uri, headers=self.headers)
        log_api('GET', uri, r)
        return r

    def document_content(self, document_id, locale_code, auto_format):
        """ downloads the translated document """
        uri = (API_URI['document_content'] % locals())
        payload = {}
        if locale_code:
            payload['locale_code'] = locale_code
        if auto_format:
            payload['auto_format'] = auto_format
        r = requests.get(self.host + uri, headers=self.headers, params=payload, stream=True)
        log_api('GET', uri, r)
        return r

    def document_update(self, document_id, file_name=None, **kwargs):
        uri = (API_URI['document_id'] % locals())
        payload = {'id': document_id}
        for key in kwargs:
            if kwargs[key]:
                payload[key] = kwargs[key]
        if file_name:
            document = open(file_name, 'rb')
            files = {'content': (file_name, document)}
            r = requests.patch(self.host + uri, headers=self.headers, data=payload, files=files)
            document.close()
        else:
            r = requests.patch(self.host + uri, headers=self.headers, data=payload)
        log_api('PATCH', uri, r)        
        return r

    def document_delete_target(self, document_id, locale):
        uri = (API_URI['document_translation_locale'] % locals())
        r = requests.delete(self.host + uri, headers=self.headers)
        log_api('DELETE', uri, r)
        return r

    def document_delete(self, document_id):
        uri = (API_URI['document_id'] % locals())
        r = requests.delete(self.host + uri, headers=self.headers)
        log_api('DELETE', uri, r)
        return r

    def list_workflows(self, community_id):
        uri = API_URI['workflow']
        payload = {'community_id': community_id}
        r = requests.get(self.host + uri, headers=self.headers, params=payload)
        log_api('GET', uri, r)
        return r

    def list_locales(self):
        uri = 'http://gmc.lingotek.com/v1/locales'
        r = requests.get(uri)
        return r

    def list_filters(self):
        uri = API_URI['filter']
        r = requests.get(self.host + uri, headers=self.headers)
        log_api('GET', uri, r)
        return r

    def get_project_info(self, community_id):
        response = self.list_projects(community_id)
        info = {}
        if response.status_code == 200:
            if int(response.json()['properties']['total']) == 0:
                return info
            entities = response.json()['entities']
            for entity in entities:
                info[entity['properties']['id']] = entity['properties']['title']
            return info
        elif response.status_code == 204:
            return info
        else:
            raise RequestFailedError("Unable to get existing projects")

    def get_communities_info(self):
        response = self.list_communities()
        if response.status_code != 200:
            raise RequestFailedError("Unable to get user's list of communities")
        entities = response.json()['entities']
        info = {}
        for entity in entities:
            info[entity['properties']['id']] = entity['properties']['title']
        return info


def log_api(method, uri, response):
    try:
        content_length = response.headers['content-length']
    except KeyError:
        content_length = 'No content-length header'
    log = '{method} {uri} {status} {length}'.format(method=method, uri=uri, status=response.status_code,
                                                    length=content_length)
    logger.api_call(log)
    try:
        import json
        response_info = json.dumps(response.json(), indent=4, separators=(',', ': '))
    except ValueError:
        response_info = 'No json response available'
    logger.api_response(response_info)
