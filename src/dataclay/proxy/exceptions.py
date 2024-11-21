"""The middleware can throw the exceptions defined below."""

class MiddlewareException(Exception):
    """Exception raised for errors in the middleware."""
    status_code = None
