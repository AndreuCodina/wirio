from enum import Enum, auto


class CallSiteKind(Enum):
    SYNC_FACTORY = auto()
    ASYNC_FACTORY = auto()
    CONSTRUCTOR = auto()
    SERVICE_PROVIDER = auto()
