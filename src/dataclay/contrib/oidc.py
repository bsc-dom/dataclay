"""
Helper classes to add OpenID Connect middleware to the proxy.

This module provides a basic foundation that can be used to add OIDC
middleware to the proxy. This middleware can provide some authentication
and more advanced ACL mechanisms (see the Keycloak examples for a concrete
working implementation of this kind of middleware).
"""

import logging
from typing import Awaitable, Callable
import requests
import jwt
import grpc
from dataclay.proxy.middleware import middleware_context, MiddlewareException
import keycloak
from keycloak import KeycloakOpenID

import os

class KeycloakConfig:

    def server_url(self) -> str:
        return os.getenv("KEYCLOAK_SERVER_URL")

    def realm_name(self) -> str:
        return os.getenv("KEYCLOAK_REALM_NAME")

    def resource_server_id(self) -> str:
        return os.getenv("KEYCLOAK_RESOURCE_SERVER_ID")

    def audience(self) -> str:
        return os.getenv("KEYCLOAK_AUDIENCE")

    def client_id(self) -> str:
        return os.getenv("KEYCLOAK_CLIENT_ID")

    def client_secret_key(self) -> str:
        return os.getenv("KEYCLOAK_CLIENT_SECRET_KEY")

KEYCLOAK_CONFIG = KeycloakConfig()



logger = logging.getLogger(__name__)


class OIDCInterceptor(grpc.aio.ServerInterceptor):
    def __init__(self, discovery_url: str):
        self.discovery_url = discovery_url

        # TODO: Fetch the OpenID configuration from the discovery_url
        # Implementation notes:
        # `__init__` seems a good place where to conect to the OIDC discovery URL
        # and retrieve the endpoints that we require (and store those endpoints in
        # internal variables in this class, failing if the discovery_url is not a valid
        # URL or does not contain a valid OIDC configuration). Note that downloading the
        # certificates is something that might be done later (because they can be updated,
        # maybe we want to cache them, we want to refresh it if the server rekeys, etc).
        # Eventually, we might give the user the option to either give a discovery_url
        # or manually provide the endpoints, but that is not a priority right now.

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        """Interceptor function. Populates middleware_context according to whether:
            -The user can't be authenticated:
                -With the grpc context
            -The user can be authenticated but has no roles:
                -With the grpc context + preferred_username
            -The user can be authenticated and has roles:
                -With the grpc context + preferred_username + {roles}

        Args:
            continuation (Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]]): Continuation of the grpc functionality
            handler_call_details (grpc.HandlerCallDetails): Details sent in the grpc call

        Returns: 
            Returns the result of the continuation
        """
        logger.info("Intercepting call to %s", handler_call_details.method)
        from base64 import b64decode
        from cryptography.hazmat.primitives import serialization

        #raise NotImplementedError("OIDCInterceptor is not implemented yet")
    
        # Check if the request has a token, and validate its signature and validity
        # through the OpenID endpoints (endpoints inferred through the discovery_url).

        
    
        current_mwc = dict(handler_call_details.invocation_metadata)


        if "username" not in current_mwc: 
            middleware_context.set(current_mwc)
            return await continuation(handler_call_details)

        keycloak_open_id = KeycloakOpenID(
            KEYCLOAK_CONFIG.server_url(),
            KEYCLOAK_CONFIG.realm_name(),
            KEYCLOAK_CONFIG.client_id(),
            current_mwc["key"],
        )

        if "path" not in current_mwc:
            raise MiddlewareException("Path cannot be NULL")

        if "token" not in current_mwc:
            logger.info("/////////////MIRA////////////////")
            logger.info("client_id %s: ", KEYCLOAK_CONFIG.client_id())
            logger.info("username %s: ", current_mwc["username"])
            logger.info("password %s: ", current_mwc["password"])
            logger.info("grant_type %s: ", "password")
            logger.info("client_secret %s: ", current_mwc["key"])
            USER_AUTH = {
            "client_id": KEYCLOAK_CONFIG.client_id(),
            "username":current_mwc["username"],
            "password":current_mwc["password"],
            "grant_type": "password",
            "client_secret": current_mwc["key"],
            }

            try:
                r = requests.post(
                self.discovery_url+"/realms/dataclay/protocol/openid-connect/token", data=USER_AUTH
                )
                r.raise_for_status()
            except requests.exceptions.RequestException:
                middleware_context.set(current_mwc)
                return await continuation(handler_call_details)

            token = r.json()["access_token"]
        else:
            token = current_mwc.get("token")

        
        permissions = keycloak_open_id.uma_permissions(token)
        logger.info("~~~~~~~~~~~~~~Aquestes son les permissions: %s", permissions)
        current_mwc["permissions"] = permissions
        
        middleware_context.set(current_mwc)
        logger.info("######################################")
        return await continuation(handler_call_details)
