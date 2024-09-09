from flask import url_for

# from flask import url_for
from injector import Binder, CallableProvider, Module, inject, singleton
from Ligare.identity.config import SAML2Config, SSOConfig
from Ligare.identity.SAML2 import SAML2Client
from Ligare.programming.collections.dict import AnyDict
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from typing_extensions import override


class SSOModule(Module):
    pass


class SAML2Module(SSOModule):
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

        metadata: str = settings.metadata

        acs_url = (
            settings.acs_url
            if settings.acs_url is not None
            else url_for("sso.idp_initiated", idp_name="okta", _external=True)
        )
        https_acs_url = (
            settings.https_acs_url
            if settings.https_acs_url is not None
            else url_for(
                "sso.idp_initiated", idp_name="okta", _external=True, _scheme="https"
            )
        )
        client_settings: AnyDict = {
            "entityid": acs_url,
            "service": {
                "sp": {
                    "endpoints": {
                        "assertion_consumer_service": [
                            (acs_url, BINDING_HTTP_REDIRECT),
                            (acs_url, BINDING_HTTP_POST),
                            (https_acs_url, BINDING_HTTP_REDIRECT),
                            (https_acs_url, BINDING_HTTP_POST),
                        ]
                    }
                }
            },
        }

        return SAML2Client(metadata, client_settings)
