from enum import Enum, auto

global_requestor_id = 0

class CacheEventType(Enum):
    Load = auto()  
    Store = auto()  
    Replacement = auto()  
    GetS = auto()  
    GetM = auto()  
    PutM = auto()  
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
    is_request = True
    data_recvers = []

class Bus:
    queue = []
    queue_size = 1

class Cache:
    state = CacheState.I
    data = 0
    data_valid = False

    bus = None
    llc = None

    retry_send_event = None

    def process_req_event(self, event):
        if event.type == CacheEventType.Load:
            if self.state == CacheState.I:
                self.state = CacheState.ISD
                event = Event(
                    type=CacheEventType.GetS,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
                send_done = self.bus.send_req_event(event)
                if not send_done:
                    self.retry_send_event = event
                return (0, False)
            elif self.state == CacheState.ISD or self.state == CacheState.IMD:
                return (0, False)
            elif self.state == CacheState.S or self.state == CacheState.SMD or self.state == CacheState.M:
                return (self.data, True)

        elif event.type == CacheEventType.Store:
            if self.state == CacheState.I:
                self.state = CacheState.IMD
                event = Event(
                    type=CacheEventType.GetM,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
                send_done = self.bus.send_req_event(event)
                if not send_done:
                    self.retry_send_event = event
                return (0, False)
            elif self.state == CacheState.ISD or self.state == CacheState.IMD or self.state == CacheState.SMD:
                return (0, False)
            elif self.state == CacheState.S or self.state == CacheState.M:
                self.state = CacheState.SMD
                event = Event(
                    type=CacheEventType.GetM,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
                send_done = self.bus.send_req_event(event)
                if not send_done:
                    self.retry_send_event = event
                return (0, False)
            elif self.state == CacheState.M:
                self.data = event.data
                return (self.data, True)
        
        elif event.type == CacheEventType.Replacement:
            if self.state == CacheState.I:
                print("ERROR: should not happen: replacement in I state")
                raise Exception
            elif self.state == CacheState.ISD or self.state == CacheState.IMD or self.state == CacheState.SMD:
                return (0, False)
            elif self.state == CacheState.S:
                self.state = CacheState.I
                return (0, True)
            elif self.state == CacheState.M:
                event = Event(
                    type=CacheEventType.GetM,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True,
                    data_recvers=[llc]
                )
                send_done = self.bus.send_req_event(event)
                if not send_done:
                    self.retry_send_event = event
                    self.state = CacheState.M
                    return (0, False)
                else:
                    self.state = CacheState.I
                    return (0, True)

        elif event.type == CacheEventType.GetS and event.requestor == self:
            if self.state == CacheState.ISD:
                return (0, True)
            else:
                print("ERROR: should not happen: replacement in I state")
                raise Exception
        elif event.type == CacheEventType.GetM and event.requestor == self:
            if self.state == CacheState.IMD:
                return (0, True)
            elif self.state == CacheState.SMD:
                return (0, True)
            else:
                print("ERROR: should not happen: replacement in I state")
                raise Exception
        elif event.type == CacheEventType.PutM and event.requestor == self:
            if self.state == CacheState.I:
                self.data = event.data
                return (0, True)
            else:
                print("ERROR: should not happen: replacement in I state")
                raise Exception
                

class LLC:
    c = 0

class Core:
    load_data = 0
    store_data = 0
    
    retry_send_event = None
    # wait_load_resp = False
    # wait_store_resp = False

    cache = None


class DataDriver:
    data = 0
    data_valid = False

    cores = []

    def add_objects(self, objects):
        for cache in objects:
            core = Core()
            core.data = self.data
            core.data_valid = False
            core.cache = cache
            self.data_objects.append(cache)

    def tick_run(self):
        for core in self.cores:
            if not core.retry_send_event:
                event = self.make_random_core_event(core.cache, core)
                (resp_data, send_done) = object.process_req_event(event)
                if not send_done:
                    core.retry_send_event = event
                else:
                    if event.type == CacheEventType.Load:
                        core.load_data = resp_data
                        if  (not self.data_valid) or core.load_data != self.data:
                            print("ERROR: Data mismatch")
                            raise Exception

                    elif event.type == CacheEventType.Store:
                        self.data = core.store_data
                        self.data_valid = True
                    
            else:
                send_done = object.process_req_event(core.retry_send_event)
                if send_done:
                    core.retry_send_event = None

                    if event.type == CacheEventType.Load:
                        core.load_data = resp_data
                        if  (not self.data_valid) or core.load_data != self.data:
                            print("ERROR: Data mismatch")

                    elif event.type == CacheEventType.Store:
                        self.data = core.store_data
                        self.data_valid = True

    def make_random_core_event(self, cache, core):
        import random  
          
        random_integer = random.randrange(0, 3)
        if random_integer == 0:
            return Event(
                type=CacheEventType.Load,
                requestor=core,
                data=0,
                data_valid=False,
                is_request=True
            )
        elif random_integer == 1:
            core.store_data = self.data + 1
            return Event(
                type=CacheEventType.Store,
                requestor=core,
                data=core.store_data,
                data_valid=True,
                is_request=True
            )
        elif random_integer == 2:
            if cache.state != CacheState.I:
                return Event(
                    type=CacheEventType.Replacement,
                    requestor=None,
                    data=0,
                    data_valid=False,
                    is_request=True
                )


class TickDriver:
    tick = 0
    max_tick = 1024

    tick_objects = []

    def add_objects(self, objects):
        for object in objects:
            self.tick_objects.append(object)

    def run(self):
        while self.tick < self.max_tick:
            for object in self.tick_objects:
                object.tick_run()
            tick_driver.tick += 1




cache0 = Cache()
cache1 = Cache()
cache2 = Cache()
llc = LLC()
bus = Bus()

bus.connect([cache0, cache1, cache2, llc])

data_driver = DataDriver()
tick_driver = TickDriver()

data_driver.add_objects([cache0, cache1, cache2])
tick_driver.add_objects([data_driver, cache0, cache1, cache2, llc, bus])

tick_driver.max_tick = 2048
tick_driver.run()
