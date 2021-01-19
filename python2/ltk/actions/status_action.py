from ltk.actions.action import *
from tabulate import tabulate

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
                doc_id = self.get_latest_document_version(doc_id) or doc_id
                self._get_status_of_doc(doc_id, detailed)
        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to Lingotek")
            exit()
        except ValueError:
            logger.warning("Could not connect to Lingotek")
            exit()
        # Python 3
#         #except json.decoder.JSONDecodeError:
#             #logger.warning("Could not connect to Lingotek")
#             #exit()
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
                #title = entry['entities'][0]['properties']['title']
                #progress = entry['entities'][0]['properties']['progress']
                #self._print_status(title, progress)
                #if detailed:
                #    self._print_detailed_status(entry['properties']['id'], title)
                self._get_status_of_doc(entry['properties']['id'], detailed)

    def _get_status_of_doc(self, doc_id, detailed):
        doc_id = self.get_latest_document_version(doc_id) or doc_id
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
                self._get_process(entry)
        else:
            title = response.json()['properties']['title']
            progress = response.json()['properties']['progress']
            statustext = response.json()['properties']['status'].upper()
            self._print_status(title, doc_id, progress, statustext)
            if detailed:
                self._print_detailed_status(doc_id, title)

    def _get_process(self, entry):
        if 'process_id' not in entry:
            error_message = "Check Lingotek TMS to see if \'"+entry['file_name']+"\' has been deleted or was not properly imported"
            raise_error("", "Not Found: "+error_message, True, entry['id'])
            return
        process_id = entry['process_id']
        if process_id == 'imported':#documents added with ltk import -t don't come with a process id, so they get set to 'imported'
            error_message = "Check Lingotek TMS to see if \'"+entry['file_name']+"\' has been deleted"
            raise_error("", "Not Found: "+error_message, True, entry['id'])
            return
        response = self.api.get_process(process_id)
        if response.status_code == 404:
            # The process doesn't exist for some reason
            self._failed_entry(entry['id'], entry['name'])
        else:
            status = response.json()['properties']['status']
            progress = response.json()['properties']['progress']
            if status.lower() == 'in_progress':
                # Process is currently in progress. Replaces need for upload wait time since now we can get the
                # current document process progress.
                print('Uploading document {0}: {1}% complete'.format(entry['name'], progress))
            elif status.lower() == 'completed':
                # Process is completed and the document was uploaded to TMS, but there was an error in getting the document status
                # Seems to happen when the document is deleted from within TMS
                print('Document {0} was imported, but could not be found within TMS. You may need to run ltk clean to update the local database'.format(entry['name']))
            else:
                # Process has a failed status
                self._failed_entry(entry['id'], entry['name'])

    def _failed_entry(self, doc_id, name):
        error_message = "\'"+name+"\' failed to import properly"
        raise_error("", "Not Found: "+error_message, True, doc_id)
        self.doc_manager.remove_element(doc_id)
        # Process has failed status/does not exist, so document info is
        # deleted from the local database

    def _print_status(self, title, doc_id, progress, statustext):
        print ('{0} ({1}): {2}% ({3})'.format(title, doc_id, progress, statustext))
        # print title + ': ' + str(progress) + '%'
        # for each doc id, also call /document/id/translation and get % of each locale

    def _print_detailed_status(self, doc_id, doc_name):
        doc_id = self.get_latest_document_version(doc_id) or doc_id
        response = self.api.document_translation_status(doc_id)
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get detailed status of document', True, doc_id, doc_name)
        try:
            # print(response.json())
            if 'entities' in response.json():
                for entry in response.json()['entities']:
                    curr_locale = entry['properties']['locale_code']
                    curr_progress = entry['properties']['percent_complete']
                    curr_statustext = entry['properties']['status']
                    # print ('\tlocale: {0} \t percent complete: {1}%'.format(curr_locale, curr_progress))
                    if 'entities' in entry:
                        for entity in entry['entities']:
                            if entity['rel'][0] == 'phases':
                                if 'entities' in entity:
                                    table = []
                                    for phase in entity['entities']:
                                        phase_name = phase['properties']['name']
                                        phase_order = phase['properties']['order']
                                        phase_percent_complete = phase['properties']['percent_completed']
                                        phase_status = phase['properties']['status']
                                        table.append({"Phase": str(phase_order), "Name": phase_name, "Status": phase_status, "Phase Percent Complete": str(phase_percent_complete) + '%'})
                                    table.sort(key=lambda x: x['Phase'])
                                    print('\n')
                                    print('Locale: {0} \t Total Percent Complete: {1}% ({2})\n'.format(curr_locale, curr_progress, curr_statustext))
                                    # print('Locale: {0} \n'.format(curr_locale))
                                    print(tabulate(table, headers="keys"))
                                    
                    # detailed_status[doc_id] = (curr_locale, curr_progress)
        except KeyError as e:
            log_error(self.error_file_name, e)
            print("Error listing translations")
            return
            # return detailed_status
