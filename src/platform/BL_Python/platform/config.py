from BL_Python.programming.config import AbstractConfig
from pydantic import BaseModel


class IdentityRoleConfig(BaseModel):
    default: str


class IdentityConfig(BaseModel, AbstractConfig):
    role: IdentityRoleConfig | None = None


class Config(BaseModel, AbstractConfig):
    identity: IdentityConfig
