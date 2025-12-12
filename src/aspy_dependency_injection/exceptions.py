class ObjectDisposedError(Exception):
    """The exception that is thrown when an operation is performed on a disposed object."""

    def __init__(self, object_name: object | None) -> None:
        super().__init__(object_name)
