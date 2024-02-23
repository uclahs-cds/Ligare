from typing import Any, Callable, Union

from BL_Python.database.config import DatabaseConnectArgsConfig
from sqlalchemy import create_engine
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import sessionmaker


class PostgreSQLScopedSession(ScopedSession):
    @staticmethod
    def create(
        connection_string: str,
        echo: bool = False,
        execution_options: dict[str, Any] | None = None,
        connect_args: DatabaseConnectArgsConfig | None = None,
    ):
        engine = create_engine(
            connection_string,
            echo=echo,
            execution_options=execution_options or {},
            connect_args=connect_args.model_dump() if connect_args is not None else {},
        )

        return PostgreSQLScopedSession(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )

    def __init__(
        self,
        session_factory: Union[Callable[..., Any], "sessionmaker[Any]"],
        scopefunc: Any = None,
    ) -> None:
        super().__init__(session_factory, scopefunc)
