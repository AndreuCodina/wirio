from enum import Enum, auto


class CallSiteResultCacheLocation(Enum):
    ROOT = auto()
    SCOPE = auto()
    DISPOSE = auto()
    NONE = auto()
