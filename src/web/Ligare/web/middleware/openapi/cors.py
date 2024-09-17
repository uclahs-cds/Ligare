from connexion import FlaskApp
from connexion.middleware import MiddlewarePosition
from injector import Module, inject
from Ligare.web.config import Config
from starlette.middleware.cors import CORSMiddleware


class CORSMiddlewareModule(Module):
    @inject
    def register_middleware(self, app: FlaskApp, config: Config):
        cors_config = config.web.security.cors

        app.add_middleware(
            CORSMiddleware,
            position=MiddlewarePosition.BEFORE_EXCEPTION,
            allow_origins=cors_config.origins or [],
            allow_credentials=cors_config.allow_credentials,
            allow_methods=cors_config.allow_methods,
            allow_headers=cors_config.allow_headers,
        )
