from .sqlite import SQLiteScopedSession


class DatabaseEngine:
    @staticmethod
    def get_session_from_connection_string(connection_string: str, echo: bool = False):
        if connection_string.startswith("sqlite://"):
            return SQLiteScopedSession.create(connection_string, echo)

        raise ValueError(
            f'Unexpected connection string used for database engine. Received "{connection_string}".'
        )
