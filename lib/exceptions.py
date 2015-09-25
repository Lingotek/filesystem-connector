class UninitializedError(Exception):
    """ Project has not been initialized """

class ResourceNotFound(Exception):
    """ Requested document is not found """

class NoIdSpecified(Exception):
    """ Required id is not specified """

