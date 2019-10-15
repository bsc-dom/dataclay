
""" Class description goes here. """

"""Interceptor for GRPC server calls."""

from grpc import ServerInterceptor
from logging import getLogger

from dataclay import PrvManager
from dataclay.paraver.prv_traces import TraceType
from dataclay.commonruntime.Settings import settings
from . import HEADER_MESSAGEID
from decorator import decorator, decorate
import time

logger = getLogger(__name__)


class ParaverServerInterceptor(ServerInterceptor):

    request_id = None
    sv_client_port = None

    def __init__(self, origin_hostname, origin_port):
        logger.debug("Initialize ParaverServerInterceptor")
        self.origin_hostname = origin_hostname
        self.origin_port = origin_port
        self.prv_manager = PrvManager.get_manager()

    def intercept_service(self, continuation, handler_call_details):
        """
        Override of the ServerInterceptor method.
        If paraver is active (activate_paraver_traces) get the req_id from metadata
        and store the client_port as class var, then add the receive trace to the traces queue.

        :param continuation: A function that takes a HandlerCallDetails and proceeds to invoke the next interceptor in the chain,
                             if any, or the RPC handler lookup logic, with the call details passed as an argument,
                             and returns an RpcMethodHandler instance if the RPC is considered serviced, or None otherwise.
        :param handler_call_details: A HandlerCallDetails describing the RPC.
        :return: Response of the RPC.
        """
        if settings.paraver_tracing_enabled:

            logger.debug("Intercept")
            
            try:
                ParaverServerInterceptor.request_id = int(handler_call_details.invocation_metadata[1].value)
            except Exception:
                try:
                    ParaverServerInterceptor.request_id = int(handler_call_details.invocation_metadata[0].value)
                except Exception:
                    return continuation(handler_call_details)

            if "java" in handler_call_details.invocation_metadata[0].value:
                # If client call comes from Java client_port is logicmodule_port
                ParaverServerInterceptor.sv_client_port = settings.logicmodule_port
                
            elif "python" in handler_call_details.invocation_metadata[1].value:
                # If comes from python client_port is static one defined in client interceptor
                ParaverServerInterceptor.sv_client_port = 892892
                
            client_port = ParaverServerInterceptor.sv_client_port

            self.prv_manager.add_network_receive(
                self.origin_hostname,
                client_port, 
                ParaverServerInterceptor.request_id,
                0 # unknown/unused method id
            )
            response = continuation(handler_call_details)

            return response

        else:
            return continuation(handler_call_details)

    def add_send(self):
        """ If Paraver is active add the send trace to the traces queue"""
        if settings.paraver_tracing_enabled:
            if ParaverServerInterceptor.request_id == None:
                # Interceptor didn't receive request
                return
            
            self.prv_manager.add_network_send(
                int(time.time() * 1000000000),
                TraceType.SEND_RESPONSE,
                self.origin_port,
                ParaverServerInterceptor.request_id,
                self.origin_hostname,
                ParaverServerInterceptor.sv_client_port,
                0,  # unknown/unused message size
                0   # unknown/unused method id
            )
