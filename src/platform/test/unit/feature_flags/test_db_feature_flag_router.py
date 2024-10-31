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
from mock import MagicMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm.scoping import ScopedSession
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


def get_scoped_session_mock(session: Session | MagicMock):
    scoped_session_mock = MagicMock(
        return_value=MagicMock(__enter__=MagicMock(return_value=session))
    )
    return scoped_session_mock


@pytest.fixture()
def feature_flag_scoped_session() -> ScopedSession:
    from injector import Injector

    injector = Injector([
        ConfigModule(inmemory_database_config(), DatabaseConfig),
        ScopedSessionModule(bases=[PlatformBase]),  # pyright: ignore[reportArgumentType]
    ])

    scoped_session = injector.get(ScopedSession)
    return scoped_session


def get_feature_flag_session(feature_flag_scoped_session: ScopedSession) -> Session:
    with feature_flag_scoped_session() as session:
        PlatformBase.metadata.create_all(session.bind)  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
        return session


@pytest.fixture()
def feature_flag_session(feature_flag_scoped_session: ScopedSession) -> Session:
    return get_feature_flag_session(feature_flag_scoped_session)


@pytest.fixture()
def db_feature_flag_router(
    feature_flag_scoped_session: ScopedSession,
) -> DBFeatureFlagRouter[FeatureFlag]:
    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    return DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, feature_flag_scoped_session, logger
    )


def _create_feature_flag(
    session: Session, name: str | None = None, description: str | None = None
) -> None:
    session.add(
        FeatureFlagTableBase(
            name=_FEATURE_FLAG_TEST_NAME if name is None else name,
            description=_FEATURE_FLAG_TEST_DESCRIPTION
            if description is None
            else description,
        )
    )
    session.commit()


@pytest.fixture()
def create_feature_flag(feature_flag_session: Session):
    _create_feature_flag(feature_flag_session)


def test__feature_is_enabled__defaults_to_false(
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag], create_feature_flag: None
):
    # The value is false because it was not explicitly enabled. This is the database default value.
    is_enabled = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == False


@pytest.mark.parametrize("default", [True, False])
def test__feature_is_enabled__uses_default_when_flag_does_not_exist(
    default: bool,
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    is_enabled = db_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, default
    )

    assert is_enabled == default


def test__feature_is_enabled__disallows_empty_name(
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    with pytest.raises(ValueError):
        _ = db_feature_flag_router.feature_is_enabled("")


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__feature_is_enabled__disallows_non_string_names(
    name: Any,
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    with pytest.raises(TypeError):
        _ = db_feature_flag_router.feature_is_enabled(name)


def test__set_feature_is_enabled__fails_when_flag_does_not_exist(
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    with pytest.raises(LookupError):
        _ = db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, True)


def test__set_feature_is_enabled__disallows_empty_name(
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    with pytest.raises(ValueError):
        _ = db_feature_flag_router.set_feature_is_enabled("", False)


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__set_feature_is_enabled__disallows_non_string_names(
    name: Any,
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    with pytest.raises(TypeError):
        _ = db_feature_flag_router.set_feature_is_enabled(name, False)


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__sets_correct_value(
    enable: bool,
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    create_feature_flag: None,
):
    _ = db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    is_enabled = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == enable


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__caches_flags(enable: bool, mocker: MockerFixture):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    session_query_mock = mocker.patch("sqlalchemy.orm.session.Session.query")
    session_mock.query = session_query_mock
    scoped_session_mock = get_scoped_session_mock(session_mock)

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, scoped_session_mock, logger
    )

    _ = db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
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
    scoped_session_mock = get_scoped_session_mock(session_mock)

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, scoped_session_mock, logger
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
    scoped_session_mock = get_scoped_session_mock(session_mock)

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, scoped_session_mock, logger
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
    scoped_session_mock = get_scoped_session_mock(session_mock)

    logger = logging.getLogger(_FEATURE_FLAG_LOGGER_NAME)
    db_feature_flag_router = DBFeatureFlagRouter[FeatureFlag](
        FeatureFlagTableBase, scoped_session_mock, logger
    )

    _ = db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    first_value = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    _ = db_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, not enable
    )
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    second_value = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert session_query_mock.call_count == 2
    assert first_value == enable
    assert second_value == (not enable)


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__returns_correct_initial_state(
    value: bool,
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    create_feature_flag: None,
):
    initial_change = db_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, value
    )

    assert initial_change.name == _FEATURE_FLAG_TEST_NAME
    assert initial_change.old_value == False
    assert initial_change.new_value == value


@pytest.mark.parametrize("value", [True, False])
def test__set_feature_is_enabled__returns_correct_new_and_old_state(
    value: bool,
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    create_feature_flag: None,
):
    initial_change = db_feature_flag_router.set_feature_is_enabled(  # pyright: ignore[reportUnusedVariable]
        _FEATURE_FLAG_TEST_NAME, value
    )
    change = db_feature_flag_router.set_feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, not value
    )

    assert change.name == _FEATURE_FLAG_TEST_NAME
    assert change.old_value == value
    assert change.new_value == (not value)


def test___create_feature_flag__returns_correct_TFeatureFlag(
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
):
    feature_flag = db_feature_flag_router._create_feature_flag(  # pyright: ignore[reportPrivateUsage]
        _FEATURE_FLAG_TEST_NAME, True, _FEATURE_FLAG_TEST_DESCRIPTION
    )

    assert isinstance(feature_flag, FeatureFlag)


@pytest.mark.parametrize("value", [True, False])
def test___create_feature_flag__creates_correct_TFeatureFlag(
    value: bool,
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
):
    feature_flag = db_feature_flag_router._create_feature_flag(  # pyright: ignore[reportPrivateUsage]
        _FEATURE_FLAG_TEST_NAME, value, _FEATURE_FLAG_TEST_DESCRIPTION
    )

    assert feature_flag.name == _FEATURE_FLAG_TEST_NAME
    assert feature_flag.description == _FEATURE_FLAG_TEST_DESCRIPTION
    assert feature_flag.enabled == value


def test__get_feature_flags__returns_empty_sequence_when_no_flags_exist(
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    feature_flags = db_feature_flag_router.get_feature_flags()

    assert isinstance(feature_flags, tuple)
    assert not feature_flags


@pytest.mark.parametrize(
    "added_flags",
    [
        {f"{_FEATURE_FLAG_TEST_NAME}2": True},
        {f"{_FEATURE_FLAG_TEST_NAME}2": False},
        {
            f"{_FEATURE_FLAG_TEST_NAME}1": True,
            f"{_FEATURE_FLAG_TEST_NAME}2": False,
            f"{_FEATURE_FLAG_TEST_NAME}3": True,
            f"{_FEATURE_FLAG_TEST_NAME}4": False,
            f"{_FEATURE_FLAG_TEST_NAME}5": True,
            f"{_FEATURE_FLAG_TEST_NAME}6": False,
        },
    ],
)
def test__get_feature_flags__returns_all_existing_flags(
    added_flags: dict[str, bool],
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    for flag_name, enabled in added_flags.items():
        _create_feature_flag(feature_flag_session, flag_name)
        _ = db_feature_flag_router.set_feature_is_enabled(flag_name, enabled)

    feature_flags = db_feature_flag_router.get_feature_flags()
    feature_flags_dict = {
        feature_flag.name: (feature_flag.enabled, feature_flag.description)
        for feature_flag in feature_flags
    }

    assert isinstance(feature_flags, tuple)
    assert len(feature_flags) == len(added_flags)

    for filtered_flag in feature_flags_dict:
        assert filtered_flag in feature_flags_dict
        assert feature_flags_dict[filtered_flag][0] == added_flags[filtered_flag]
        assert feature_flags_dict[filtered_flag][1] == _FEATURE_FLAG_TEST_DESCRIPTION


@pytest.mark.parametrize(
    "added_flags,filtered_flags",
    [
        [{f"{_FEATURE_FLAG_TEST_NAME}2": True}, [f"{_FEATURE_FLAG_TEST_NAME}2"]],
        [{f"{_FEATURE_FLAG_TEST_NAME}2": False}, [f"{_FEATURE_FLAG_TEST_NAME}2"]],
        [
            {
                f"{_FEATURE_FLAG_TEST_NAME}1": True,
                f"{_FEATURE_FLAG_TEST_NAME}2": False,
                f"{_FEATURE_FLAG_TEST_NAME}3": True,
                f"{_FEATURE_FLAG_TEST_NAME}4": False,
                f"{_FEATURE_FLAG_TEST_NAME}5": True,
                f"{_FEATURE_FLAG_TEST_NAME}6": False,
            },
            [f"{_FEATURE_FLAG_TEST_NAME}1", f"{_FEATURE_FLAG_TEST_NAME}2"],
        ],
    ],
)
def test__get_feature_flags__returns_filtered_flags(
    added_flags: dict[str, bool],
    filtered_flags: list[str],
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    for flag_name, enabled in added_flags.items():
        _create_feature_flag(feature_flag_session, flag_name)
        _ = db_feature_flag_router.set_feature_is_enabled(flag_name, enabled)

    feature_flags = db_feature_flag_router.get_feature_flags(filtered_flags)
    feature_flags_dict = {
        feature_flag.name: (feature_flag.enabled, feature_flag.description)
        for feature_flag in feature_flags
    }

    assert isinstance(feature_flags, tuple)
    assert len(feature_flags) == len(filtered_flags)

    for filtered_flag in filtered_flags:
        assert filtered_flag in feature_flags_dict
        assert feature_flags_dict[filtered_flag][0] == added_flags[filtered_flag]
        assert feature_flags_dict[filtered_flag][1] == _FEATURE_FLAG_TEST_DESCRIPTION


@pytest.mark.parametrize(
    "added_flags,filtered_flags",
    [
        [{f"{_FEATURE_FLAG_TEST_NAME}2": True}, [f"{_FEATURE_FLAG_TEST_NAME}1"]],
        [{f"{_FEATURE_FLAG_TEST_NAME}2": False}, [f"{_FEATURE_FLAG_TEST_NAME}3"]],
        [
            {
                f"{_FEATURE_FLAG_TEST_NAME}1": True,
                f"{_FEATURE_FLAG_TEST_NAME}2": False,
                f"{_FEATURE_FLAG_TEST_NAME}3": True,
                f"{_FEATURE_FLAG_TEST_NAME}4": False,
                f"{_FEATURE_FLAG_TEST_NAME}5": True,
                f"{_FEATURE_FLAG_TEST_NAME}6": False,
            },
            [f"{_FEATURE_FLAG_TEST_NAME}7", f"{_FEATURE_FLAG_TEST_NAME}8"],
        ],
    ],
)
def test__get_feature_flags__returns_empty_sequence_when_flags_exist_but_filtered_list_items_do_not_exist(
    added_flags: dict[str, bool],
    filtered_flags: list[str],
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
):
    for flag_name, enabled in added_flags.items():
        _create_feature_flag(feature_flag_session, flag_name)
        _ = db_feature_flag_router.set_feature_is_enabled(flag_name, enabled)

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
            f"{_FEATURE_FLAG_TEST_NAME}2": False,
            f"{_FEATURE_FLAG_TEST_NAME}3": True,
            f"{_FEATURE_FLAG_TEST_NAME}4": False,
            f"{_FEATURE_FLAG_TEST_NAME}5": True,
            f"{_FEATURE_FLAG_TEST_NAME}6": False,
        },
    ],
)
def test__get_feature_flags__caches_all_existing_flags_when_queried(
    added_flags: dict[str, bool],
    db_feature_flag_router: DBFeatureFlagRouter[FeatureFlag],
    feature_flag_session: Session,
    mocker: MockerFixture,
):
    for flag_name, enabled in added_flags.items():
        _create_feature_flag(feature_flag_session, flag_name)
        _ = db_feature_flag_router.set_feature_is_enabled(flag_name, enabled)

    cache_mock = mocker.patch(
        "Ligare.platform.feature_flag.caching_feature_flag_router.CachingFeatureFlagRouter.set_feature_is_enabled",
        autospec=True,
    )

    _ = db_feature_flag_router.get_feature_flags()

    call_args_dict: dict[str, bool] = {
        call.args[1]: call.args[2] for call in cache_mock.call_args_list
    }

    # CachingFeatureFlagRouter.set_feature_is_enabled should be called
    # once for every feature flag retrieved from the database
    assert cache_mock.call_count == len(added_flags)
    for flag_name, enabled in added_flags.items():
        assert call_args_dict[flag_name] == enabled
