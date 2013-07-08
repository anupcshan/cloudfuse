#!/usr/bin/python

import errno
import os

DEFAULT_CREDENTIALS_DIR = os.environ['HOME'] + '/.cloudfs'

class Registry:
    def __init__(self):
        self.endpoints = {}
        self.folderToEndPointMap = {}

    def registerEndpoint(self, providerId, cls):
        print 'Registering endpoint with id %s' % providerId
        self.endpoints[providerId] = cls
        print 'Total endpoints %d' % len(self.endpoints)


class EndPoint:
    __registry = Registry()

    def __init__(self, credDir):
        if credDir is None:
            self.credentialsDir = DEFAULT_CREDENTIALS_DIR
        else:
            self.credentialsDir = credDir

        self.ensureCredentialsDirExists()

    def ensureCredentialsDirExists(self):
        try:
            os.makedirs(self.credentialsDir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @classmethod
    def registerEndPoint(cls):
        EndPoint.__registry.registerEndpoint(cls.getProviderId(), cls)

    """
    Authenticate the client with its backend provider.

    This step should call storeCredentials to persist its credentials
    once the authentication is complete.

    TODO: Split this into initAuthentication and postAuthentication? That helps
    in cases where authentication involves a callback (like OAuth).
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

    """
    Get a unique provider ID which determines which endpoint loads a
    set of stored credentials. This should be able to handle multiple API versions.

    TODO: Should this be made into a checker method?
    """
    @classmethod
    def getProviderId(self):
        raise NotImplementedError("getProviderId not implemented")
