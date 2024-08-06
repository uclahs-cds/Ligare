from abc import ABC, abstractmethod


class FeatureFlagRouter(ABC):
    """
    The base feature flag router.
    All feature flag routers should extend this class.
    """

    @abstractmethod
    def _notify_enabled(self, name: str) -> None:
        """ """

    @abstractmethod
    def _notify_disabled(self, name: str) -> None:
        """ """

    @abstractmethod
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> None:
        """ """

    @abstractmethod
    def feature_is_enabled(
        self, name: str, default: bool | None = False
    ) -> bool | None:
        """ """
