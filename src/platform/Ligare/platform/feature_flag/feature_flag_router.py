from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar


@dataclass(frozen=True)
class FeatureFlag:
    name: str
    enabled: bool


@dataclass(frozen=True)
class FeatureFlagChange:
    name: str
    old_value: bool | None
    new_value: bool | None


TFeatureFlag = TypeVar("TFeatureFlag", bound=FeatureFlag, covariant=True)


class FeatureFlagRouter(Generic[TFeatureFlag], ABC):
    """
    The base feature flag router.
    All feature flag routers should extend this class.
    """

    def _notify_change(
        self, name: str, new_value: bool, old_value: bool | None
    ) -> None:
        """
        Override to provide a method to be used to notify when a feature is enabled or disabled.
        Implementation of when and whether this is called is the responsibility of subclasses.
        This is never called by default; the base class implementation is a no-op.

        :param str name: The name of the feature flag.
        :param bool new_value: The value that the flag is changing to.
        :param bool | None old_value: The value that the flag is changing from.
        """

    @abstractmethod
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> FeatureFlagChange:
        """
        Enable or disable a feature flag.

        :param str name: The name of the feature flag.
        :param bool is_enabled: If `True`, the feature is enabled. If `False`, the feature is disabled.
        :return FeatureFlagChange: An object representing the previous and new values of the changed feature flag.
        """

    @abstractmethod
    def feature_is_enabled(self, name: str, default: bool = False) -> bool:
        """
        Determine whether a feature flag is enabled or disabled.

        :param str name: The name of the feature flag.
        :param bool default: A default value to return for cases where a feature flag may not exist. Defaults to False.
        :return bool: If `True`, the feature is enabled. If `False`, the feature is disabled.
        """

    @abstractmethod
    def _create_feature_flag(self, name: str, enabled: bool) -> FeatureFlag:
        """
        Subclasses should override this in order to instantiate type-safe
        instances of `TFeatureFlag` to any other `FeatureFlag` subclasses
        in the type hierarchy.

        :param str name: _description_
        :param bool enabled: _description_
        :return TFeatureFlag: An instance of `TFeatureFlag`
        """

    @abstractmethod
    def get_feature_flags(
        self, names: list[str] | None = None
    ) -> Sequence[TFeatureFlag]:
        """
        Get all feature flags and whether they are enabled.
        If `names` is not `None`, this only returns the enabled state of the flags in the list.

        :param list[str] | None names: Get only the flags contained in this list.
        :return tuple[TFeatureFlag]: An immutable sequence (a tuple) of feature flags.
        If `names` is `None` this sequence contains _all_ feature flags. Otherwise, the list is filtered.
        """
