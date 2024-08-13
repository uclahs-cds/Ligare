import ast
import inspect
from typing import Sequence

from Ligare.platform.feature_flag.feature_flag_router import (
    FeatureFlag,
    FeatureFlagChange,
    FeatureFlagRouter,
)
from typing_extensions import override

_FEATURE_FLAG_TEST_NAME = "foo_feature"


class TestFeatureFlagRouter(FeatureFlagRouter[FeatureFlag]):
    @override
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> FeatureFlagChange:
        return super().set_feature_is_enabled(name, is_enabled)

    @override
    def feature_is_enabled(self, name: str, default: bool = False) -> bool:
        return super().feature_is_enabled(name, default)

    @override
    def _create_feature_flag(self, name: str, enabled: bool) -> FeatureFlag:
        return super()._create_feature_flag(name, enabled)

    @override
    def get_feature_flags(
        self, names: list[str] | None = None
    ) -> Sequence[FeatureFlag]:
        return super().get_feature_flags(names)


class NotifyingFeatureFlagRouter(TestFeatureFlagRouter):
    def __init__(self) -> None:
        self.notification_count = 0
        super().__init__()

    @override
    def _notify_change(
        self, name: str, new_value: bool, old_value: bool | None
    ) -> None:
        self.notification_count += 1
        return super()._notify_change(name, new_value, old_value)


def test___notify_change__is_a_noop():
    test_feature_flag_router = TestFeatureFlagRouter()
    source = inspect.getsource(test_feature_flag_router._notify_change)  # pyright: ignore[reportPrivateUsage]
    # strip the leading \t because the method is in a class
    # and the AST parse will fail because of unexpected indent
    parsed = ast.parse(source.strip())
    function_node = parsed.body[0]
    # [0] is the docblock
    function_body_nodes = function_node.body[1:]  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType,reportAttributeAccessIssue]

    # empty means the function doesn't contain any code
    assert not function_body_nodes


def test__set_feature_is_enabled__does_not_notify():
    notifying_feature_flag_router = NotifyingFeatureFlagRouter()

    _ = notifying_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, True
    )

    assert notifying_feature_flag_router.notification_count == 0


def test__feature_is_enabled__does_not_notify():
    notifying_feature_flag_router = NotifyingFeatureFlagRouter()

    _ = notifying_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert notifying_feature_flag_router.notification_count == 0


def test__feature_is_enabled__does_not_notify_after_flag_is_set():
    notifying_feature_flag_router = NotifyingFeatureFlagRouter()

    _ = notifying_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, True
    )
    notifying_feature_flag_router.notification_count = 0

    _ = notifying_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert notifying_feature_flag_router.notification_count == 0
