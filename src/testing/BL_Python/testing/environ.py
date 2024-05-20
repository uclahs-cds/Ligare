from os import environ

import pytest


@pytest.fixture
def environ_resetter():
    """
    When the test finishes, reset `os.environ` to its state before the test started.
    """
    original_environ = environ.copy()
    try:
        yield
    finally:
        for key in set(environ) - set(original_environ):
            _ = environ.pop(key, None)
