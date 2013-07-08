#!/usr/bin/python

import errno
import os
import pickle
import uuid

DEFAULT_CREDENTIALS_DIR = os.environ['HOME'] + '/.cloudfs/credentials'

class Registry:
    def __init__(self):
        self.endpointclasses = {}
        self.endpoints = []

    def registerEndpoint(self, providerId, cls):
        print 'Registering endpoint with id %s' % providerId
        self.endpointclasses[providerId] = cls
        print 'Total endpointclasses %d' % len(self.endpointclasses)

    def getEndPointForProvider(self, providerId):
        ep = self.endpointclasses[providerId]()
        self.endpoints.append(ep)
        return ep

    def getEndPoints(self):
        return self.endpoints


class EndPoint:
    __registry = Registry()

    def __init__(self):
        self._uuid = uuid.uuid4().hex

    @classmethod
    def ensureCredentialsDirExists(self):
        try:
            os.makedirs(DEFAULT_CREDENTIALS_DIR)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @classmethod
    def registerEndPoint(cls):
        EndPoint.__registry.registerEndpoint(cls.getProviderId(), cls)

    @classmethod
    def loadSavedEndPoints(cls):
        cls.ensureCredentialsDirExists()
        for entry in os.listdir(DEFAULT_CREDENTIALS_DIR):
            print 'Loading credentials %s' % entry
            f = open(os.path.join(DEFAULT_CREDENTIALS_DIR, entry), 'r')
            providerId = f.readline().splitlines()[0]
            print 'Located provider %s' % providerId
            ep = cls.__registry.getEndPointForProvider(providerId)
            ep._uuid = entry
            ep.loadCredentials(pickle.load(f))

    @classmethod
    def getAllEndPoints(cls):
        return EndPoint.__registry.getEndPoints()

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

    def loadCredentials(self, credentials):
        raise NotImplementedError("loadCredentials not implemented")

    """
    Save authorization keys or cookies after logging into the backend.
    """
    @classmethod
    def storeCredentials(cls, credentials, _uuid=None):
        if _uuid is None:
            _uuid = uuid.uuid4().hex
            print _uuid

        f = open(os.path.join(DEFAULT_CREDENTIALS_DIR, _uuid), 'w')
        f.write(cls.getProviderId() + '\n')
        pickle.dump(credentials, f)
        f.close()
        return _uuid

    """
    Get a unique provider ID which determines which endpoint loads a
    set of stored credentials. This should be able to handle multiple API versions.

    TODO: Should this be made into a checker method?
    """
    @classmethod
    def getProviderId(cls):
        raise NotImplementedError("getProviderId not implemented")
