from typing import Any

from Ligare.web.testing.create_app import CreateOpenAPIApp


class TestSSO(CreateOpenAPIApp):
    def test__sso__something(self, openapi_client: Any):
        pass
