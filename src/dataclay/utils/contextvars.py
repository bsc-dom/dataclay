import contextvars


def run_in_context(context: contextvars.Context, callable, *args, **kwargs):
    """Run a callable with a given context"""
    return context.run(callable, *args, **kwargs)
