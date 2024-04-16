from BL_Python.platform.identity.user_loader import Loader
from BL_Python.platform.identity.user_loader import T as TUserMixin
from flask import Config as Config
from injector import Binder, Module
from typing_extensions import override


class IdentityModule(Module):
    def __init__(
        self,
        loader: Loader[TUserMixin],
    ) -> None:
        super().__init__()
        self._loader = loader

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(Loader, to=self._loader)
