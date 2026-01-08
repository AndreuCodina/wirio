from enum import Enum, auto


class CallSiteKind(Enum):
    SYNC_FACTORY = auto()
    ASYNC_FACTORY = auto()
    CONSTRUCTOR = auto()
    CONSTANT = auto()
    SERVICE_PROVIDER = auto()
