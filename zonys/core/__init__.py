# pylint: disable=redefined-builtin
def open() -> "_Handle":
    return _Handle()


class _Handle:
    pass
