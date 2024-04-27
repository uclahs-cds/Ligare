from BL_Python.identity.config import SAML2Config, SSOConfig
from BL_Python.identity.SAML2 import SAML2Client
from BL_Python.programming.collections.dict import AnyDict

# from flask import url_for
from injector import Binder, CallableProvider, Module, inject, singleton
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from typing_extensions import override


class SSOModule(Module):
    def __init__(self):  # , metadata: str, settings: AnyDict) -> None:
        """
        metadata can be XML or a URL
        """
        super().__init__()

    #        self._metadata = metadata
    #        self._settings = settings

    @override
    def configure(self, binder: Binder) -> None:
        # Making this a callback allows to defer instantiation of the SAML2 client
        # until after the Flask application has started, which is needed to generate
        # the ACS URLs in the SAML2 config.
        binder.bind(
            SAML2Client, to=CallableProvider(self._get_saml2_client), scope=singleton
        )

    @inject
    def _get_saml2_client(self, config: SSOConfig):
        """
        Get an instance of the SAML2 manager with ACS URLs.
        This method depends on a currently running Flask application for the use of `url_for`.
        """

        settings = config.settings
        if not isinstance(settings, SAML2Config):
            # FIXME need to bring this closer in line with how the database config works
            raise Exception(
                "Wrong config type for SAML2 settings. This is a program error, not a configuration error."
            )

        # FIXME application assumes this is not None, but it technically can be ... and then it will crash
        metadata: str = settings.metadata

        # acs_url = url_for("sso.idp_initiated", idp_name="okta", _external=True)
        # https_acs_url = url_for(
        #    "sso.idp_initiated", idp_name="okta", _external=True, _scheme="https"
        # )
        client_settings: AnyDict = {
            "entityid": settings.acs_url,
            "service": {
                "sp": {
                    "endpoints": {
                        "assertion_consumer_service": [
                            (settings.acs_url, BINDING_HTTP_REDIRECT),
                            (settings.acs_url, BINDING_HTTP_POST),
                            (settings.https_acs_url, BINDING_HTTP_REDIRECT),
                            (settings.https_acs_url, BINDING_HTTP_POST),
                        ]
                    }
                }
            },
        }

        return SAML2Client(metadata, client_settings)
