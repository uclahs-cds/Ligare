from BL_Python.database.config import DatabaseConnectArgsConfig

from .postgresql import PostgreSQLScopedSession
from .sqlite import SQLiteScopedSession


class DatabaseEngine:
    @staticmethod
    def get_session_from_connection_string(
        connection_string: str,
        echo: bool = False,
        execution_options: dict[str, str] | None = None,
        connect_args: DatabaseConnectArgsConfig | None = None,
    ):
        if connection_string.startswith("sqlite://"):
            return SQLiteScopedSession.create(
                connection_string,
                echo,
                execution_options=execution_options,
                connect_args=connect_args,
            )

        if connection_string.startswith("postgresql://"):
            return PostgreSQLScopedSession.create(
                connection_string,
                echo,
                execution_options=execution_options,
                connect_args=connect_args,
            )

        raise ValueError(
            f'Unexpected connection string used for database engine. Received "{connection_string}".'
        )
