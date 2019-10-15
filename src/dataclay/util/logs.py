
""" Class description goes here. """

import json
import logging


class JSONFormatter(logging.Formatter):
    """Simple JSON formatter for the logging facility."""
    def format(self, obj):
        """Note that obj is a LogRecord instance."""
        # Copy the dictionary
        ret = dict(obj.__dict__)

        # Perform the message substitution
        args = ret.pop("args")
        msg = ret.pop("msg")
        ret["message"] = msg % args

        # Exceptions must be formatted (they are not JSON-serializable
        try:
            ei = ret.pop("exc_info")
        except KeyError:
            pass
        else:
            if ei is not None:
                ret["exc_info"] = self.formatException(ei)

        # Dump the dictionary in JSON form
        return json.dumps(ret, skipkeys=True)
