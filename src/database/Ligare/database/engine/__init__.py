from Ligare.database.config import DatabaseConnectArgsConfig
from Ligare.database.types import MetaBase

from .postgresql import PostgreSQLScopedSession
from .sqlite import SQLiteScopedSession


class DatabaseEngine:
    _session_type_map = {
        "sqlite": SQLiteScopedSession,
        "postgresql": PostgreSQLScopedSession,
    }

    @staticmethod
    def get_session_from_connection_string(
        connection_string: str,
        echo: bool = False,
        execution_options: dict[str, str] | None = None,
        connect_args: DatabaseConnectArgsConfig | None = None,
        bases: list[MetaBase | type[MetaBase]] | None = None,
    ) -> SQLiteScopedSession | PostgreSQLScopedSession:
        schema_rindex = connection_string.find(":") if connection_string else -1
        if schema_rindex == -1 or schema_rindex == 0:
            raise ValueError(
                f"Invalid connection string used for database engine. URL is missing scheme. {connection_string=}"
            )

        engine_name = connection_string[:schema_rindex]
        session_type = DatabaseEngine._session_type_map.get(engine_name)

        if not engine_name or not session_type:
            raise ValueError(
                f"Unsupported connection string used for database engine. {connection_string=}"
            )

        scoped_session = session_type.create(
            connection_string,
            echo,
            execution_options=execution_options,
            connect_args=connect_args,
            bases=bases,
        )

        return scoped_session
