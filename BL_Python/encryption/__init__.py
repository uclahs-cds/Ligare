# import hashlib
# from typing import TYPE_CHECKING, Any, Callable, Dict, cast
#
# from flask.json.tag import TaggedJSONSerializer
# from itsdangerous import URLSafeTimedSerializer
#
# if TYPE_CHECKING:
#    from _typeshed import ReadableBuffer
#
#
# def _get_serializer(
#    secret_key: str,
#    salt: str = "cookie-session",
#    key_derivation: str = "hmac",
#    digest_method: Callable[
#        ["ReadableBuffer"], "hashlib._Hash"  # pyright: ignore[reportPrivateUsage]
#    ] = hashlib.sha1,
# ):
#    serializer = TaggedJSONSerializer()
#    return URLSafeTimedSerializer(
#        secret_key,
#        salt=salt,
#        serializer=serializer,
#        signer_kwargs={
#            "key_derivation": key_derivation,
#            "digest_method": digest_method,
#        },
#    )
#
#
# def decrypt_flask_cookie(secret_key: str, cookie_str: str) -> Dict[str, Any]:
#    """
#    Decrypt a Flask session cookie.
#    https://gist.github.com/babldev/502364a3f7c9bafaa6db
#    """
#    serializer = _get_serializer(secret_key)
#    data: Any = serializer.loads(cookie_str)
#    assert type(data) is dict
#    return data  # pyright: ignore[reportUnknownVariableType]
#
#
# def encrypt_flask_cookie(secret_key: str, data: Dict[str, Any]) -> str:
#    """
#    Encrypt a dictionary into a Flask session cookie.
#    """
#    serializer = _get_serializer(secret_key)
#    cookie_str: str | bytes = cast(str | bytes, serializer.dumps(data))
#    assert type(cookie_str) is str
#    return cookie_str
#
