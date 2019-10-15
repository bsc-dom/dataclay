
""" Class description goes here. """

"""Interceptor for GRPC client calls."""

from grpc import UnaryUnaryClientInterceptor
from logging import getLogger

from dataclay import PrvManager
from dataclay.communication.grpc.paraver import HEADER_CLIENTPORT
from dataclay.paraver.prv_traces import TraceType
from dataclay.commonruntime.Settings import settings

from . import HEADER_MESSAGEID
import time

logger = getLogger(__name__)


class ParaverClientInterceptor(UnaryUnaryClientInterceptor):

    def __init__(self, origin_hostname, remote_hostaddr, remote_port):
        logger.debug("Initialize ParaverClientInterceptor")
        self.request_id = 42
        self.prv_manager = PrvManager.get_manager()
        self.origin_hostname = origin_hostname
        self.remote_hostaddr = remote_hostaddr
        self.remote_port = remote_port

    def intercept_unary_unary(self, continuation, client_call_details, request):
        """
        Override of the UnaryUnaryClientInterceptor method.
        If paraver is active (activate_paraver_traces) add req_id to metadata
        and try to get the client_port from it after the response, then add the send/receive traces to the traces queue. 

        :param continuation: A function that proceeds with the invocation by executing the next interceptor in chain
                             or invoking the actual RPC on the underlying Channel.
                             It is the interceptor's responsibility to call it if it decides to move the RPC forward.
                             The interceptor can use response_future = continuation(client_call_details, request) to continue with the RPC.
                             continuation returns an object that is both a Call for the RPC and a Future. 
                             In the event of RPC completion, the return Call-Future's result value will be the response message of the RPC.
                             Should the event terminate with non-OK status, the returned Call-Future's exception value will be an RpcError.

        :param client_call_details: A ClientCallDetails object describing the outgoing RPC.
        :param request: The request value for the RPC.
        :return: Response of the RPC.
        """
        if settings.paraver_tracing_enabled:
                
            logger.debug("Intercept")
            req_id = self.request_id
            self.request_id += 1

            metadata = client_call_details.metadata
            if not metadata:
                metadata = list()

            metadata.append((HEADER_MESSAGEID, str(req_id)))

            # It is known that client_call_details is in fact a namedtuple,
            # (i.e. inmutable) so let's take advantage of the _replace method
            new_call_details = client_call_details._replace(metadata=metadata)
            
            send_time = int(time.time() * 1000000000)
            response = continuation(new_call_details, request)
            metadata = response.initial_metadata()

            client_port = dict(metadata).get(HEADER_CLIENTPORT)
            if not client_port:
                # If we can't retrieve the client port assign a static value in client/server interceptor
                client_port = 892892
            
            self.prv_manager.add_network_send(
                send_time,
                TraceType.SEND_REQUEST,
                int(client_port),
                req_id,
                self.remote_hostaddr,
                self.remote_port,
                0,  # unknown/unused message size
                0  # unknown/unused method id
            )

            self.prv_manager.add_network_receive(
                self.remote_hostaddr,
                self.remote_port,
                req_id,
                0
            )
            return response
        else:
            return continuation(client_call_details, request)
            
