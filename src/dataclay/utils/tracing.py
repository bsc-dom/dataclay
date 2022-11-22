from opentelemetry import trace


class LoggerEvent:
    def __init__(self, logger):
        super().__setattr__("logger", logger)

    def __getattr__(self, name):
        def wrapper(msg, *args, **kwargs):
            current_span = trace.get_current_span()
            if current_span.is_recording:
                current_span.add_event(msg % args)
            getattr(self.logger, name)(msg, *args, **kwargs)

        return wrapper
