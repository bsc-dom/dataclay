import functools
import logging

logger = logging.getLogger(__name__)


class Dummy1:
    def get_tracer(self, name):
        return Dummy2()


class Dummy2:
    def start_as_current_span(self, *args, **kwargs):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator


try:
    from opentelemetry import trace
except ImportError:
    trace = Dummy1()


class LoggerEvent:
    def __init__(self, logger):
        super().__setattr__("logger", logger)

    def __getattr__(self, name):
        def wrapper(msg, *args, **kwargs):
            if not isinstance(trace, Dummy1):
                current_span = trace.get_current_span()
                if current_span.is_recording:
                    current_span.add_event(msg % args)
            getattr(self.logger, name)(msg, *args, **kwargs)

        return wrapper


def set_tracer_provider(service_name, hostname, port, exporter="otlp"):
    logger.info(f"Setting tracer {exporter} for service {service_name} to {hostname}:{port}")
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource(attributes={SERVICE_NAME: service_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))

    if exporter == "otlp":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        otlp_exporter = OTLPSpanExporter(endpoint=f"{hostname}:{port}", insecure=True)
        processor = BatchSpanProcessor(otlp_exporter)

    elif exporter == "console":
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        processor = BatchSpanProcessor(ConsoleSpanExporter())

    trace.get_tracer_provider().add_span_processor(processor)

    if service_name == "client":
        from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

        GrpcInstrumentorClient().instrument()
    else:
        from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        GrpcInstrumentorServer().instrument()
        RedisInstrumentor().instrument()
