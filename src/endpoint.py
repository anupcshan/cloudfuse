#!/usr/bin/python

class EndPoint:
    def __init__(self):
        pass

    def authenticate(self):
        raise NotImplementedError("authenticate not implemented")

    def createFile(self, path):
        raise NotImplementedError("createFile not implemented")

    def getFile(self, path):
        raise NotImplementedError("getFile not implemented")

    def getInfo(self):
        raise NotImplementedError("getInfo not implemented")

    def listfiles(self, folder = None):
        raise NotImplementedError("listFiles not implemented")

    def removeFile(self, path):
        raise NotImplementedError("removeFile not implemented")
