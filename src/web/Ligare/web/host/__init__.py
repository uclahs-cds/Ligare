from Ligare.programming.collections.dict import merge
from uvicorn.workers import UvicornWorker


class LifespanUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = merge(UvicornWorker.CONFIG_KWARGS, {"lifespan": "on"})


class ProxiedUvicornWorker(LifespanUvicornWorker):
    CONFIG_KWARGS = merge(
        UvicornWorker.CONFIG_KWARGS,
        {"proxy_headers": True, "forwarded_allow_ips": "*"},
    )
