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
    'document_latest_version': '/api/document/%(document_id)s/latest-version',
    'document_format': '/api/document/format',
    'workflow': '/api/workflow',
    'filter': '/api/filter',
    'filter_id': '/api/filter/%(filter_id)s',
    'filter_content': '/api/filter/%(filter_id)s/content',
    'document_cancel': '/api/document/%(document_id)s/cancel',
    'document_cancel_locale': '/api/document/%(document_id)s/translation/%(locale)s/cancel',
    'process' :'/api/process/%(process_id)s',
    'reference': '/api/document/%(document_id)s/reference-material',
    'reference_id': '/api/document/%(document_id)s/reference-material/%(reference_id)s'
}
