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
        logger.debug("Intercepting call to %s", handler_call_details.method)

        raise NotImplementedError("OIDCInterceptor is not implemented yet")
    
        # Check if the request has a token, and validate its signature and validity
        # through the OpenID endpoints (endpoints inferred through the discovery_url).

        current_mwc = middleware_context.get()
        current_mwc["oidc_user"] = ...  # None if not authenticated
        current_mwc["oidc_roles"] = ...  # Empty list if not authenticated

        return await continuation(handler_call_details)

def jwt_validation(username, password, roles):
    
    from base64 import b64decode
    from cryptography.hazmat.primitives import serialization

    USER_AUTH = {
        "client_id": "direct-access-demo",
        "username":username,
        "password":password,
        "grant_type": "password",
    }

    try:
        r = requests.post(
        "http://keycloak:8080/realms/dataclay/protocol/openid-connect/token", data=USER_AUTH
        )
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise e
    token = r.json()["access_token"]

    r = requests.get("http://keycloak:8080/realms/dataclay/")
    r.raise_for_status()
    key_der_base64 = r.json()["public_key"]

    key_der = b64decode(key_der_base64.encode())

    public_key = serialization.load_der_public_key(key_der)

    decoded_payload = jwt.decode(token, public_key, algorithms=["RS256"])

    if "realm_access" in decoded_payload:
        for role in roles:
            if role in decoded_payload["realm_access"]["roles"]:
                return
    raise Exception(f"The user '{username}' does not have the required role to access the database")
    