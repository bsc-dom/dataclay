"""Middleware support for the proxy."""

import contextvars
import logging
from dataclay.config import ProxySettings, settings
#from dataclay.contrib.oidc import jwt_validation

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
    async def __call__(self, method_name, request, context):   
        try:
            m = getattr(self, method_name)
        except AttributeError:
            return
        logger.debug("Middleware %r is processing method %s" % (self, method_name))
        await m(request, context)
