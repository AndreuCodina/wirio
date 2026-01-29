from enum import Enum, auto


class ServiceLifetime(Enum):
    SINGLETON = auto()
    SCOPED = auto()
    TRANSIENT = auto()
