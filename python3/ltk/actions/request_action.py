from ltk.actions.action import *

class RequestAction(Action):
    def __init__(self, actionPath, doc_name, requestPath, entered_locales, to_cancel, to_delete, due_date, workflow, document_id=None, surpressMessage=False):
        Action.__init__(self, actionPath)

        self.document_name = doc_name
        self.requestPath = requestPath
        self.entered_locales = entered_locales
        self.to_cancel = to_cancel
        self.to_delete = to_delete
        self.workflow = workflow
        self.due_date = due_date
        self.document_id = document_id
        self.surpressMessage = surpressMessage

        self.expected_code = ''
        self.failure_message = ''
        self.info_message = ''
        self.change_db_entry = ''
        self.docs = []

    def target_action(self):
        try:
            is_successful = False
            locales = []
            if self.entered_locales:
                for locale in self.entered_locales:
                    locales.extend(locale.split(','))
                if self.to_delete:
                    locales = get_valid_locales(self.api, locales, 'deleted')
                elif self.to_cancel:
                    locales = get_valid_locales(self.api, locales, 'cancelled')
                else:
                    locales = get_valid_locales(self.api, locales, 'added')
            elif self.watch_locales:
                locales = self.watch_locales
            elif self.surpressMessage:
                # don't print out anything when on watch
                return False
            else:
                logger.info('No locales have been set. Locales can be passed in as arguments or set as target locales in ltk config.')
                return False
            if self.requestPath:
                self.document_id = None
                self.document_name = None
            self.change_db_entry = True
            if self.to_delete:
                if not self.entered_locales:
                    logger.error("Please enter a target locale to delete")
                    return
                self.expected_code = 204
                self.failure_message = 'Failed to delete target'
                self.info_message = 'Deleted locale'
            elif self.to_cancel:
                if not self.entered_locales:
                    logger.error("Please enter a target locale to cancel")
                    return
                self.expected_code = 204
                self.failure_message = 'Failed to cancel target'
                self.info_message = 'Cancelled locale'
            else:
                self.expected_code = 201
                self.failure_message = 'Failed to add target'
                self.info_message = 'Added target'
            # print("doc_name: "+str(document_name))
            if not self.requestPath and not self.document_name and not self.document_id:
                self.docs = self.doc_manager.get_all_entries()
            elif self.requestPath:
                self.docs = self.get_docs_in_path(self.requestPath)
            else:
                if self.document_id:
                    entry = self.doc_manager.get_doc_by_prop('id', self.document_id)
                    if not entry:
                        logger.error('Document specified for target doesn\'t exist: {0}'.format(self.document_id))
                        return
                elif self.document_name:
                    entry = self.doc_manager.get_doc_by_prop('name', self.document_name)
                    if not entry:
                        logger.error('Document name specified for target doesn\'t exist: {0}'.format(self.document_name))
                        return
                        # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
                if not entry:
                    logger.error('Could not add target. File specified is invalid.')
                    return
                self.docs.append(entry)
            if len(self.docs) == 0:
                if self.requestPath and len(self.requestPath) > 0:
                    logger.info("File "+str(self.requestPath)+" not found")
                else:
                    logger.info("No documents to request a target locale")

            is_successful = self._request_translations(locales)
            return is_successful
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on request: "+str(e))

    def _request_translations(self, locales):
        for entry in self.docs:
            if not self._handleEntryRequest(entry, locales):
                return False
        return True
       

    def _handleEntryRequest(self, entry, locales):
        is_successful = False
        self.document_id = entry['id']
        self.document_name = entry['file_name']
        existing_locales = []
        if 'locales' in entry and entry['locales']:
            existing_locales = entry['locales']
        for locale in locales:
            locale = locale.replace('_','-')
            if self.to_delete:
                response = self.api.document_delete_target(self.document_id, locale)
            elif self.to_cancel:
                response = self.api.document_cancel_target(self.document_id, locale)
            else:
                response = self.api.document_add_target(self.document_id, locale, self.workflow, self.due_date)
            if self.expected_code == 201: # Request target
                if response.status_code == 202:
                    if 'next_document_id' in response.json():
                        self.doc_manager.update_document('id', response.json()['next_document_id'], self.document_id)
                        self.document_id = response.json()['next_document_id']
                elif response.status_code == 402:
                    raise_error(response.json(), "", True)
                elif response.status_code == 410:
                    logger.info("Document has been archived. Reuploading...")
                    target_locales = existing_locales
                    if locale not in existing_locales:
                        target_locales.append(locale)
                    title = entry['name']
                    self.doc_manager.remove_element(self.document_id)
                    self.add_document(self.document_name, title, self.default_metadata, translation_locale_code=target_locales)
                    return
                elif response.status_code == 423:
                    if 'next_document_id' in response.json():
                        self.doc_manager.update_document('id', response.json()['next_document_id'], self.document_id)
                        self.document_id = response.json()['next_document_id']
                        self._handleEntryRequest(entry, [locale])
                    else:
                        raise_error(response.json(), "Document was locked but no next document id provided", False)
            if response.status_code != self.expected_code:
                if (response.json() and response.json()['messages']):
                    response_message = response.json()['messages'][0]
                    response_message = response_message.replace(self.document_id, self.document_name + ' (' + self.document_id + ')')
                    response_message = response_message.replace('.', ' ')
                    response_message = response_message + 'for document ' + self.document_name
                    print(response_message + "\n")
                    #if 'not found' in response_message:
                        #return
                else:
                    raise_error(response.json(), '{message} {locale} for document {name}\n'.format(message=self.failure_message, locale=locale, name=self.document_name), True)
                if not 'already exists' in response_message:
                    self.change_db_entry = False
                # self.update_doc_locales(document_id)
                continue
            logger.info('{message} {locale} for document {name}\n'.format(message=self.info_message, locale=locale, name=self.document_name))
        remote_locales = self.get_doc_locales(self.document_id, self.document_name) # Get locales from Lingotek Cloud
        locales_to_add = []
        existing_locales = []
        if 'locales' in entry and entry['locales']:
            existing_locales = entry['locales']
        if self.change_db_entry:
            # Make sure that the locales that were just added are added to the database as well as the previous remote locales (since they were only just recently added to Lingotek's system)
            if (self.to_delete or self.to_cancel) and self.entered_locales:
                locales_to_add = locales
            else:
                if remote_locales:
                    for locale in remote_locales:
                        if locale not in locales:
                            locales_to_add.append(locale)

                for locale in locales:
                    locale = locale.replace('_', '-')
                    if locale not in existing_locales and locale not in locales_to_add:
                        locales_to_add.append(locale)
            if self.to_delete:
                self._target_action_db(self.to_delete, locales_to_add, self.document_id)
            else:
                self._target_action_db(self.to_cancel, locales_to_add, self.document_id)
            #self._target_action_db((self.to_delete or self.to_cancel), locales_to_add, self.document_id)
            is_successful = True

        return is_successful