"""
Server blueprint
Non-API specific endpoints for application management
"""
import json
from logging import Logger

from BL_Python.programming.config import Config
from flask import Blueprint
from flask import Config as FlaskAppConfig
from flask import request
from injector import inject
from sqlalchemy.orm.session import Session

from database import Base, Person

server_blueprint = Blueprint("", __name__)


@inject
@server_blueprint.route("/healthcheck", methods=("GET",))
def healthcheck(config: Config, flask_config: FlaskAppConfig, log: Logger):
    return "healthcheck: flask app is running"


@inject
@server_blueprint.route("/get_person/<name>", methods=("GET",))
def get_person(name: str, session: Session, log: Logger):
    people = session.query(Person).filter(Person.name == name).all()
    return [person.to_dict() for person in people]


@inject
@server_blueprint.route("/add_person/<name>", methods=("GET",))
def add_person(name: str, session: Session, log: Logger):
    person = Person(name=name)
    session.add(person)
    session.commit()
    return person.to_dict()


@inject
@server_blueprint.route("/create_db", methods=("GET",))
def create_db(session: Session, log: Logger):
    log.info("Creating database")
    Base.metadata.create_all(session.bind.engine)
    return "done"
