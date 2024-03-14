from enum import Enum, auto

global_requestor_id = 0

class CacheEventType(Enum):
    Load = auto()  
    Store = auto()  
    Replacement = auto()  
    OwnGetS = auto()  
    OwnGetM = auto()  
    OwnPutM = auto()  
    Data = auto()  
    OtherGetS = auto()  
    OtherGetM = auto()  
    OtherPutM = auto()  

class CacheState(Enum):
    I = auto()
    ISD = auto()
    IMD = auto()
    S = auto()
    SMD = auto()
    M = auto()

class LLCEventType(Enum):
    GetS = auto()  
    GetM = auto()  
    PutM = auto()  
    DataFromOwner = auto()  

class LLCState(Enum):
    IorS = auto()
    IorSD = auto()
    M = auto()

class Event:
    type = 0
    requestor = 0
    data = 0
    data_valid = False

class Bus:
    queue = []
    queue_size = 1

class Cache:
    state = 0
    data = 0
    data_valid = False

    bus = None

    def processEvent(event):
        if event == "bus":
            if Cache.data_valid:
                Cache.data_valid = False
                Cache.state = 0
                Bus.a = Cache.data
            else:
                Cache.data = Bus.a
                Cache.data_valid = True
                Cache.state = 1
        elif event == "tick":
            if Cache.state == 0:
                Cache.state = 1

class LLC:
    c = 0

class DataDriver:
    data = 0

class TickDriver:
    tick = 0
    max_tick = 1024

cache0 = Cache()
cache1 = Cache()
cache2 = Cache()
llc = LLC()
bus = Bus()
data_driver = DataDriver()
tick_driver = TickDriver()

bus.connect([cache0, cache1, cache2, llc])
data_driver.connect([cache0, cache1, cache2])
tick_driver.connect([data_driver, cache0, cache1, cache2, llc, bus])

tick_driver.max_tick = 2048
tick_driver.run()
