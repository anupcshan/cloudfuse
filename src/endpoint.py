#!/usr/bin/python
"""Abstract cloud endpoint."""

import errno
import hashlib
import json
import logging
import os
import pickle
import uuid
from config import Config

class PathMetadata:
    """
    Data object to store metadata about an object location in a backend
    datastore.

    TODO: Should sharing info be a part of this structure?
    TODO: Should there be a way to check for object modification?
          Like hashes or timestamps.
    """

    def __init__(self):
        self.is_dir = False
        self.size = 0
        self.path = ""
        self.name = ""
        self.mtime = 0
        self.children = None
        self.explored = False

class EndPoint:
    """
    Abstract cloud endpoint interface.

    Provides hooks to authenticate and interact with backend datastore.
    """
    __endpoint_classes = {}
    __endpoints = []
    _config = Config()
    _logger = logging.getLogger('EndPoint')

    def __init__(self, _uuid = None):
        if _uuid is None:
            _uuid = uuid.uuid4().hex
        self._uuid = _uuid
        self._cloudfs_root_dir = "_cloudfs"
        self._cloudfs_root_inode = "/ROOT"
        self._cloudfs_objects_dir = self.rel_path("/objects")

    def __str__(self):
        return '%s:%s' % (self.get_providerid(), self._uuid)

    @classmethod
    def ensure_credentialsdir_exists(cls):
        """
        Create credentials directory if it does not exist.
        """
        try:
            os.makedirs(EndPoint._config.get_credentials_dir())
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @classmethod
    def register_endpoint(cls):
        """
        Register a cloud endpoint.
        
        This method should be called by the implementation while its module is loaded.
        """
        provider_id = cls.get_providerid()
        EndPoint._logger.info('Registering endpoint with id %s' % provider_id)
        EndPoint.__endpoint_classes[provider_id] = cls
        EndPoint._logger.info('Total endpointclasses %d' % len(EndPoint.__endpoint_classes))

    @classmethod
    def _get_endpoint_for_provider(cls, provider_id, _uuid = None):
        """
        Creates a new instance of the endpoint.
        """
        endpoint = EndPoint.__endpoint_classes[provider_id](_uuid)
        EndPoint.__endpoints.append(endpoint)
        return endpoint

    @classmethod
    def load_saved_endpoints(cls):
        """
        Go through credentials directory and instantiate all saved credentials.
        """
        cls.ensure_credentialsdir_exists()
        for entry in os.listdir(EndPoint._config.get_credentials_dir()):
            EndPoint._logger.info('Loading credentials %s' % entry)
            handle = open(os.path.join(
                        EndPoint._config.get_credentials_dir(), entry), 'r')
            provider_id = handle.readline().splitlines()[0]
            EndPoint._logger.info('Located provider %s' % provider_id)
            endpoint = EndPoint._get_endpoint_for_provider(provider_id)
            endpoint.load_credentials(pickle.load(handle))

    @classmethod
    def get_all_endpoints(cls):
        """
        Get a list of all authenticated endpoints.
        """
        return EndPoint.__endpoints

    def _make_request(self, operation, uri, method='GET', parse=True, body=None):
        """
        Make an API request and parse response into JSON.
        """
        _, response = self._connection.request(method=method, uri=uri,
                headers=self.get_signed_request(uri, method=method), body=body)
        if parse:
            self._logger.debug('%s => %s', operation, response)
            return json.loads(response)
        else:
            return response

    def authenticate(self):
        """
        Authenticate the client with its backend provider.

        This step should call store_credentials to persist its credentials
        once the authentication is complete.

        TODO: Split this into initAuthentication and postAuthentication? That helps
        in cases where authentication involves a callback (like OAuth).
        """
        raise NotImplementedError("authenticate not implemented")

    def create_folder(self, path):
        """
        Create a new folder in the specified path on the backend provider.

        TODO: Error codes?
        """
        raise NotImplementedError("create_folder not implemented")

    def create_file(self, path, data):
        """
        Upload data and create a new file/object in the specified path/namespace
        on the backend provider.

        TODO: Error codes?
        """
        raise NotImplementedError("create_file not implemented")

    def rel_path(self, path):
        return self._cloudfs_root_dir + path

    def safe_create_filesystem(self):
        """
        Create empty filesystem structure
        """
        self.safe_create_root_folder()
        self.create_folder_if_absent(self._cloudfs_objects_dir)

    def safe_create_root_folder(self):
        """
        Create empty root folder if not present.
        """
        self.create_folder_if_absent(self._cloudfs_root_dir)

    def safe_get_root_inode(self):
        """
        Return root inode instance if present, None otherwise.
        """
        if self.if_file_exists(self.rel_path(self._cloudfs_root_inode)):
            root_block_hash = self.get_file(self.rel_path(self._cloudfs_root_inode))
            # FIXME: The root block need not be present on the same provider as the
            # ROOT block pointer.
            return pickle.loads(self.get_object(root_block_hash))

        return None

    def create_root_inode(self, inode):
        inode_data = pickle.dumps(inode)
        dhash = self.create_object(inode_data)
        self.create_file(self.rel_path(self._cloudfs_root_inode), dhash)

    def get_object(self, objhash):
        return self.get_file(self._cloudfs_objects_dir + '/' + objhash)

    def create_object(self, data):
        dhash = hashlib.sha256(data).hexdigest()
        self.create_file(self._cloudfs_objects_dir + '/' + dhash, data)
        return dhash

    def if_folder_exists(self, path):
        """
        Checks if folder at given path exists on backend provider.
        """
        pathinfo = self.get_path_metadata(path)

        if pathinfo is not None and pathinfo.is_dir is True:
            return True

        return False

    def if_file_exists(self, path):
        """
        Checks if file at given path exists on backend provider.
        """
        pathinfo = self.get_path_metadata(path)

        if pathinfo is not None and pathinfo.is_dir is not True:
            return True

        return False

    def create_folder_if_absent(self, path):
        """
        Create a folder at the specified path if it is not already present
        """
        if not self.if_folder_exists(path):
            self.create_folder(path)

    def get_file(self, path):
        """
        Fetch data stored in the specified file/object on the backend provider.

        TODO: Error codes? File portions?
        """
        raise NotImplementedError("get_file not implemented")

    def get_info(self):
        """
        Get user info from the backend provider, including:
        - username (to identify multiple accounts on the same backend)
        - quota details (disk used/remaining, bandwidth used/remaining)

        TODO: Come up with a consistent format for this data.
        """
        raise NotImplementedError("get_info not implemented")

    def get_path_metadata(self, path):
        """
        Get metadata about the object at the specified path.
        Returns a PathMetadata instance.
        """
        raise NotImplementedError("get_path_metadata not implemented")

    def remove_file(self, path):
        """
        Delete/remove a file/object on the backend provider.

        TODO: Error codes? Batching?
        """
        raise NotImplementedError("remove_file not implemented")

    def load_credentials(self, credentials):
        """
        Load saved credentials.

        Called with same parameters as passed to store_credentials.
        """
        raise NotImplementedError("load_credentials not implemented")

    @classmethod
    def store_credentials(cls, credentials, _uuid=None):
        """
        Save authorization keys or cookies after logging into the backend.
        """
        if _uuid is None:
            _uuid = uuid.uuid4().hex

        handle = open(os.path.join(
                    EndPoint._config.get_credentials_dir(), _uuid), 'w')
        handle.write(cls.get_providerid() + '\n')
        pickle.dump(credentials, handle)
        handle.close()
        return _uuid

    @classmethod
    def get_providerid(cls):
        """
        Get a unique provider ID which determines which endpoint loads a
        set of stored credentials. This should be able to handle multiple API versions.

        TODO: Should this be made into a checker method?
        """
        raise NotImplementedError("get_providerid not implemented")
