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
from dataclay.proxy.middleware import middleware_context

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

        if "token" not in current_mwc:
            USER_AUTH = {
            "client_id": "direct-access-demo",
            "username":current_mwc["username"],
            "password":current_mwc["password"],
            "grant_type": "password",
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

        try:
            r = requests.get(self.discovery_url+"/realms/dataclay/")#"http://keycloak:8080/realms/dataclay/"
            r.raise_for_status()
            key_der_base64 = r.json()["public_key"]

            key_der = b64decode(key_der_base64.encode())

            public_key = serialization.load_der_public_key(key_der)

            decoded_payload = jwt.decode(token, public_key, algorithms=["RS256"])
        except:
            middleware_context.set(current_mwc)
            return await continuation(handler_call_details)


        current_mwc["oidc_user"] = decoded_payload["preferred_username"]

        if "realm_access" in decoded_payload:
            current_mwc["oidc_roles"] = decoded_payload["realm_access"]["roles"]

        middleware_context.set(current_mwc)
        return await continuation(handler_call_details)
