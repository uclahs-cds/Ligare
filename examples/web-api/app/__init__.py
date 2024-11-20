from connexion import FlaskApp
from Ligare.web.application import ApplicationBuilder

application_builder = ApplicationBuilder[FlaskApp]()

application_builder.use_configuration(
    lambda config_builder: config_builder.with_config_filename("app/config.toml")
)

result = application_builder.build()

result.run()