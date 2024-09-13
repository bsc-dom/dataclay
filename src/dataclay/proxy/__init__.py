import logging
import requests
import jwt
from dataclay.exceptions import DataClayException
from dataclay.proxy.middleware import MiddlewareBase, MiddlewareException


logger = logging.getLogger(__name__)


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
    logger.info(r.json())
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
    raise MiddlewareException(f"The user '{username}' does not have the required role to access the database")
    

