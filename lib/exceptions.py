class UninitializedError(Exception):
    """ Project has not been initialized """

class ResourceNotFound(Exception):
    """ Requested document is not found """

class AlreadyExistsError(Exception):
    """ Resource already exists """

class NoIdSpecified(Exception):
    """ Required id is not specified """

class RequestFailedError(Exception):
    """ Request went wrong """

