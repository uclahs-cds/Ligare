import cProfile
from functools import wraps
from logging import Logger
from random import choice
from string import ascii_letters
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable


def do_profile(fn: "Callable[..., Any]"):
    """
    Use this decorator to start cProfile when the decorated method is called.
    This will save the profile data to a file named `profile.{name_of_the_decorated_method}.{a random string of 8 characters}`

    Usage:

    @do_profile
    def foo():
        ...
    """

    @wraps(fn)
    def decorated_view(*args: "Any", **kwargs: "Any"):
        with cProfile.Profile() as pr:
            result = pr.runcall(fn, *args, **kwargs)
            profile_filename = f"profile.{fn.__name__}.{''.join(choice(ascii_letters) for _ in range(8))}"
            Logger("PROFILE").warn(f"Saving profile to {profile_filename}")
            pr.dump_stats(profile_filename)
            return result

    return decorated_view
