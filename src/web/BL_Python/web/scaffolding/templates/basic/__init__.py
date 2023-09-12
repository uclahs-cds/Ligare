from BL_Python.database.config import DatabaseConfig
from BL_Python.database.dependency_injection import ScopedSessionModule
from BL_Python.web.application import create_app

# fmt: off
app = create_app(
    application_configs=[DatabaseConfig],
    application_modules=[ScopedSessionModule()]
)
# fmt: on
