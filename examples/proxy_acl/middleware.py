from pprint import pprint

from dataclay.proxy import MiddlewareBase, MiddlewareException, get_session

class ActiveMethodWhitelist(MiddlewareBase):
    def __init__(self, user, methods):
        self._user = user
        self._method_names = methods

    def CallActiveMethod(self, request, context):
        session = get_session(request)

        if session.username != self._user:
            # Not the user we filter
            return

        if request.method_name in self._method_names:
            # Method in whitelist
            return
        
        raise MiddlewareException("Method not allowed")
