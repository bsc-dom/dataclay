from middleware import ActiveMethodWhitelist
from dataclay.contrib.oidc import OIDCInterceptor
from dataclay.contrib.middleware import MiddlewareValidation
#from middleware_val import MyValidation

interceptors = [
    OIDCInterceptor("http://keycloak:8080"),#https://keycloak.dev.icos.91.109.56.214.sslip.io
]

middleware_backend = [
    ActiveMethodWhitelist(user="user", methods=["add_year", "get"]),
    ActiveMethodWhitelist(user="luser", methods=["add_year", "get"]),
    MiddlewareValidation(),
    #MyValidation({"custom_dataset":{"custom_role_2","custom_role"}}), #{dataset_X:{which roles can access the dataset_X}}
]

# Not using middleware for MetadataService
middleware_metadata = []
