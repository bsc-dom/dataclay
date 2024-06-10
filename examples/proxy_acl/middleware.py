import logging
import pickle
from pprint import pprint

from dataclay.proxy import MiddlewareBase, MiddlewareException, jwt_validation

logger = logging.getLogger(__name__)


class ActiveMethodWhitelist(MiddlewareBase):
    def __init__(self, user, methods):
        self._user = user
        self._method_names = methods

    def CallActiveMethod(self, request, context):
        metadata = dict(context.invocation_metadata())
        if metadata.get("username") != self._user:
            # Not the user we filter
            return

        if request.method_name in self._method_names:
            # Method in whitelist
            jwt_validation(metadata.get("username"), metadata.get("authorization"))
            # Token has been validated
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
                jwt_validation(metadata.get("username"), metadata.get("authorization"))
                # Token has been validated
                return

        raise MiddlewareException("Method GetObjectAttribute not allowed")

    def SetObjectAttribute(self, request, context):
        metadata = dict(context.invocation_metadata())

        if metadata.get("username") != self._user:
            # Not the user we filter
            return

        gets = ("set", "__setattr__", "setattr")
        for method in gets:
            if method in self._method_names:
                # Method in whitelist
                jwt_validation(metadata.get("username"), metadata.get("authorization"))
                # Token has been validated
                return

        raise MiddlewareException("Method SetObjectAttribute not allowed")

    def DelObjectAttribute(self, request, context):
        metadata = dict(context.invocation_metadata())

        if metadata.get("username") != self._user:
            # Not the user we filter
            return

        gets = ("delete", "__delattr__", "delattr")
        for method in gets:
            if method in self._method_names:
                # Method in whitelist
                jwt_validation(metadata.get("username"), metadata.get("authorization"))
                # Token has been validated
                return

        raise MiddlewareException("Method DelObjectAttribute not allowed")
