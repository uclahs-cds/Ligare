import pytest
from Ligare.programming.config import AbstractConfig, ConfigBuilder, load_config
from Ligare.programming.config.exceptions import (
    ConfigBuilderStateError,
    NotEndsWithConfigError,
)
from pydantic import BaseModel
from pytest_mock import MockerFixture
from typing_extensions import override


class FooConfig(BaseModel):
    value: str
    other_value: bool = False


class BarConfig(BaseModel):
    value: str


class BazConfig(BaseModel, AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()

    value: str


class TestConfig(BaseModel, AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()

    foo: FooConfig = FooConfig(value="xyz")
    bar: BarConfig | None = None


class InvalidConfigClass(BaseModel, AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()

    pass


def test__Config__load_config__reads_toml_file(mocker: MockerFixture):
    fake_config_dict = {}
    toml_mock = mocker.patch("toml.load", return_value=fake_config_dict)
    _ = load_config(TestConfig, "foo.toml")
    assert toml_mock.called


def test__Config__load_config__initializes_section_config_value(mocker: MockerFixture):
    fake_config_dict = {"foo": {"value": "abc123"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config(TestConfig, "foo.toml")
    assert config.foo.value == "abc123"


def test__Config__load_config__initializes_section_config(mocker: MockerFixture):
    fake_config_dict = {"bar": {"value": "abc123"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config(TestConfig, "foo.toml")
    assert config.bar is not None
    assert config.bar.value == "abc123"


def test__Config__load_config__applies_overrides(mocker: MockerFixture):
    fake_config_dict = {"foo": {"value": "abc123"}}
    override_config_dict = {"foo": {"value": "XYZ"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config(TestConfig, "foo.toml", override_config_dict)
    assert config.foo.value == override_config_dict["foo"]["value"]


def test__ConfigBuilder__build__raises_error_when_no_root_config_and_no_section_configs_specified():
    config_builder = ConfigBuilder[TestConfig]()
    with pytest.raises(ConfigBuilderStateError):
        _ = config_builder.build()


def test__ConfigBuilder__build__raises_error_when_section_class_name_is_invalid():
    config_builder = ConfigBuilder[TestConfig]()
    _ = config_builder.with_configs([InvalidConfigClass])
    with pytest.raises(NotEndsWithConfigError):
        _ = config_builder.build()


def test__ConfigBuilder__build__uses_object_as_root_config_when_no_root_config_specified():
    config_builder = ConfigBuilder[TestConfig]()
    _ = config_builder.with_configs([BazConfig])
    config_type = config_builder.build()
    assert TestConfig not in config_type.__mro__
    assert BazConfig not in config_type.__mro__
    assert hasattr(config_type, "baz")
    assert hasattr(config_type(), "baz")


def test__ConfigBuilder__build__uses_root_config_when_no_section_configs_specified():
    config_builder = ConfigBuilder[TestConfig]()
    _ = config_builder.with_root_config(TestConfig)
    config_type = config_builder.build()
    assert config_type is TestConfig
    assert isinstance(config_type(), TestConfig)


def test__ConfigBuilder__build__creates_config_type_when_multiple_configs_specified(
    mocker: MockerFixture,
):
    fake_config_dict = {"baz": {"value": "ABC"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    config_builder = ConfigBuilder[TestConfig]()
    _ = config_builder.with_root_config(TestConfig)
    _ = config_builder.with_configs([BazConfig])
    config_type = config_builder.build()
    config = load_config(config_type, "foo.toml")

    assert TestConfig in config_type.__mro__
    assert hasattr(config, "baz")


def test__ConfigBuilder__build__sets_dynamic_config_values_when_multiple_configs_specified(
    mocker: MockerFixture,
):
    fake_config_dict = {"baz": {"value": "ABC"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    config_builder = ConfigBuilder[TestConfig]()
    _ = config_builder.with_root_config(TestConfig)
    _ = config_builder.with_configs([BazConfig])
    config_type = config_builder.build()
    config = load_config(config_type, "foo.toml")

    assert hasattr(config, "baz")
    assert getattr(config, "baz")
    assert getattr(getattr(config, "baz"), "value")
    assert getattr(getattr(config, "baz"), "value") == "ABC"
