#!/usr/bin/python
"""Abstract cloud endpoint."""

import errno
import os
import pickle
import uuid

DEFAULT_CREDENTIALS_DIR = os.environ['HOME'] + '/.cloudfs/credentials'

class Registry:
    """List of registered EndPoint plugins."""
    def __init__(self):
        self.endpointclasses = {}
        self.endpoints = []

    def register_endpoint(self, provider_id, cls):
        print 'Registering endpoint with id %s' % provider_id
        self.endpointclasses[provider_id] = cls
        print 'Total endpointclasses %d' % len(self.endpointclasses)

    def get_endpoint_for_provider(self, provider_id, _uuid = None):
        endpoint = self.endpointclasses[provider_id](_uuid)
        self.endpoints.append(endpoint)
        return endpoint

    def get_endpoints(self):
        return self.endpoints


class EndPoint:
    __registry = Registry()

    def __init__(self, _uuid = None):
        if _uuid is None:
            _uuid = uuid.uuid4().hex
        self._uuid = _uuid

    @classmethod
    def ensure_credentialsdir_exists(cls):
        try:
            os.makedirs(DEFAULT_CREDENTIALS_DIR)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @classmethod
    def register_endpoint(cls):
        EndPoint.__registry.register_endpoint(cls.get_providerid(), cls)

    @classmethod
    def load_saved_endpoints(cls):
        cls.ensure_credentialsdir_exists()
        for entry in os.listdir(DEFAULT_CREDENTIALS_DIR):
            print 'Loading credentials %s' % entry
            handle = open(os.path.join(DEFAULT_CREDENTIALS_DIR, entry), 'r')
            provider_id = handle.readline().splitlines()[0]
            print 'Located provider %s' % provider_id
            endpoint = cls.__registry.get_endpoint_for_provider(provider_id)
            endpoint.load_credentials(pickle.load(handle))

    @classmethod
    def get_all_endpoints(cls):
        return EndPoint.__registry.get_endpoints()

    """
    Authenticate the client with its backend provider.

    This step should call store_credentials to persist its credentials
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
    def create_file(self, path, data):
        raise NotImplementedError("create_file not implemented")

    """
    Fetch data stored in the specified file/object on the backend provider.

    TODO: Error codes? File portions?
    """
    def get_file(self, path):
        raise NotImplementedError("get_file not implemented")

    """
    Get user info from the backend provider, including:
    - username (to identify multiple accounts on the same backend)
    - quota details (disk used/remaining, bandwidth used/remaining)

    TODO: Come up with a consistent format for this data.
    """
    def get_info(self):
        raise NotImplementedError("get_info not implemented")

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
    def remove_file(self, path):
        raise NotImplementedError("remove_file not implemented")

    def load_credentials(self, credentials):
        raise NotImplementedError("load_credentials not implemented")

    """
    Save authorization keys or cookies after logging into the backend.
    """
    @classmethod
    def store_credentials(cls, credentials, _uuid=None):
        if _uuid is None:
            _uuid = uuid.uuid4().hex
            print _uuid

        handle = open(os.path.join(DEFAULT_CREDENTIALS_DIR, _uuid), 'w')
        handle.write(cls.get_providerid() + '\n')
        pickle.dump(credentials, handle)
        handle.close()
        return _uuid

    """
    Get a unique provider ID which determines which endpoint loads a
    set of stored credentials. This should be able to handle multiple API versions.

    TODO: Should this be made into a checker method?
    """
    @classmethod
    def get_providerid(cls):
        raise NotImplementedError("get_providerid not implemented")
