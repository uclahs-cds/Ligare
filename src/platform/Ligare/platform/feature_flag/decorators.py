from typing import Any, Callable

from injector import Injector, inject
from typing_extensions import overload

from .feature_flag_router import FeatureFlag, FeatureFlagRouter


@overload
def feature_flag(
    feature_flag_name: str, *, enabled_callback: Callable[..., Any]
) -> Callable[..., Callable[..., Any]]: ...
@overload
def feature_flag(
    feature_flag_name: str, *, disabled_callback: Callable[..., Any]
) -> Callable[..., Callable[..., Any]]: ...


def feature_flag(
    feature_flag_name: str,
    *,
    enabled_callback: Callable[..., None] = lambda: None,
    disabled_callback: Callable[..., None] = lambda: None,
) -> Callable[..., Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]):
        @inject
        def wrapper(
            feature_flag_router: FeatureFlagRouter[FeatureFlag],
            injector: Injector,
        ):
            if feature_flag_router.feature_is_enabled(feature_flag_name):
                enabled_callback()
            else:
                disabled_callback()

            return injector.call_with_injection(fn)

        return wrapper

    return decorator
