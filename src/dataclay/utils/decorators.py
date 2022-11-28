import functools

import grpc

from dataclay.exceptions import *


def grpc_error_handler(func):
    @functools.wraps(func)
    def wrapper_grpc_error_handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as e:
            raise DataClayException(e.details()) from None

    return wrapper_grpc_error_handler
