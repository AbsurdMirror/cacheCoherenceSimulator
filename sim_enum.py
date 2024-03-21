from enum import Enum, auto

class EventType(Enum):
    Request = 0
    Response = auto()  
    Data = auto()

class EventCmd(Enum):
    Load = 0
    Store = auto()  
    Replacement = auto()  
    GetS = auto()  
    GetM = auto()  
    PutM = auto()  
    Data = auto()  

class ARAT_MSI_EventCmd(Enum):
    Load = 0
    Store = auto()  
    Replacement = auto()  
    OwnGetS = auto()  
    OwnGetM = auto()  
    OwnPutM = auto()  
    Data = auto()  
    OtherGetS = auto()  
    OtherGetM = auto()  
    OtherPutM = auto()  

class ARAT_MSI_CacheState(Enum):
    I = 0
    ISD = auto()
    IMD = auto()
    S = auto()
    SMD = auto()
    M = auto()

class ARAT_MSI_LLCState(Enum):
    IorS = 0
    IorSD = auto()
    M = auto()
