import hashlib
from typing import TYPE_CHECKING, Any, Callable, Dict

from flask.json.tag import TaggedJSONSerializer
from flask.sessions import SessionMixin
from itsdangerous import URLSafeTimedSerializer

if TYPE_CHECKING:
    from _typeshed import ReadableBuffer  # pragma: no cover

_EMPTY_SECRET_KEY_MESSAGE = (
    "It is insecure to use an empty `secret_key`. Refusing to continue."
)


def _get_serializer(
    secret_key: str,
    salt: str = "cookie-session",
    key_derivation: str = "hmac",
    digest_method: Callable[
        ["ReadableBuffer"], "hashlib._Hash"  # pyright: ignore[reportPrivateUsage]
    ] = hashlib.sha1,
):
    serializer = TaggedJSONSerializer()
    return URLSafeTimedSerializer(
        secret_key,
        salt=salt,
        serializer=serializer,
        signer_kwargs={
            "key_derivation": key_derivation,
            "digest_method": digest_method,
        },
    )


def decrypt_flask_cookie(secret_key: str, cookie_str: str) -> Dict[str, Any]:
    """
    Decrypt a Flask session cookie.
    https://gist.github.com/babldev/502364a3f7c9bafaa6db
    """
    if not secret_key:
        raise Exception(_EMPTY_SECRET_KEY_MESSAGE)

    serializer = _get_serializer(secret_key)
    data: Any = serializer.loads(cookie_str)

    if type(data) is not dict:
        raise AssertionError(
            f"Deserialized session data is not a dictionary. It is a `{type(data)}`."
        )

    return data  # pyright: ignore[reportUnknownVariableType]


def encrypt_flask_cookie(secret_key: str, data: Dict[str, Any] | SessionMixin) -> str:
    """
    Encrypt a dictionary into a Flask session cookie.
    """
    if not secret_key:
        raise Exception(_EMPTY_SECRET_KEY_MESSAGE)

    serializer = _get_serializer(secret_key)
    cookie_str = serializer.dumps(data)

    if type(cookie_str) is not str:
        raise AssertionError(
            f"Serialized cookie data is not a str. It is a `{type(cookie_str)}`."
        )

    return cookie_str
