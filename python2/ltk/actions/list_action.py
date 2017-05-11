from ltk.actions.action import *

class ListAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def list_action(self, **kwargs):
        if 'id_type' in kwargs and kwargs['id_type']:
            id_type = kwargs['id_type']
            if id_type == 'workflow':
                self.list_workflows()
            elif id_type == 'locale':
                self.list_locales()
            elif id_type == 'format':
                self.list_formats()
            elif id_type == 'filter':
                self.list_filters()
            elif id_type == 'remote':
                self.list_remote()

        elif 'hide_docs' in kwargs and 'title' in kwargs:
            self.list_ids(kwargs['hide_docs'], kwargs['title'])

        else: logger.error("Error on command line input for 'ltk list'")

    def list_filters(self):
        response = self.api.list_filters()
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get filters')
        filter_entities = response.json()['entities']
        print ('Filters: id, created, title')
        for entry in sorted(filter_entities, key=lambda entry: entry['properties']['upload_date'], reverse=True):
            properties = entry['properties']
            title = properties['title']
            filter_id = properties['id']
            upload_date = time.strftime("%Y-%m-%d", time.localtime(int(properties['upload_date']/1000)))
            is_public = " (public)" if properties['is_public'] else ""
            print ('{0}  {1}  {2}{3}'.format(filter_id, upload_date, title, is_public))

    def list_formats(self):
        format_info = self.api.get_document_formats()
        format_mapper = detect_format(None, True)

        format_list = {}
        for format_name in sorted(set(format_info.values())):
            format_list[format_name] = []

        for extension in format_mapper.keys():
            key = format_mapper[extension]
            if key not in format_list:
                format_list[key] = []
            format_list[key].append(extension)

        print("Lingotek Cloud accepts content using any of the formats listed below. File formats will be auto-detected for the extensions as specified below. Alternatively, formats may be specified explicitly upon add. Lingotek supports variations and customizations on these formats with filters.")
        print()
        print('%-30s' % "Format" + '%s' % "Auto-detected File Extensions")
        print("-----------------------------------------------------------")
        for k,v in sorted(format_list.items()):
            print('%-30s' % k + '%s' % ' '.join(v))

    def list_ids(self, hide_docs, title=False):
        try:
            """ lists ids of list_type specified """
            folders = self.folder_manager.get_file_names()
            if len(folders):
                underline("Folder path")
                for folder in folders:
                    if title:
                        print(folder)
                    else:
                        print(self.get_relative_path(folder))
                if hide_docs:
                    return
                print("")
            elif hide_docs:
                print("No added folders")
                return
            ids = []
            titles = []
            locales = []
            max_length = 0
            entries = self.doc_manager.get_all_entries()
            for entry in entries:
                # if entry['file_name'].startswith(cwd.replace(self.path, '')):
                ids.append(entry['id'])
                try:
                    if title:
                        name = entry['name']
                    else:
                        name = self.get_relative_path(self.norm_path(entry['file_name']))
                        # print("relative path: "+name)
                    if len(name) > max_length:
                        max_length = len(name)
                    titles.append(name)
                except (IndexError, KeyError) as e:
                    log_error(self.error_file_name, e)
                    titles.append("        ")
                try:
                    locales.append(entry['locales'])
                except KeyError:
                    locales.append([])
            if not ids:
                print ('No local documents')
                return
            if max_length > 90:
                max_length = 90
            underline('%-*s' % (max_length,'Filename') + ' %-38s' % 'Lingotek ID' + 'Locales')
            for i in range(len(ids)):
                title = titles[i]
                if len(title) > max_length:
                    title = title[(len(titles[i])-30):]
                info = '%-*s' % (max_length,title) + ' %-38s' % ids[i] + ', '.join(locale.replace('_','-') for locale in locales[i])
                print (info)
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on list: "+str(e))

    def list_locales(self):
        locale_info = []
        response = self.api.list_locales()
        if response.status_code != 200:
            raise exceptions.RequestFailedError("Failed to get locale codes")
        locale_json = response.json()
        for entry in locale_json:
            locale_code = locale_json[entry]['locale'].replace('_','-')
            language = locale_json[entry]['language_name']
            country = locale_json[entry]['country_name']
            locale_info.append((locale_code, language, country))
        for locale in sorted(locale_info):
            if not len(locale[2]):  # Arabic
                print ("{0} ({1})".format(locale[0], locale[1]))
            else:
                print ("{0} ({1}, {2})".format(locale[0], locale[1], locale[2]))

    def list_remote(self):
        """ lists ids of all remote documents """
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
            print ('Remote documents:\nID \t \t \t \t \t Document name')
            for entry in response.json()['entities']:
                title = entry['properties']['title']
                id = entry['properties']['id']
                info = '{id} \t {title}'.format(id=id, title=title)
                print (info)

    def list_workflows(self):
        try:
            response = self.api.list_workflows(self.community_id)
            if response.status_code != 200:
                raise_error(response.json(), "Failed to list workflows")
            ids, titles = log_id_names(response.json())
            if not ids:
                print ('No workflows')
                return
            print ('Workflows: id, title')
            for i in range(len(ids)):
                info = '{id} \t {title}'.format(id=ids[i], title=titles[i])
                print (info)
        except:
            logger.error("An error occurred while attempting to connect to remote.")
