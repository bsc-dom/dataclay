import logging

from dataclay.proxy import jwt_validation
from dataclay.proxy.middleware import MiddlewareBase, MiddlewareException

logger = logging.getLogger(__name__)


class ActiveMethodWhitelist(MiddlewareBase):

    def __init__(self, user, methods, role_dataset):
        self._user = user
        self._method_names = methods
        self._role_dataset = role_dataset

    def CallActiveMethod(self, request, context):
        metadata = dict(context.invocation_metadata())
        
        if metadata.get("username") != self._user:
            # Not the user we filter
            return
        
        if request.method_name in self._method_names:
            # Method in whitelist
            if metadata.get("dataset-name") in self._role_dataset:
                jwt_validation(metadata.get("username"), metadata.get("password"), self._role_dataset[metadata.get("dataset-name")])
                #User has the necessary role to access the dataset
            return
        raise MiddlewareException("Method not allowed")

    def GetObjectAttribute(self, request, context):
        metadata = dict(context.invocation_metadata())

        if metadata.get("username") != self._user:
            # Not the user we filter
            return

        gets = ("get", "__getattribute__", "getattr")
        for method in gets:
            if method in self._method_names:
                # Method in whitelist
                if metadata.get("dataset-name") in self._role_dataset:
                    jwt_validation(metadata.get("username"), metadata.get("password"), self._role_dataset[metadata.get("dataset-name")])
                    #User has the necessary role to access the dataset
                return
        raise MiddlewareException("Method GetObjectAttribute not allowed")

    def SetObjectAttribute(self, request, context):
        metadata = dict(context.invocation_metadata())

        if metadata.get("username") != self._user:
            # Not the user we filter
            return

        sets = ("set", "__setattr__", "setattr")
        for method in sets:
            if method in self._method_names:
                # Method in whitelist
                if metadata.get("dataset-name") in self._role_dataset:
                    jwt_validation(metadata.get("username"), metadata.get("password"), self._role_dataset[metadata.get("dataset-name")])
                    #User has the necessary role to access the dataset
                return
        raise MiddlewareException("Method SetObjectAttribute not allowed")

    def DelObjectAttribute(self, request, context):
        metadata = dict(context.invocation_metadata())

        if metadata.get("username") != self._user:
            # Not the user we filter
            return

        dels = ("delete", "__delattr__", "delattr")
        for method in dels:
            if method in self._method_names:
                # Method in whitelist
                if metadata.get("dataset-name") in self._role_dataset:
                    jwt_validation(metadata.get("username"), metadata.get("password"), self._role_dataset[metadata.get("dataset-name")])
                    #User has the necessary role to access the dataset
                return
        raise MiddlewareException("Method DelObjectAttribute not allowed")
