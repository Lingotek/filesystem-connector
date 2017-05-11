from ltk.actions.action import *

class PullAction(Action):
    def __init__(self, path, download):
        Action.__init__(self, path)
        self.download = download

    def pull_translations(self, locale_code, locale_ext, no_ext, auto_format):
        try:
            if 'clone' in self.download_option and not locale_ext or (no_ext and not locale_ext):
                locale_ext = False
            else:
                locale_ext = True
            if not locale_code:
                entries = self.doc_manager.get_all_entries()
                if entries:
                    for entry in entries:
                        try:
                            locales = entry['locales']
                            for locale in locales:
                                locale = locale.replace('_','-')
                                self.download.download_action(entry['id'], locale, auto_format, locale_ext)
                        except KeyError:
                            self.download.download_action(entry['id'], None, auto_format, locale_ext)
                else:
                    logger.info("No documents have been added")
            else:
                document_ids = self.doc_manager.get_doc_ids()
                if document_ids:
                    for document_id in document_ids:
                        self.download_action(document_id, locale_code, auto_format, locale_ext)
                else:
                    logger.info("No documents have been added")
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on pull: "+str(e))
