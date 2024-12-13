from .fixtures.context import mocked_context

# Mock decorator to that returns the original function
def decorator_mock(step_name):
    def wrapper(func):
        return func
    return wrapper
