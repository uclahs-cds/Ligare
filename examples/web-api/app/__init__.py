from Ligare.web.application import ApplicationBuilder
from connexion import FlaskApp

application_builder = ApplicationBuilder(FlaskApp)

application_builder.use_configuration(
    lambda config_builder: \
        config_builder \
            .with_config_filename("app/config.toml")
)

application = application_builder.build()
application.run()