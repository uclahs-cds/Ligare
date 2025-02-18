from injector import inject
from Ligare.programming.application import ApplicationBase, ApplicationBuilder
from Ligare.programming.config import Config
from typing_extensions import override


class Application(ApplicationBase):
    @inject
    @override
    def run(self, config: "AppConfig"):
        print(config.message)
        input("\nPress anything to exit. ")


builder = ApplicationBuilder(Application)


class AppConfig(Config):
    message: str


builder.use_configuration(
    lambda config_builder: config_builder \
        .with_config_type(AppConfig) \
        .with_config_filename("app/config.toml")
)

application = builder.build()

if __name__ == "__main__":
    application.run()
