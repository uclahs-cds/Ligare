from injector import inject
from Ligare.programming.application import ApplicationBase, ApplicationBuilder
from Ligare.programming.config import AbstractConfig
from pydantic import BaseModel
from typing_extensions import override


class AppConfig(BaseModel, AbstractConfig):
    foo: str

    @override
    def post_load(self):
        super().post_load()


class Application(ApplicationBase):
    @inject
    @override
    def run(self, config: AppConfig):
        print("config says: ")
        print(config)
        _ = input("Press anything to exit. ")


builder = ApplicationBuilder(Application)

_ = builder.use_configuration(
    lambda config_builder: config_builder.with_config_type(
        AppConfig
    ).with_config_filename("app/config.toml")
)
result = builder.build()
result.run()
