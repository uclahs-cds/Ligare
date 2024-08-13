import logging
from typing import Any

import pytest
from Ligare.platform.feature_flag.caching_feature_flag_router import (
    CachingFeatureFlagRouter,
)
from Ligare.platform.feature_flag.feature_flag_router import FeatureFlag
from mock import MagicMock
from pytest import LogCaptureFixture

_FEATURE_FLAG_TEST_NAME = "foo_feature"
_FEATURE_FLAG_LOGGER_NAME = "FeatureFlagLogger"


def test__feature_is_enabled__disallows_empty_name():
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    with pytest.raises(ValueError):
        _ = caching_feature_flag_router.feature_is_enabled("")


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__feature_is_enabled__disallows_non_string_names(name: Any):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    with pytest.raises(TypeError):
        _ = caching_feature_flag_router.feature_is_enabled(name)


def test__set_feature_is_enabled__disallows_empty_name():
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    with pytest.raises(ValueError):
        _ = caching_feature_flag_router.set_feature_is_enabled("", False)


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__set_feature_is_enabled__disallows_non_string_names(name: Any):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    with pytest.raises(TypeError):
        _ = caching_feature_flag_router.set_feature_is_enabled(name, False)


@pytest.mark.parametrize("value", [None, "", "False", "True", 0, 1, -1, {}, [], (0,)])
def test__set_feature_is_enabled__disallows_non_bool_values(value: Any):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    with pytest.raises(TypeError) as e:
        _ = caching_feature_flag_router.set_feature_is_enabled(
            _FEATURE_FLAG_TEST_NAME, value
        )

    assert e.match("`is_enabled` must be a boolean")


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__sets_correct_value(value: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, value
    )
    is_enabled = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == value


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__returns_correct_initial_state(value: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    initial_change = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, value
    )

    assert initial_change.name == _FEATURE_FLAG_TEST_NAME
    assert initial_change.old_value is None
    assert initial_change.new_value == value


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__returns_correct_new_and_old_state(value: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    initial_change = caching_feature_flag_router.set_feature_is_enabled(  # pyright: ignore[reportUnusedVariable]
        _FEATURE_FLAG_TEST_NAME, value
    )
    change = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, not value
    )

    assert change.name == _FEATURE_FLAG_TEST_NAME
    assert change.old_value == value
    assert change.new_value == (not value)


def test__feature_is_enabled__defaults_to_false_when_flag_does_not_exist():
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    is_enabled = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == False


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__caches_new_flag(value: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, value
    )
    assert _FEATURE_FLAG_TEST_NAME in caching_feature_flag_router._feature_flags  # pyright: ignore[reportPrivateUsage]
    is_enabled = caching_feature_flag_router._feature_flags.get(_FEATURE_FLAG_TEST_NAME)  # pyright: ignore[reportPrivateUsage]
    assert is_enabled == value


@pytest.mark.parametrize("value", [True, False])
def test__feature_is_enabled__uses_cache(value: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    mock_dict = MagicMock()
    caching_feature_flag_router._feature_flags = mock_dict  # pyright: ignore[reportPrivateUsage]
    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, value
    )

    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert mock_dict.get.call_count == 3


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__resets_cache_when_flag_enable_is_set(enable: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, enable
    )
    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    first_value = caching_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME
    )

    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, not enable
    )
    _ = caching_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    second_value = caching_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME
    )

    assert first_value == enable
    assert second_value == (not enable)


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__notifies_when_setting_new_flag(
    value: bool,
    caplog: LogCaptureFixture,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, value
    )

    assert f"Setting new feature flag '{_FEATURE_FLAG_TEST_NAME}' to `{value}`." in {
        record.msg for record in caplog.records
    }


@pytest.mark.parametrize(
    "first_value,second_value,expected_log_msg",
    [
        [
            True,
            True,
            f"Tried to change feature flag value for '{_FEATURE_FLAG_TEST_NAME}' to the same value. It is already enabled.",
        ],
        [
            False,
            False,
            f"Tried to change feature flag value for '{_FEATURE_FLAG_TEST_NAME}' to the same value. It is already disabled.",
        ],
        [
            True,
            False,
            f"Changing feature flag value for '{_FEATURE_FLAG_TEST_NAME}' from `True` to `False`.",
        ],
        [
            False,
            True,
            f"Changing feature flag value for '{_FEATURE_FLAG_TEST_NAME}' from `False` to `True`.",
        ],
    ],
)
def test__set_feature_is_enabled__notifies_when_changing_flag(
    first_value: bool,
    second_value: bool,
    expected_log_msg: str,
    caplog: LogCaptureFixture,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, first_value
    )
    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, second_value
    )

    assert expected_log_msg in {record.msg for record in caplog.records}


@pytest.mark.parametrize("value", [True, False])
def test__feature_is_cached__correctly_determines_whether_value_is_cached(value: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    _ = caching_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, value
    )

    feature_is_cached = caching_feature_flag_router.feature_is_cached(
        _FEATURE_FLAG_TEST_NAME
    )

    assert feature_is_cached


def test___create_feature_flag__returns_correct_TFeatureFlag():
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    feature_flag = caching_feature_flag_router._create_feature_flag(  # pyright: ignore[reportPrivateUsage]
        _FEATURE_FLAG_TEST_NAME, True
    )

    assert isinstance(feature_flag, FeatureFlag)


@pytest.mark.parametrize("value", [True, False])
def test___create_feature_flag__creates_correct_TFeatureFlag(value: bool):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    feature_flag = caching_feature_flag_router._create_feature_flag(  # pyright: ignore[reportPrivateUsage]
        _FEATURE_FLAG_TEST_NAME, value
    )

    assert feature_flag.name == _FEATURE_FLAG_TEST_NAME
    assert feature_flag.enabled == value


def test__get_feature_flags__returns_empty_sequence_when_no_flags_exist():
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    feature_flags = caching_feature_flag_router.get_feature_flags()

    assert isinstance(feature_flags, tuple)
    assert not feature_flags


def test__get_feature_flags__returns_all_existing_flags():
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    FLAG_COUNT = 4

    for i in range(FLAG_COUNT):
        _ = caching_feature_flag_router.set_feature_is_enabled(
            f"{_FEATURE_FLAG_TEST_NAME}{i}", (i % 2) == 0
        )

    feature_flags = caching_feature_flag_router.get_feature_flags()

    assert isinstance(feature_flags, tuple)
    assert len(feature_flags) == FLAG_COUNT


def test__get_feature_flags__returns_filtered_flags():
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    caching_feature_flag_router = CachingFeatureFlagRouter[FeatureFlag](logger)

    FLAG_COUNT = 4
    FILTERED_FLAG_NAME = f"{_FEATURE_FLAG_TEST_NAME}2"

    for i in range(FLAG_COUNT):
        _ = caching_feature_flag_router.set_feature_is_enabled(
            f"{_FEATURE_FLAG_TEST_NAME}{i}", (i % 2) == 0
        )

    feature_flags = caching_feature_flag_router.get_feature_flags([FILTERED_FLAG_NAME])

    assert isinstance(feature_flags, tuple)
    assert len(feature_flags) == 1
    assert feature_flags[0].name == FILTERED_FLAG_NAME
    assert feature_flags[0].enabled  # (2 % 2) == 0 ## - True
