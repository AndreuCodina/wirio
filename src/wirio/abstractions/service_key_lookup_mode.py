from enum import Enum, auto


class ServiceKeyLookupMode(Enum):
    INHERIT_KEY = auto()
    NULL_KEY = auto()
    EXPLICIT_KEY = auto()
