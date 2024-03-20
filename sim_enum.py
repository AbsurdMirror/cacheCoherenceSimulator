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

# NON-ATOMIC REQUESTS, ATOMIC TRANSACTIONS Enums
class NARAT_MSI_EventCmd(Enum):
    Load = 0
    Store = auto()  
    Replacement = auto()  
    GetS = auto()  
    GetM = auto()  
    PutM = auto()  
    Data = auto()  
    NoData = auto()

class NARAT_MSI_CacheEventCmd(Enum):
    Load = 0
    Store = auto()  
    Replacement = auto()  
    OwnGetS = auto()  
    OwnGetM = auto()  
    OwnPutM = auto()  
    OtherGetS = auto()  
    OtherGetM = auto()  
    OtherPutM = auto()  
    Data = auto()  

class NARAT_MSI_LLCEventCmd(Enum):
    GetS = 0
    GetM = auto()  
    PutM = auto()  
    Data = auto()  
    NoData = auto()

class NARAT_MSI_CacheState(Enum):
    I = 0
    ISAD = auto()
    ISD = auto()
    IMAD = auto()
    IMD = auto()
    S = auto()
    SMAD = auto()
    SMD = auto()
    M = auto()
    MIA = auto()
    IIA = auto()

class NARAT_MSI_LLCState(Enum):
    IorS = 0
    IorSD = auto()
    M = auto()
    MD = auto()

class NARAT_BusState(Enum):
    WaitReq   = 0
    TransReq  = auto()
    WaitData  = auto()
    TransData = auto()
