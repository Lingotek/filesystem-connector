from ltk.actions.action import *

class StatusAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.uploadWaitTime = 300

    def get_status(self, **kwargs):
        try:
            doc_name = None
            detailed = False

            if 'detailed' in kwargs and kwargs['detailed']:
                detailed = True
            if 'doc_name' in kwargs:
                doc_name = kwargs['doc_name']

            if 'all' in kwargs and kwargs['all']:
                self._get_all_status(detailed)
                return
            else:
                doc_ids = self._get_doc_ids(doc_name)
                if not doc_ids:
                    print("No documents to report")
                    return

            for doc_id in doc_ids:
                self._get_status_of_doc(doc_id, detailed)
        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to Lingotek")
            exit()
        except ValueError:
            logger.warning("Could not connect to Lingotek")
            exit()
        # Python 3
        #except json.decoder.JSONDecodeError:
            #logger.warning("Could not connect to Lingotek")
            #exit()
        # End Python 3
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.warning("Error on requesting status: "+str(e))

    def _get_doc_ids(self, doc_name):
        if doc_name is not None:
            entry = self.doc_manager.get_doc_by_prop('name', doc_name)
            try:
                doc_ids = [entry['id']]
            except TypeError:
                raise exceptions.ResourceNotFound("Document name specified for status doesn't exist: {0}".format(doc_name))
        else:
            doc_ids = self.doc_manager.get_doc_ids()

        return doc_ids

    def _get_all_status(self, detailed):
        response = self.api.list_documents(self.project_id)
        if response.status_code == 204:
            print("No documents to report")
            return
        elif response.status_code != 200:
            if check_response(response):
                raise_error(response.json(), "Failed to get status of documents", True)
            else:
                raise_error("", "Failed to get status of documents", True)
        else:
            for entry in response.json()['entities']:
                title = entry['entities'][0]['properties']['title']

                progress = entry['entities'][0]['properties']['progress']
                self._print_status(title, progress)
                if detailed:
                    self.print_detailed(entry['properties']['id'], title)

    def _get_status_of_doc(self, doc_id, detailed):
        response = self.api.document_status(doc_id)
        if response.status_code != 200:
            entry = self.doc_manager.get_doc_by_prop('id', doc_id)
            if entry:
                error_message = "Failed to get status of document "+entry['file_name']
            else:
                error_message = "Failed to get status of document "+str(doc_id)
            if check_response(response):
                raise_error(response.json(), error_message, True, doc_id)
            else:
                #if document has recently been added, determined by uploadWaitTime, let user know that document is still being processed
                #otherwise, suggest that user check TMS for deletion or potential upload problems
                entry = self.doc_manager.get_doc_by_prop('id', doc_id)
                diff = time.time() - entry['added']
                if diff < self.uploadWaitTime:
                    error_message = "\'" +entry['file_name']+ "\' is still being processed"
                    raise_error("", str(response.status_code)+" Not Found: "+error_message, True, doc_id)
                else:
                    error_message = "Check Lingotek TMS to see if \'" +entry['file_name']+ "\' has been deleted or was not properly imported"
                    raise_error("", str(response.status_code)+" Not Found: "+error_message, True, doc_id)
        else:
            title = response.json()['properties']['title']
            progress = response.json()['properties']['progress']
            self._print_status(title, progress)
            if detailed:
                self._print_detailed_status(doc_id, title)

    def _print_status(self, title, progress):
        print ('{0}: {1}%'.format(title, progress))
        # print title + ': ' + str(progress) + '%'
        # for each doc id, also call /document/id/translation and get % of each locale

    def _print_detailed_status(self, doc_id, doc_name):
        response = self.api.document_translation_status(doc_id)
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get detailed status of document', True, doc_id, doc_name)
        try:
            if 'entities' in response.json():
                for entry in response.json()['entities']:
                    curr_locale = entry['properties']['locale_code']
                    curr_progress = entry['properties']['percent_complete']
                    print ('\tlocale: {0} \t percent complete: {1}%'.format(curr_locale, curr_progress))
                    # detailed_status[doc_id] = (curr_locale, curr_progress)
        except KeyError as e:
            log_error(self.error_file_name, e)
            print("Error listing translations")
            return
            # return detailed_status
