class Dummy1:
    def get_tracer(self, name):
        return Dummy2()

class Dummy2:
    def start_as_current_span(self, *args, **kwargs):
        def decorator(func):
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
