import logging
from typing import Any

import pytest
from BL_Python.platform.feature_flag.caching_feature_flag_router import (
    CachingFeatureFlagRouter,
)
from typing_extensions import override

_FEATURE_FLAG_TEST_NAME = "foo_feature"


def test__feature_is_enabled__disallows_empty_name():
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    with pytest.raises(ValueError):
        _ = caching_feature_flag_router.feature_is_enabled("")


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__feature_is_enabled__disallows_non_string_names(name: Any):
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    with pytest.raises(TypeError):
        _ = caching_feature_flag_router.feature_is_enabled(name)


def test__set_feature_is_enabled__disallows_empty_name():
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    with pytest.raises(ValueError):
        caching_feature_flag_router.set_feature_is_enabled("", False)


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__set_feature_is_enabled__disallows_non_string_names(name: Any):
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    with pytest.raises(TypeError):
        caching_feature_flag_router.set_feature_is_enabled(name, False)


@pytest.mark.parametrize("value", [None, "", "False", "True", 0, 1, -1, {}, [], (0,)])
def test__set_feature_is_enabled__disallows_non_bool_values(value: Any):
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    with pytest.raises(TypeError) as e:
        _ = caching_feature_flag_router.set_feature_is_enabled(
            _FEATURE_FLAG_TEST_NAME, value
        )

    assert e.match("`is_enabled` must be a boolean")


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__sets_correct_value(value: bool):
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    caching_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, value)
    is_enabled = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == value


def test__feature_is_enabled__defaults_to_false_when_flag_does_not_exist():
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    is_enabled = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == False


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__caches_new_flag(value: bool):
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    caching_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, value)
    assert _FEATURE_FLAG_TEST_NAME in caching_feature_flag_router._feature_flags  # pyright: ignore[reportPrivateUsage]
    is_enabled = caching_feature_flag_router._feature_flags.get(_FEATURE_FLAG_TEST_NAME)  # pyright: ignore[reportPrivateUsage]
    assert is_enabled == value


@pytest.mark.parametrize("value", [True, False])
def test__feature_is_enabled__uses_cache(value: bool):
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    call_count = 0

    class FakeDict(dict):  # pyright: ignore[reportMissingTypeArgument]
        @override
        def __getitem__(self, key: Any) -> Any:
            nonlocal call_count
            call_count += 1
            return super().__getitem__(key)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]

    caching_feature_flag_router._feature_flags = FakeDict()  # pyright: ignore[reportPrivateUsage]

    caching_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, value)
    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert call_count == 2


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__resets_cache_when_flag_enable_is_set(enable: bool):
    logger = logging.getLogger("FeatureFlagLogger")
    caching_feature_flag_router = CachingFeatureFlagRouter(logger)

    caching_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    first_value = caching_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME
    )

    caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, not enable
    )
    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    second_value = caching_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME
    )

    assert first_value == enable
    assert second_value == (not enable)
