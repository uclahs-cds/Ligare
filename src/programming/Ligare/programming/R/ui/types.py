from typing import Literal, TypedDict

from typing_extensions import NotRequired


class RMethodParameterBase(TypedDict):
    name: str
    type: Literal["text", "number", "checkbox", "hidden", "nested"]
    default: NotRequired[str | int | float | bool | None]


class RMethodParameterNumberExtra(TypedDict, total=False):
    step: NotRequired[int | float]
    min: NotRequired[int | float]
    max: NotRequired[int | float]


class RMethodParameterNumber(RMethodParameterBase, total=False):
    # this override exists so pyright can determine the correct
    # dictionary types based on the value of `type`.
    type: Literal["number"]  # pyright: ignore[reportIncompatibleVariableOverride]
    extra: NotRequired[RMethodParameterNumberExtra]


class RMethodParameterText(RMethodParameterBase, total=False):
    type: Literal["text"]  # pyright: ignore[reportIncompatibleVariableOverride]


class RMethodParameterCheckbox(RMethodParameterBase, total=False):
    type: Literal["checkbox"]  # pyright: ignore[reportIncompatibleVariableOverride]


class RMethodParameterNested(TypedDict):
    type: Literal["nested"]
    label: str
    inputs: list["RMethodParameter"]


RMethodParameter = (
    RMethodParameterNumber
    | RMethodParameterText
    | RMethodParameterCheckbox
    | RMethodParameterNested
)


RMethodsParameters = dict[str, list[RMethodParameter]]

RMethodsParametersDocs = dict[str, dict[str, str]]

RMethodsMetadata = TypedDict(
    "RMethodsMetadata", {"GitHub": str, "CRAN": str, "RDRR": str}
)
