from middleware import ActiveMethodWhitelist

# No interceptors used
interceptors = []

middleware_backend = [
    ActiveMethodWhitelist(user="alice", methods=["add_element"]),
    ActiveMethodWhitelist(user="bob", methods=["public_data"]),
    ActiveMethodWhitelist(user="charlie", methods=[]),
]

# Not using middleware for MetadataService
middleware_metadata = []
