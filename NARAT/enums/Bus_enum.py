from enum import Enum, auto

class NARAT_BusState(Enum):
    WaitReq   = 0
    TransReq  = auto()
    WaitData  = auto()
    TransData = auto()
