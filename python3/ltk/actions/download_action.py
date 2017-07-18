from ltk.actions.action import *

class DownloadAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.download_root = ''
        self.download_path = ''
        self.DOWNLOAD_NUMBER = 1
        self.default_download_ext = "({0})".format(self.DOWNLOAD_NUMBER)
        self.current_doc = ''

    def download_by_path(self, file_path, locale_codes, locale_ext, no_ext, auto_format, xliff):
        docs = self.get_docs_in_path(file_path)
        if len(docs) == 0:
            logger.warning("No document found with file path "+str(file_path))
        if docs:
            for entry in docs:
                locales = []
                if locale_codes:
                    locales = locale_codes.split(",")
                elif 'locales' in entry:
                    locales = entry['locales']
                if 'clone' in self.download_option and not locale_ext or (no_ext and not locale_ext):
                    self.download_locales(entry['id'], locales, auto_format, xliff, False)
                else:
                    self.download_locales(entry['id'], locales, auto_format, xliff, True)

    def download_locales(self, document_id, locale_codes, auto_format, xliff, locale_ext=True):
        if locale_codes:
            for locale_code in locale_codes:
                locale_code = locale_code.replace("_","-")
                self.download_action(document_id, locale_code, auto_format, xliff, locale_ext)

    def download_action(self, document_id, locale_code, auto_format, xliff=False, locale_ext=True):
        try:
            response = self.api.document_content(document_id, locale_code, auto_format, xliff)
            entry = None
            entry = self.doc_manager.get_doc_by_prop('id', document_id)
            if response.status_code == 200:
                self.download_path = self.path
                if 'clone' in self.download_option:
                    if not locale_code:
                        print("Cannot download "+str(entry['file_name']+" with no target locale."))
                        return
                    self._clone_download(locale_code)
                elif 'folder' in self.download_option:
                    locale_code = locale_code.replace("-","_")
                    if locale_code in self.locale_folders:
                        if self.locale_folders[locale_code] == 'null':
                            logger.warning("Download failed: folder not specified for "+locale_code)
                        else:
                            self.download_path = self.locale_folders[locale_code]
                    else:
                        self.download_path = self.download_dir
                if not entry:
                    doc_info = self.api.get_document(document_id)
                    try:
                        file_title = doc_info.json()['properties']['title']
                        title, extension = os.path.splitext(file_title)
                        if not extension:
                            extension = doc_info.json()['properties']['extension']
                            extension = '.' + extension
                        if extension and extension != '.none':
                            title += extension
                    except KeyError as e:
                        log_error(self.error_file_name, e)
                        raise_error(doc_info.json(),
                                    'Something went wrong trying to download document: {0}'.format(document_id), True)
                        return
                    self.download_path = os.path.join(self.download_path, title)
                    logger.info('Downloaded: {0} ({1} - {2})'.format(title, self.get_relative_path(self.download_path), locale_code))
                else:
                    file_name = entry['file_name']
                    if not file_name == self.current_doc:
                        self.DOWNLOAD_NUMBER = 1
                        self.current_doc = file_name
                    base_name = os.path.basename(self.norm_path(file_name))
                    if not locale_code:
                        #Don't download source document(s), only download translations
                        logger.info("No target locales for "+file_name+".")
                        return
                    if locale_ext:
                        downloaded_name = self.append_ext_to_file(locale_code, base_name, True)
                    else:
                        downloaded_name = base_name
                    if 'xliff' in response.headers['Content-Type'] and xliff == True:
                        downloaded_name = self.change_file_extension('xlf', downloaded_name)
                    if 'same' in self.download_option:
                        self.download_path = os.path.dirname(file_name)
                        new_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
                        if not os.path.isfile(new_path) or (locale_code in new_path):
                            self.download_path = new_path
                        else:
                            self.default_download_ext = "({0})".format(self.DOWNLOAD_NUMBER)
                            downloaded_name = self.append_ext_to_file(self.default_download_ext, base_name, False)
                            self.download_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
                            self.DOWNLOAD_NUMBER += 1
                    else:
                        if self.download_path == "null":
                            self.download_path = os.path.join(self.path,downloaded_name)
                        else:
                            self.download_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
                self.doc_manager.add_element_to_prop(document_id, 'downloaded', locale_code)
                config_file_name, conf_parser = self.init_config_file()

                # create new file and write contents
                try:
                    with open(self.download_path, 'wb') as fh:
                        for chunk in response.iter_content(1024):
                            fh.write(chunk)
                    logger.info('Downloaded: {0} ({1} - {2})'.format(downloaded_name, self.get_relative_path(self.download_path), locale_code))
                except:
                    logger.warning('Error: Download failed at '+self.download_path)
                    return self.download_path
                git_autocommit = conf_parser.get('main', 'git_autocommit')
                if git_autocommit in ['True', 'on']:
                    if not self.git_auto.repo_is_defined:
                        if self.git_auto.repo_exists(self.download_path) and os.path.isfile(self.download_path):
                            self.git_auto.add_file(self.download_path)
                    else:
                        self.git_auto.add_file(self.download_path)

                return self.download_path
            else:
                printResponseMessages(response)
                if entry:
                    raise_error(response.json(), 'Failed to download content for {0} ({1})'.format(entry['name'], document_id), True)
                else:
                    raise_error(response.json(), 'Failed to download content for id: {0}'.format(document_id), True)
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on download: "+str(e))

    def _clone_download(self, locale_code):
        try:
            locale_folders = {}
            for key, value in self.locale_folders.items():
                key = key.replace('_', '-')
                locale_folders[key] = value
            if locale_code in locale_folders:
                self.download_root = locale_folders[locale_code]
            elif self.download_dir and len(self.download_dir):
                self.download_root = os.path.join((self.download_dir if self.download_dir and self.download_dir != 'null' else ''),locale_code)
            else:
                self.download_root = locale_code
            self.download_root = os.path.join(self.path, self.download_root)
            self.download_path = self.download_root
            target_dirs = self.download_path.split(os.sep)
            incremental_path = ""
            if not os.path.exists(self.download_root):
                os.mkdir(self.download_root)
                #print("Created directory: "+ download_root)
            if target_dirs:
                for target_dir in target_dirs:
                    incremental_path += target_dir + os.sep
                    #print("target_dir: "+str(incremental_path))
                    new_path = os.path.join(self.path,incremental_path)
                    # print("new path: "+str(new_path))
                    if not os.path.exists(new_path):
                        try:
                            os.mkdir(new_path)
                            # print("Created directory "+str(new_path))
                        except Exception as e:
                            log_error(self.error_file_name, e)
                            logger.warning("Could not create cloned directory "+new_path)
        except IOError as e:
            print(e.errno)
            print(e)

    def change_file_extension(self, new_ext, base_name):
        name_parts = base_name.split('.')
        new_name = None
        if(len(name_parts) > 1):
            name_parts[-1] = new_ext
            new_name = '.'.join(part for part in name_parts)
        else:
            new_name = name_parts[0] + '.' + new_ext
            self.download_path = os.path.join(self.path, os.path.join(self.download_path, new_name))
            # print("New name: {0}".format(new_name))
            # print("Download path: {0}".format(self.download_path))

        return new_name

    def append_ext_to_file(self, to_append, base_name, append_locale):
        name_parts = base_name.split('.')
        if len(name_parts) > 1:
            if append_locale:
                name_parts.insert(-1, to_append)
            else:
                name_parts[0] = name_parts[0] + to_append

            downloaded_name = '.'.join(part for part in name_parts)

            return downloaded_name
        else:
            downloaded_name = name_parts[0] + '.' + to_append
            self.download_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
            return downloaded_name
