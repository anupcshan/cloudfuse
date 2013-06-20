#!/usr/bin/python

class EndPoint:
    def __init__(self):
        pass

    """
    Authenticate the client with its backend provider.

    This step should call storeCredentials to persist its credentials
    once the authentication is complete.
    """
    def authenticate(self):
        raise NotImplementedError("authenticate not implemented")

    """
    Upload data and create a new file/object in the specified path/namespace
    on the backend provider.

    TODO: Error codes?
    """
    def createFile(self, path, data):
        raise NotImplementedError("createFile not implemented")

    """
    Fetch data stored in the specified file/object on the backend provider.

    TODO: Error codes? File portions?
    """
    def getFile(self, path):
        raise NotImplementedError("getFile not implemented")

    """
    Get user info from the backend provider, including:
    - username (to identify multiple accounts on the same backend)
    - quota details (disk used/remaining, bandwidth used/remaining)

    TODO: Come up with a consistent format for this data.
    """
    def getInfo(self):
        raise NotImplementedError("getInfo not implemented")

    """
    Get a list of all files in a folder.

    TODO: Error codes?
    """
    def listfiles(self, folder = None):
        raise NotImplementedError("listFiles not implemented")

    """
    Delete/remove a file/object on the backend provider.

    TODO: Error codes? Batching?
    """
    def removeFile(self, path):
        raise NotImplementedError("removeFile not implemented")

    """
    Save authorization keys or cookies after logging into the backend.

    TODO: Should this be common across all endpoints? Add corresponding loadCredentials?
    """
    def storeCredentials(self, credentials):
        raise NotImplementedError("storeCredentials not implemented")
