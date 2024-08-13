import requests

USER_AUTH = {
    "client_id": "direct-access-demo",
    "username": "user",
    "password": "user",
    "grant_type": "password",
}

if __name__ == "__main__":
    r = requests.post(
        "http://localhost:8080/realms/dataclay/protocol/openid-connect/token", data=USER_AUTH
    )

    token = r.json()["access_token"]
    print(token)
