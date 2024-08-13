import logging
from typing import Any, Tuple

import pytest
from Ligare.database.config import DatabaseConfig
from Ligare.database.dependency_injection import ScopedSessionModule
from Ligare.platform.feature_flag.db_feature_flag_router import (
    DBFeatureFlagRouter,
    FeatureFlag,
    FeatureFlagTable,
)
from Ligare.programming.dependency_injection import ConfigModule
from pytest_mock import MockerFixture
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm.session import Session

_FEATURE_FLAG_TEST_NAME = "foo_feature"
_FEATURE_FLAG_TEST_DESCRIPTION = "foo description"
_FEATURE_FLAG_LOGGER_NAME = "FeatureFlagLogger"


class PlatformMetaBase(DeclarativeMeta):
    pass


class PlatformBase(object):
    pass


from Ligare.database.testing.config import inmemory_database_config

PlatformBase = declarative_base(cls=PlatformBase, metaclass=PlatformMetaBase)
FeatureFlagTableBase = FeatureFlagTable(PlatformBase)


@pytest.fixture()
def feature_flag_session():
    from injector import Injector

    injector = Injector([
        ConfigModule(inmemory_database_config(), DatabaseConfig),
        ScopedSessionModule(bases=[PlatformBase]),  # pyright: ignore[reportArgumentType]
    ])

    session = injector.get(Session)
    PlatformBase.metadata.create_all(session.bind)  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
    return session


def _create_feature_flag(
    session: Session, name: str | None = None, description: str | None = None
):
    session.add(
        FeatureFlagTableBase(
            name=_FEATURE_FLAG_TEST_NAME if name is None else name,
            description=_FEATURE_FLAG_TEST_DESCRIPTION
            if description is None
            else description,
        )
    )
    session.commit()


def test__feature_is_enabled__defaults_to_false(feature_flag_session: Session):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )
    _create_feature_flag(feature_flag_session)

    # The value is false because it was not explicitly enabled. This is the database default value.
    is_enabled = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == False


@pytest.mark.parametrize("default", [True, False])
def test__feature_is_enabled__uses_default_when_flag_does_not_exist(
    default: bool,
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    is_enabled = db_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, default
    )

    assert is_enabled == default


def test__feature_is_enabled__disallows_empty_name(feature_flag_session: Session):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    with pytest.raises(ValueError):
        _ = db_feature_flag_router.feature_is_enabled("")


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__feature_is_enabled__disallows_non_string_names(
    name: Any, feature_flag_session: Session
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    with pytest.raises(TypeError):
        _ = db_feature_flag_router.feature_is_enabled(name)


def test__set_feature_is_enabled__fails_when_flag_does_not_exist(
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    with pytest.raises(LookupError):
        db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, True)


def test__set_feature_is_enabled__disallows_empty_name(feature_flag_session: Session):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )
    _create_feature_flag(feature_flag_session)

    with pytest.raises(ValueError):
        db_feature_flag_router.set_feature_is_enabled("", False)


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__set_feature_is_enabled__disallows_non_string_names(
    name: Any, feature_flag_session: Session
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    with pytest.raises(TypeError):
        db_feature_flag_router.set_feature_is_enabled(name, False)


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__sets_correct_value(
    enable: bool, feature_flag_session: Session
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )
    _create_feature_flag(feature_flag_session)

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    is_enabled = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == enable


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__caches_flags(enable: bool, mocker: MockerFixture):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    session_query_mock = mocker.patch("sqlalchemy.orm.session.Session.query")
    session_mock.query = session_query_mock

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, session_mock, logger
    )

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert session_query_mock.call_count == 1


@pytest.mark.parametrize("check_cache", [(True, 1), (False, 0)])
def test__feature_is_enabled__checks_cache(
    check_cache: Tuple[bool, int], mocker: MockerFixture
):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    feature_is_enabled_mock = mocker.patch(
        "Ligare.platform.feature_flag.caching_feature_flag_router.CachingFeatureFlagRouter.feature_is_cached"
    )
    _ = mocker.patch(
        "Ligare.platform.feature_flag.caching_feature_flag_router.CachingFeatureFlagRouter.set_feature_is_enabled"
    )

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, session_mock, logger
    )

    _ = db_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, False, check_cache[0]
    )

    assert feature_is_enabled_mock.call_count == check_cache[1]


@pytest.mark.parametrize("check_cache", [(True, 0), (False, 1)])
def test__feature_is_enabled__sets_cache(
    check_cache: Tuple[bool, int], mocker: MockerFixture
):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    feature_is_enabled_mock = mocker.patch(
        "Ligare.platform.feature_flag.caching_feature_flag_router.CachingFeatureFlagRouter.feature_is_cached"
    )
    set_feature_is_enabled_mock = mocker.patch(
        "Ligare.platform.feature_flag.caching_feature_flag_router.CachingFeatureFlagRouter.set_feature_is_enabled"
    )
    feature_is_enabled_mock.return_value = True

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, session_mock, logger
    )

    _ = db_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, False, check_cache[0]
    )

    assert set_feature_is_enabled_mock.call_count == check_cache[1]


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__resets_cache_when_flag_enable_is_set(
    enable: bool, mocker: MockerFixture
):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    session_query_mock = mocker.patch("sqlalchemy.orm.session.Session.query")
    session_mock.query = session_query_mock

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, session_mock, logger
    )

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    first_value = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, not enable)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    second_value = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert session_query_mock.call_count == 2
    assert first_value == enable
    assert second_value == (not enable)


def test___create_feature_flag__returns_correct_TFeatureFlag(
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    feature_flag = db_feature_flag_router._create_feature_flag(  # pyright: ignore[reportPrivateUsage]
        _FEATURE_FLAG_TEST_NAME, True
    )

    assert isinstance(feature_flag, FeatureFlag)


@pytest.mark.parametrize("value", [True, False])
def test___create_feature_flag__creates_correct_TFeatureFlag(
    value: bool,
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    feature_flag = db_feature_flag_router._create_feature_flag(  # pyright: ignore[reportPrivateUsage]
        _FEATURE_FLAG_TEST_NAME, value
    )

    assert feature_flag.name == _FEATURE_FLAG_TEST_NAME
    assert feature_flag.enabled == value


def test__get_feature_flags__returns_empty_sequence_when_no_flags_exist(
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    feature_flags = db_feature_flag_router.get_feature_flags()

    assert isinstance(feature_flags, tuple)
    assert not feature_flags


@pytest.mark.parametrize(
    "added_flags,filtered_flags",
    [
        [{f"{_FEATURE_FLAG_TEST_NAME}2": True}, [f"{_FEATURE_FLAG_TEST_NAME}1"]],
        [{f"{_FEATURE_FLAG_TEST_NAME}2": False}, [f"{_FEATURE_FLAG_TEST_NAME}3"]],
        [
            {
                f"{_FEATURE_FLAG_TEST_NAME}1": True,
                f"{_FEATURE_FLAG_TEST_NAME}1": False,
                f"{_FEATURE_FLAG_TEST_NAME}2": True,
                f"{_FEATURE_FLAG_TEST_NAME}2": False,
                f"{_FEATURE_FLAG_TEST_NAME}3": True,
                f"{_FEATURE_FLAG_TEST_NAME}3": False,
            },
            [f"{_FEATURE_FLAG_TEST_NAME}4", f"{_FEATURE_FLAG_TEST_NAME}5"],
        ],
    ],
)
def test__get_feature_flags__returns_empty_sequence_when_flags_exist_but_filtered_list_does_not_exist(
    added_flags: dict[str, bool],
    filtered_flags: list[str],
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    for flag_name, enabled in added_flags.items():
        _create_feature_flag(feature_flag_session, flag_name)
        db_feature_flag_router.set_feature_is_enabled(flag_name, enabled)

    feature_flags = db_feature_flag_router.get_feature_flags(filtered_flags)

    assert isinstance(feature_flags, tuple)
    assert len(feature_flags) == 0


@pytest.mark.parametrize(
    "added_flags",
    [
        {f"{_FEATURE_FLAG_TEST_NAME}2": True},
        {f"{_FEATURE_FLAG_TEST_NAME}2": False},
        {
            f"{_FEATURE_FLAG_TEST_NAME}1": True,
            f"{_FEATURE_FLAG_TEST_NAME}1": False,
            f"{_FEATURE_FLAG_TEST_NAME}2": True,
            f"{_FEATURE_FLAG_TEST_NAME}2": False,
            f"{_FEATURE_FLAG_TEST_NAME}3": True,
            f"{_FEATURE_FLAG_TEST_NAME}3": False,
        },
    ],
)
def test__get_feature_flags__returns_all_existing_flags(
    added_flags: dict[str, bool],
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    for flag_name, enabled in added_flags.items():
        _create_feature_flag(feature_flag_session, flag_name)
        db_feature_flag_router.set_feature_is_enabled(flag_name, enabled)

    feature_flags = db_feature_flag_router.get_feature_flags()
    feature_flags_dict = {
        feature_flag.name: feature_flag.enabled for feature_flag in feature_flags
    }

    assert isinstance(feature_flags, tuple)
    assert len(feature_flags) == len(added_flags)

    for filtered_flag in feature_flags_dict:
        assert filtered_flag in feature_flags_dict
        assert feature_flags_dict[filtered_flag] == added_flags[filtered_flag]


@pytest.mark.parametrize(
    "added_flags,filtered_flags",
    [
        [{f"{_FEATURE_FLAG_TEST_NAME}2": True}, [f"{_FEATURE_FLAG_TEST_NAME}2"]],
        [{f"{_FEATURE_FLAG_TEST_NAME}2": False}, [f"{_FEATURE_FLAG_TEST_NAME}2"]],
        [
            {
                f"{_FEATURE_FLAG_TEST_NAME}1": True,
                f"{_FEATURE_FLAG_TEST_NAME}1": False,
                f"{_FEATURE_FLAG_TEST_NAME}2": True,
                f"{_FEATURE_FLAG_TEST_NAME}2": False,
                f"{_FEATURE_FLAG_TEST_NAME}3": True,
                f"{_FEATURE_FLAG_TEST_NAME}3": False,
            },
            [f"{_FEATURE_FLAG_TEST_NAME}1", f"{_FEATURE_FLAG_TEST_NAME}2"],
        ],
    ],
)
def test__get_feature_flags__returns_filtered_flags(
    added_flags: dict[str, bool],
    filtered_flags: list[str],
    feature_flag_session: Session,
):
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_session, logger
    )

    for flag_name, enabled in added_flags.items():
        _create_feature_flag(feature_flag_session, flag_name)
        db_feature_flag_router.set_feature_is_enabled(flag_name, enabled)

    feature_flags = db_feature_flag_router.get_feature_flags(filtered_flags)
    feature_flags_dict = {
        feature_flag.name: feature_flag.enabled for feature_flag in feature_flags
    }

    assert isinstance(feature_flags, tuple)
    assert len(feature_flags) == len(filtered_flags)

    for filtered_flag in filtered_flags:
        assert filtered_flag in feature_flags_dict
        assert feature_flags_dict[filtered_flag] == added_flags[filtered_flag]
