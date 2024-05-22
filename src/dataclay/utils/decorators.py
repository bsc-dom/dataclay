import functools

import grpc

from dataclay.exceptions import DataClayException


def grpc_error_handler(func):
    @functools.wraps(func)
    def wrapper_grpc_error_handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as e:
            raise DataClayException(e.details()) from None

    return wrapper_grpc_error_handler


def grpc_aio_error_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except grpc.aio.AioRpcError as rpc_error:
            raise DataClayException(rpc_error.details()) from None

    return wrapper
