from ltk.actions.action import *

class FiltersAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def filter_list_action(self):
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

    def filter_rm_action(self, filter_id):
        response = self.api.delete_filter(filter_id)
        if response.status_code != 204:
            raise_error(response.json(), 'Failed to remove filter {0}'.format(filter_id), filter_id)
        else:
            print('Filter {0} was successfully removed.'.format(filter_id))
        return

    def filter_add_action(self, filename, filter_type):
        if os.path.isfile(filename):
            content = open(filename, 'rb')
            response = self.api.post_filter(filename, filter_type)
            if response.status_code != 201:
                raise_error(response.json(), 'Failed to create filter', filename)
            else:
                print('Filter {0} was successfully added.'.format(response.json()['properties']['id']))
        else:
            print("File \"{0}\" not found.".format(filename))

    def filter_save_action(self, filter_id, filename):
        if os.path.isfile(filename):
            content = open(filename, 'rb')
            response = self.api.patch_filter(filter_id, filename)

            if response.status_code != 202:
                raise_error(response.json(), 'Failed to save filter', filename)
            else:
                print('Filter {0} was successfully updated.'.format(filter_id))
        else:
            print("File \"{0}\" not found.".format(filename))

    def filter_get_action(self, filter_id, filename, overwrite=False):
        response = self.api.get_filter_content(filter_id)
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get filter', filter_id, filename)
            return
        if filename is None:
            import cgi
            value, params = cgi.parse_header(response.headers['Content-Disposition'])
            filename = params['filename']
        if os.path.exists(filename) and overwrite != True:
            confirm = None
            while confirm not in ['y','Y','n','N','']:
                prompt_message = 'Filter "{0}" already exists locally. Would you like to overwrite it? [y/N]: '.format(filename)
                # Python 2
                confirm = raw_input(prompt_message)
                # End Python 2
                # Python 3
#                 confirm = input(prompt_message)
                # End Python 3
            if not confirm or confirm in ['','n','N']:
                logger.info('Will not overwrite local filter "{0}"'.format(filename))
                return
        try: # save filter content to filename
            with open(filename, 'wb') as fh:
                fh.write(response.content)
                logger.info('Filter {0} saved to local file "{1}"'.format(filter_id,filename))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise


    def filter_info_action(self, filter_id):
        response = self.api.get_filter_info(filter_id)
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get filter', filter_id)
            return
        if 'properties' in response.json():
            for key in response.json()['properties']:
                print ('{0:15} {1}'.format(key + ':', response.json()['properties'][key]))
        return
