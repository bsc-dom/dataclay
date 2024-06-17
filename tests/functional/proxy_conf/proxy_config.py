from middleware import ActiveMethodWhitelist

middleware_backend = [
    ActiveMethodWhitelist(user="Marc", methods=["add_year", "get"]),
    ActiveMethodWhitelist(user="David", methods=["set"]),
]
