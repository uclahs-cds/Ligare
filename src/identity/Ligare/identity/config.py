from typing import Any

from Ligare.programming.config import AbstractConfig
from pydantic import BaseModel
from pydantic.config import ConfigDict
from typing_extensions import override


class SSOSettingsConfig(BaseModel):
    # allow any values, as this type is not
    # specifically the type to be used elsewhere
    model_config = ConfigDict(extra="allow")


class SAML2Config(SSOSettingsConfig):
    # ignore anything that DatabaseConnectArgsConfig
    # allowed to be set, except for any other attributes
    # of this class, which will end up assigned through
    # the instatiation of the __init__ override of DatabaseConfig
    model_config = ConfigDict(extra="ignore")

    metadata_url: str
    relay_state: str
    metadata: str
    acs_url: str | None = None
    https_acs_url: str | None = None


class SSOConfig(BaseModel, AbstractConfig):
    def __init__(self, **data: Any):
        super().__init__(**data)

        model_data = self.settings.model_dump() if self.settings else {}
        if self.protocol == "SAML2":
            self.settings = SAML2Config(**model_data)

    @override
    def post_load(self) -> None:
        return super().post_load()

    protocol: str = "SAML2"
    # the static field allows Pydantic to store
    # values from a dictionary
    settings: SSOSettingsConfig | None = None


class Config(BaseModel, AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()

    sso: SSOConfig
