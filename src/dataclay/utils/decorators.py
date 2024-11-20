import functools

import grpc

from dataclay.exceptions import AlreadyExistError, DataClayException, DoesNotExistError


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
            if "does not exist" in rpc_error.details():
                if "Alias" in rpc_error.details():
                    raise DoesNotExistError(
                        rpc_error.details().replace("Alias ", "").replace(" does not exist", "")
                    ) from None
                else:
                    raise DoesNotExistError(
                        rpc_error.details().replace(" does not exist", "")
                    ) from None
            elif "already exists" in rpc_error.details():
                if "Alias" in rpc_error.details():
                    raise AlreadyExistError(
                        rpc_error.details().replace("Alias ", "").replace(" already exists", "")
                    ) from None
                else:
                    raise AlreadyExistError(
                        rpc_error.details().replace(" already exists", "")
                    ) from None
            else:
                raise DataClayException(rpc_error.details()) from None

    return wrapper
