import argparse
from logging import Logger
from pprint import pprint

from BL_Python.database.config import DatabaseConfig
from BL_Python.database.dependency_injection import ScopedSessionModule
from BL_Python.programming.config import Config, load_config
from BL_Python.programming.dependency_injection import ConfigModule
from BL_Python.programming.patterns.dependency_injection import LoggerModule
from injector import Injector, inject
from sqlalchemy.orm.session import Session

from database import Base, Person


@inject
def get_person(name: str, session: Session, log: Logger):
    log.info(f"Getting person {name}")
    people = session.query(Person).filter(Person.name == name).all()
    return [person.to_dict() for person in people]


@inject
def add_person(name: str, session: Session, log: Logger):
    log.info(f"Adding person {name}")
    person = Person(name=name)
    session.add(person)
    session.commit()
    return person.to_dict()


@inject
def create_db(config: Config, session: Session, log: Logger):
    log.info("Creating database")
    Base.metadata.create_all(session.bind.engine)
    return "done"


if __name__ == "__main__":
    # fmt: off
    config = load_config("database-config.toml", config_type=DatabaseConfig)
    di_container = Injector([
       LoggerModule(),#log_to_stdout=True),
       ConfigModule(config),
       ScopedSessionModule()
    ])
    call = di_container.call_with_injection
    # fmt: on

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-c", "--create", action="store_true", help="Create the database"
    )
    arg_parser.add_argument("-a", "--add", help="Add a person")
    arg_parser.add_argument("-g", "--get", help="Get a person")
    args = arg_parser.parse_args()

    if args.create:
        pprint(call(create_db))

    if args.add:
        pprint(call(add_person, args.add))

    if args.get:
        pprint(call(get_person, args.get))
