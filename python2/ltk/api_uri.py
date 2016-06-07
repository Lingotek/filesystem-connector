# the uri for the api calls
API_URI = {
    'community': '/api/community',
    'project': '/api/project',
    'project_id': '/api/project/%(project_id)s',
    'project_translation': '/api/project/%(project_id)s/translation',
    'project_translation_locale': '/api/project/%(project_id)s/translation/%(locale)s',
    'project_status': '/api/project/%(project_id)s/status',
    'document': '/api/document',
    'document_id': '/api/document/%(document_id)s',
    'document_translation': '/api/document/%(document_id)s/translation',
    'document_status': '/api/document/%(document_id)s/status',
    'document_content': '/api/document/%(document_id)s/content',
    'document_translation_locale': '/api/document/%(document_id)s/translation/%(locale)s',  # gets the status of target
    'workflow': '/api/workflow',
    'filter': '/api/filter'
}
