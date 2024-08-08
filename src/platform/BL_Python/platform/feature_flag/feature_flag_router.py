from abc import ABC, abstractmethod


class FeatureFlagRouter(ABC):
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
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> None:
        """
        Enable or disable a feature flag.

        :param str name: The name of the feature flag.
        :param bool is_enabled: If `True`, the feature is enabled. If `False`, the feature is disabled.
        """

    @abstractmethod
    def feature_is_enabled(self, name: str, default: bool = False) -> bool:
        """
        Determine whether a feature flag is enabled or disabled.

        :param str name: The name of the feature flag.
        :param bool default: A default value to return for cases where a feature flag may not exist. Defaults to False.
        :return bool: If `True`, the feature is enabled. If `False`, the feature is disabled.
        """
