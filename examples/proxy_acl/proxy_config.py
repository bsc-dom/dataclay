from middleware import ActiveMethodWhitelist

# No interceptors used
interceptors = []

middleware_backend = [
    ActiveMethodWhitelist(user="alice", methods=["add_element", "get"]),
    ActiveMethodWhitelist(user="bob", methods=["public_data", "set", "get"]),
    ActiveMethodWhitelist(user="charlie", methods=[]),
]

# Not using middleware for MetadataService
middleware_metadata = []
