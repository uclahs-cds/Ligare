from abc import ABC, abstractmethod


class FeatureFlagRouter(ABC):
    """
    The base feature flag router.
    All feature flag routers should extend this class.
    """

    @abstractmethod
    def _notify_enabled(self, name: str) -> None:
        """
        Override to provide a method to be used to notify when a feature is enabled.
        Implementation of when and whether this is called is the responsibility of subclasses.
        This is never called by default.

        :param str name: The name of the feature flag.
        """

    @abstractmethod
    def _notify_disabled(self, name: str) -> None:
        """
        Override to provide a method to be used to notify when a feature is disabled.
        Implementation of when and whether this is called is the responsibility of subclasses.
        This is never called by default.

        :param str name: The name of the feature flag.
        """

    @abstractmethod
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> None:
        """
        Enable or disable a feature flag.

        :param str name: The name of the feature flag.
        :param bool is_enabled: If `True`, the feature is enabled. If `False`, the feature is disabled.
        """

    @abstractmethod
    def feature_is_enabled(
        self, name: str, default: bool | None = False
    ) -> bool | None:
        """
        Determine whether a feature flag is enabled or disabled.

        :param str name: The name of the feature flag.
        :param bool | None default: A default value to return for cases where a feature flag may not exist. Defaults to False.
        :return bool | None: If `True`, the feature is enabled. If `False` or `None`, the feature is disabled.
        """
