"""Middleware support for the proxy."""

import contextvars
import logging
from dataclay.config import ProxySettings, settings
from dataclay.contrib.oidc import jwt_validation

settings.proxy = ProxySettings()

logger = logging.getLogger(__name__)

middleware_context = contextvars.ContextVar("middleware_context", default={})


class MiddlewareException(Exception):
    status_code = None


class MiddlewareBase:
    """Base class to be used for middlewares.

    To implement a middleware, create a new class by deriving this
    MiddlewareBase and implement the methods that you need.
    """
    def __init__(self, role_dataset = {}):
            #If validation is active, _role_dataset sets which role you need in order to access each dataset.
            self._role_dataset = role_dataset

    def __call__(self, method_name, request, context):
        if settings.proxy.jwt_validate: 
                logger.debug("Middleware %r is validating the JWT" % self)
                metadata = dict(context.invocation_metadata())
                if not hasattr(self, '_role_dataset') or self._role_dataset is None:
                     raise AttributeError("Error: 'role_dataset' not initialized. Ensure you call super().__init__(role_dataset) in the ActiveMethodWhitelist initialitzation.")
                if metadata.get("dataset-name") in self._role_dataset:
                    #The dataset needs a specific role to be accessed
                    try:
                        jwt_validation(metadata.get("username"), metadata.get("password"), self._role_dataset[metadata.get("dataset-name")])
                        #The user has one of the needed roles
                    except Exception as e:
                         raise MiddlewareException(e)
                
        try:
            m = getattr(self, method_name)
        except AttributeError:
            return
        logger.debug("Middleware %r is processing method %s" % (self, method_name))
        m(request, context)
