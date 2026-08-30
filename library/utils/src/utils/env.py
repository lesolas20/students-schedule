from os import getenv


def getenv_str(
    key: str,
    default: str | None = None,
    *,
    required: bool = False,
) -> str | None:
    """Get an environment variable representing a `str`, return `None`
    if it does not exist.
    The optional argument `default` can specify a different value
    to return on failure.
    If `required` is set to `True`, raise `ValueError` on failure
    instead of returning `default`.
    """
    value = getenv(key)

    if value is None:
        if not required:
            return default

        msg = f"could not get value of {key!r} which is required"
        raise ValueError(msg) from None

    return value


def getenv_int(
    key: str,
    default: int | None = None,
    *,
    required: bool = False,
) -> int | None:
    """Get an environment variable representing an `int`, return None
    if it does not exist or is not a valid `int`.
    The optional argument `default` can specify a different value
    to return on failure.
    If `required` is set to `True`, raise `ValueError` on failure
    instead of returning `default`.
    """
    value = getenv(key)

    if value is None:
        if not required:
            return default

        msg = f"could not get value of {key!r} which is required"
        raise ValueError(msg) from None

    try:
        value_int = int(value)
    except ValueError:
        if not required:
            return default

        msg = f"could not convert value of {key!r} to int: {value!r}"
        raise ValueError(msg) from None

    return value_int
