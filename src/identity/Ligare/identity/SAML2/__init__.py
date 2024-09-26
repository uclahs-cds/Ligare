from functools import lru_cache
from pickle import dumps, loads
from typing import Optional, cast
from urllib.parse import urlparse

import requests
from Ligare.programming.collections import merge
from Ligare.programming.collections.dict import AnyDict
from requests import Response
from saml2 import BINDING_HTTP_POST
from saml2.client import Saml2Client as PySaml2Client
from saml2.config import Config as PySaml2Config

_SAML2_REQUESTS_TIMEOUT = 10


class SAML2Client:
    """
    Overrides some default behavior of saml2.client.Saml2Client
    """

    _metadata_url: Optional[str] = None
    _metadata: Optional[str] = None

    def __init__(self, metadata: str, settings: AnyDict) -> None:
        """
        metadata can be XML or a URL
        """
        parsed_url = urlparse(metadata)
        if parsed_url.scheme == "" and parsed_url.netloc == "":
            self._metadata = metadata
        else:
            self._metadata_url = metadata
        self._settings = settings

        super().__init__()

    @lru_cache
    def _get_saml_client(self, serialized_settings: bytes):
        override_settings = loads(serialized_settings)

        if not self._metadata and self._metadata_url:
            rv: Response = cast(
                Response,
                requests.get(self._metadata_url, timeout=_SAML2_REQUESTS_TIMEOUT),
            )  # pyright: ignore[reportUnnecessaryCast]
            self._metadata = rv.text

        if not self._metadata:
            raise AssertionError("Metadata is not set. Cannot initialize SAML2 client.")

        config = self._get_config(self._metadata, override_settings)

        sp_config = PySaml2Config()
        _ = sp_config.load(config)
        sp_config.allow_unknown_attributes = True

        saml_client = PySaml2Client(config=sp_config)
        return saml_client

    def get_saml_client(self, override_settings: AnyDict | None = None):
        """
        Get an instance of saml2.client.Saml2Client and set the metadata from the IDP.
        Also set any default and overridden settings.
        """
        if not override_settings:
            override_settings = {}

        settings = merge(self._settings, override_settings)
        serialized_settings = dumps(settings)

        saml_client = self._get_saml_client(serialized_settings)
        return saml_client

    def _get_config(self, metadata: str, override_settings: AnyDict | None = None):
        if not override_settings:
            override_settings = {}

        default_settings = {
            "metadata": {"inline": [metadata]},
            "service": {
                "sp": {
                    # Don't verify that the incoming requests originate from us via
                    # the built-in cache for authn request ids in pysaml2
                    "allow_unsolicited": True,
                    # Don't sign authn requests, since signed requests only make
                    # sense in a situation where you control both the SP and IdP
                    "authn_requests_signed": False,
                    "logout_requests_signed": True,
                    "want_assertions_signed": True,
                    "want_response_signed": False,
                },
            },
        }

        return merge(default_settings, override_settings)

    def prepare_user_authentication(self, relay_state: Optional[str] = None):
        """
        Prepares a SAML2 IDP request and returns the IDP URL.
        """
        saml_client = self.get_saml_client()

        _, info = (
            saml_client.prepare_for_authenticate()
            if relay_state is None
            else saml_client.prepare_for_authenticate(relay_state=relay_state)
        )

        redirect_url: Optional[str] = None
        # Select the IdP URL to send the AuthN request to
        for key, value in info["headers"]:
            if key == "Location":
                redirect_url = value

        if redirect_url is None:
            raise AssertionError("`redirect_url` is `None`.")

        return redirect_url

    def handle_user_login(self, saml_response: str):
        """
        Parse a SAML2 request from the IDP and call the `login_callback` with the username and SAML2 AVA.
        """
        saml_client = self.get_saml_client()
        authn_response = saml_client.parse_authn_request_response(
            saml_response, BINDING_HTTP_POST
        )
        if authn_response is None:
            raise AssertionError("`authn_response` is `None`.")

        _ = authn_response.get_identity()
        user_info = authn_response.get_subject()

        if user_info is None:
            raise AssertionError("`user_info` is `None`.")

        username = user_info.text

        if username is None:
            raise AssertionError("`username` is `None`.")

        return username, authn_response
