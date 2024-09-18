from middleware import ActiveMethodWhitelist

# No interceptors used
interceptors = []

rd = {"custom_dataset":{"custom_role_2","custom_role"}}#{dataset_X:{which roles can access the dataset_X}}

middleware_backend = [
    ActiveMethodWhitelist(user="user", methods=["add_year", "get"], role_dataset=rd),
    ActiveMethodWhitelist(user="luser", methods=["add_year", "get"], role_dataset=rd),
]

# Not using middleware for MetadataService
middleware_metadata = []
