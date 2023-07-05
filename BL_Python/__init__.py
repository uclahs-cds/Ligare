__version__: str = ""

try:
    import importlib.metadata

    __version__ = importlib.metadata.version(__package__ or __name__)
except:
    from pip._vendor import tomli

    with open("../pyproject.toml") as f:
        t = tomli.loads(f.read())
        __version__ = t["project"]["version"]
