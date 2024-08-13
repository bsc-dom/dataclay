Using Keycloak for authenticating dataClay users
================================================

Proxy configuration
-------------------

In this example, Keycloak will be using OpenID Connect, which is an authentication protocol based on OAuth 2.0 specs. There are multiple ways of configuring different kind of OAuth 2.0 setups, but in this example we will show how to make use of the discovery URL of OpenID, which is accessible at http://keycloak:8080/realms/dataclay/.well-known/openid-configuration (once the stack is started).

The discovery URL is set up in the proxy service and the proxy will make use of this to validate JWT token and its signatures.

**TODO**

Starting the stack
------------------

A `compose.yaml` is provided, which includes a Keycloak instance. This Keycloak instance will automatically import the dataclay realm (stored in the `keycloak-data` folder).

Once this stack has started, there should be a prepopulated Keycloak instance and a pristine dataClay instance ready to be used.

Browsing Keycloak
-----------------

The Keycloak web interface should be accessible through http://localhost:8080 with user `admin` and password `admin`. Realm data should be automatically imported on startup and you will see the [dataClay realm](http://localhost:8080/admin/master/console/#/dataclay/clients) properly initialized.

This realm contains contains two users: `user` and `luser` (the first one has the `custom_role` role, while the second one does not have it).

Retrieving a JWT
----------------

This is not the focus of this example, so we show a crude cURL that achieves that:

```bash
$ curl -X POST 'http://localhost:8080/realms/dataclay/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=direct-access-demo' \
  -d 'username=user' \
  -d 'password=user' \
  -d 'grant_type=password'
{"access_token":"eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJtZGVvVmxXWi1YRHFEX3lLUVNraXQ5dEY0OWNUaXVFVllSa1k1OWNPRE0wIn0.eyJleHAiOjE3MjM0NDk5MTgsImlhdCI6MTcyMzQ0OTYxOCwianRpIjoiYzRiNWEzYzItOGUyNi00YzE3LTgwOTUtZGJiYjY3ZjU3ZTgwIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL3JlYWxtcy9kYXRhY2xheSIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI2MWM2YjM5My1mZTU2LTQ5YzgtYmRkZC1iNDQxY2VmMTE1ODYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJjdXJsLWRlbW8iLCJzaWQiOiJlM2ZmN2M1NC0xNDhhLTQ2OWQtYjViYy05MGRmMjk4ZDZjZTkiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIi8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtZGF0YWNsYXkiLCJjdXN0b21fcm9sZSIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJkYXRhQ2xheSBVc2VyIEV4YW1wbGUiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ1c2VyIiwiZ2l2ZW5fbmFtZSI6ImRhdGFDbGF5IFVzZXIiLCJmYW1pbHlfbmFtZSI6IkV4YW1wbGUiLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20ifQ.shPj09XvngK0HGRogO9hOuZMaEyOJFHaYgkH12rrkBtKmQGEY8TTPHEAzZ2WnF3d7inV8czKXYmFUiSA82BHh1dkWs1eq_QAjvuHzYwKsGX_gX8nA5bXB9Ys7g-_Yot3Se_kAk41zrqcvmV5tzXn3h1I8bzouU9SW5B9Btei4qQ2oXEiwPKBVk3rJuVQGK3Zmh_cwh98Jw9pRITvcPLMsNAMzhCp5VEzd9hD56erTZudxnIYFPZELZICyEN2TDBVTF1wNO7gc4n1jRKU7LGDUqv3BjVom1XEJ2STfNoEYo_krf5wpLgSczsyipl2nDUCtpBVsM04RZlXl38sRGn-5g","expires_in":300,"refresh_expires_in":1800,"refresh_token":"eyJhbGciOiJIUzUxMiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI2NjU0MTExZC1hNDdkLTQ3OWEtYTE1My1lOWZhYTQ5MzAzZGIifQ.eyJleHAiOjE3MjM0NTE0MTgsImlhdCI6MTcyMzQ0OTYxOCwianRpIjoiNmQwZTFlMTgtNzRkOC00YTQ3LWE1MzUtNGQ4M2FmMGM0MmM3IiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL3JlYWxtcy9kYXRhY2xheSIsImF1ZCI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODA4MC9yZWFsbXMvZGF0YWNsYXkiLCJzdWIiOiI2MWM2YjM5My1mZTU2LTQ5YzgtYmRkZC1iNDQxY2VmMTE1ODYiLCJ0eXAiOiJSZWZyZXNoIiwiYXpwIjoiY3VybC1kZW1vIiwic2lkIjoiZTNmZjdjNTQtMTQ4YS00NjlkLWI1YmMtOTBkZjI5OGQ2Y2U5Iiwic2NvcGUiOiJiYXNpYyBhY3IgcHJvZmlsZSBlbWFpbCB3ZWItb3JpZ2lucyByb2xlcyJ9.BMLeq4842YLX4jDf82o6Av2cue0axQKczDKbcesqXl9LxMlIuUJu_PFLfUdCWHPTBinY0v69EwIjubYMeT79zQ","token_type":"Bearer","not-before-policy":0,"session_state":"e3ff7c54-148a-469d-b5bc-90df298d6ce9","scope":"profile email"}
```

As you can see, the `access_token` received should be a valid signed JWT token encoded in base64. You can check its contents (the website https://jwt.io provides a handy and easy to use tool to check its contents).

Keep in mind that performing login (i.e. authentication) is not the focus of this example and is not part of dataClay.

Restricted dataset access example
---------------------------------

In this example the access to the `public_dataset` will be unrestricted, while accessing to `custom_dataset` requires the `custom_role` role (a role that user `user` has but user `luser` does not).

The example `public_access.py` shows how an unauthenticated user is able to write and read objects on `public_dataset`. The example `authorized_access.py` shows how the user `user` can write and read objects on `custom_dataset`. The example `unauthorized_access.py` shows how the user `luser` cannot access the `custom_dataset` and an exception is thrown.

This example oversimplifies the authentication step (prior to authorization) with a simple `requests.post` and hardcoded user/password. A real-life environment will behave differently and the authn/authz flow will be specific to every use case. Authentication is not part of dataClay and will depend on your threat model and security infrastructure.

**TODO**
