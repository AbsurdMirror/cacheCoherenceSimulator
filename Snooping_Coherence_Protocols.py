from enum import Enum, auto
import traceback
import random  

global_requestor_id = 0
global_device_id = 0

class EventType(Enum):
    Load = auto()  
    Store = auto()  
    Replacement = auto()  
    GetS = auto()  
    GetM = auto()  
    PutM = auto()  
    Data = auto()  

class CacheState(Enum):
    I = auto()
    ISD = auto()
    IMD = auto()
    S = auto()
    SMD = auto()
    M = auto()

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
    is_data_from_owner = False
    data_recvers = []

    def __init__(self, 
                 type,
                 requestor=None,
                 data=None,
                 data_valid=False,
                 is_request=True,
                 is_data_from_owner = False,
                 data_recvers=[],
                ):  
        self.type = type  
        self.requestor = requestor  
        self.data = data  
        self.data_valid = data_valid  
        self.is_request = is_request  
        self.data_recvers = data_recvers
        self.is_data_from_owner = is_data_from_owner

    def print(self):
        print_str = "Event: "
        if self.is_request:
            print_str += "(req "
        else:
            print_str += "(resp "
        print_str += print_driver.enum_str(self.type) + ") from "
        print_str += self.requestor.name() + " "
        if self.data_valid:
            print_str += "{D: " + str(self.data) + " to "
            print_str += " ["
            for receiver in self.data_recvers:
                print_str += receiver.name() + " "
            print_str += "] "
            if self.is_data_from_owner:
                print_str += "from owner "
            print_str += "}"
        return print_str

class Bus:
    req_queue = []
    req_queue_size = 1

    data_queue = []
    data_queue_size = 1024

    connected_nodes = []
    print_driver = None

    wait_data_event = False

    nodes_rejected_times = {}
    nodes_rejected_times_test = {}

    def connect(self, nodes):
        for node in nodes:
            self.connected_nodes.append(node)
            self.nodes_rejected_times[node] = 0
            self.nodes_rejected_times_test[node.name()] = 0
            node.bus = self

    def name(self):
        return "Bus"

    def send_req_event(self, event):
        result = False
        if event.type == EventType.Data:
            if len(self.data_queue) < self.data_queue_size:
                self.data_queue.append(event)
                result = True
            else:
                result = False
        elif not self.wait_data_event:
            if len(self.req_queue) < self.req_queue_size:
                self.req_queue.append(event)
                # traceback.print_stack()
                result = True
            else:
                result = False
        else:
            result = False
        
        if result:
            self.nodes_rejected_times[event.requestor] = 0
            self.nodes_rejected_times_test[event.requestor.name()] = 0
        else:
            self.nodes_rejected_times[event.requestor] += 1
            self.nodes_rejected_times_test[event.requestor.name()] += 1

        print_driver.print(f"bus recv event", f"event is {event.print()}", f"recv result is {result}", Flag="Bus")
        return result
    
    def tick_run(self):
        print_driver.print("debug", len(self.req_queue), len(self.data_queue), self.wait_data_event, Flag="Debug")

        req_event = None
        if len(self.req_queue) > 0:
            req_event = self.req_queue.pop(0)
        
        data_event = None
        if len(self.data_queue) > 0:
            data_event = self.data_queue.pop(0)

        if req_event:
            print_driver.print(f"send event to all nodes", f"event is {req_event.print()}", Flag="Bus")
            for node in self.connected_nodes:
                node.process_req_event(req_event)
            # if req_event.type != EventType.PutM:
            self.wait_data_event = True

        if data_event:
            print_driver.print(f"send event to data recvers", Flag="Bus")
            print_driver.print(f"event is {data_event.print()}", Flag="Bus")
            for node in data_event.data_recvers:
                node.process_req_event(data_event)
            self.wait_data_event = False

        sorted_nodes = sorted(self.nodes_rejected_times.keys(), key=lambda node: self.nodes_rejected_times[node], reverse=True)
        sorted_nodes_test = sorted(self.nodes_rejected_times_test.keys(), key=lambda node: self.nodes_rejected_times_test[node], reverse=True)
        print(sorted_nodes_test, self.nodes_rejected_times_test)
        for node in sorted_nodes:
            node.resend_event()

class Cache:
    state = CacheState.I
    data = 0
    data_valid = False

    bus = None
    llc = None

    retry_send_event = None
    core_stall_event = None
    print_driver = None

    id = None

    def __init__(self):
        global global_requestor_id
        self.id = global_requestor_id
        global_requestor_id += 1
    
    def name(self):
        return "Cache" + str(self.id)

    def process_req_event(self, event):
        if event.type == EventType.Load:
            if self.state == CacheState.I:
                cache_event = Event(
                    type=EventType.GetS,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
                send_done = self.bus.send_req_event(cache_event)
                if not send_done:
                    self.retry_send_event = cache_event
                else:
                    self.state = CacheState.ISD
                self.core_stall_event = event
                return (0, False)
            elif self.state == CacheState.ISD or self.state == CacheState.IMD:
                self.core_stall_event = event
                return (0, False)
            elif self.state == CacheState.S or self.state == CacheState.SMD or self.state == CacheState.M:
                return (self.data, True)

        elif event.type == EventType.Store:
            if self.state == CacheState.I:
                cache_event = Event(
                    type=EventType.GetM,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
                send_done = self.bus.send_req_event(cache_event)
                if not send_done:
                    self.retry_send_event = cache_event
                else:
                    self.state = CacheState.IMD
                self.core_stall_event = event
                return (0, False)
            elif self.state == CacheState.ISD or self.state == CacheState.IMD or self.state == CacheState.SMD:
                self.core_stall_event = event
                return (0, False)
            elif self.state == CacheState.S:
                cache_event = Event(
                    type=EventType.GetM,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
                send_done = self.bus.send_req_event(cache_event)
                if not send_done:
                    self.retry_send_event = cache_event
                else:
                    self.state = CacheState.SMD
                self.core_stall_event = event
                return (0, False)
            elif self.state == CacheState.M:
                self.data = event.data
                return (self.data, True)
        
        elif event.type == EventType.Replacement:
            if self.state == CacheState.I:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == CacheState.ISD or self.state == CacheState.IMD or self.state == CacheState.SMD:
                self.core_stall_event = event
                return (0, False)
            elif self.state == CacheState.S:
                self.state = CacheState.I
                return (0, True)
            elif self.state == CacheState.M:
                cache_event = Event(
                    type=EventType.PutM,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
                send_done = self.bus.send_req_event(cache_event)
                if not send_done:
                    self.retry_send_event = event
                    return (0, False)
                else:
                    cache_data_event = Event(
                        type=EventType.Data,
                        requestor=self,
                        data=self.data,
                        data_valid=True,
                        is_request=True,
                        data_recvers=[llc],
                        is_data_from_owner=True
                    )
                    send_done = self.bus.send_req_event(cache_data_event)
                    assert send_done
                    self.state = CacheState.I
                    return (0, True)

        elif event.type == EventType.GetS and event.requestor == self:
            if self.state == CacheState.ISD:
                return (0, True)
            else:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()

        elif event.type == EventType.GetM and event.requestor == self:
            if self.state == CacheState.IMD:
                return (0, True)
            elif self.state == CacheState.SMD:
                return (0, True)
            else:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
        
        elif event.type == EventType.PutM and event.requestor == self:
            if self.state == CacheState.I:
                self.data = event.data
                return (0, True)
            else:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()

        elif event.type == EventType.Data and self in event.data_recvers:
            if self.state == CacheState.ISD:
                self.data = event.data
                self.data_valid = True
                self.state = CacheState.S
                if self.core_stall_event and self.core_stall_event.type == EventType.Load:
                    core_resp_event = Event(
                        type=EventType.Load,
                        requestor=self,
                        data=self.data,
                        data_valid=True,
                        is_request=False
                    )
                    send_done = self.core_stall_event.requestor.send_resp_event(core_resp_event)
                    assert send_done
            elif self.state == CacheState.IMD or self.state == CacheState.SMD:
                self.data = event.data
                self.data_valid = True
                self.state = CacheState.M
                if self.core_stall_event:
                    if self.core_stall_event.type == EventType.Load:
                        core_resp_event = Event(
                            type=EventType.Load,
                            requestor=self,
                            data=self.data,
                            data_valid=True,
                            is_request=False
                        )
                        send_done = self.core_stall_event.requestor.send_resp_event(core_resp_event)
                        assert send_done
                    elif self.core_stall_event.type == EventType.Store:
                        self.data = self.core_stall_event.data
                        data_driver.data_valid = True
                        core_resp_event = Event(
                            type=EventType.Store,
                            requestor=self,
                            data=self.data,
                            data_valid=True,
                            is_request=False
                        )
                        send_done = self.core_stall_event.requestor.send_resp_event(core_resp_event)
                        assert send_done
            else:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()

        elif event.type == EventType.GetS and event.requestor != self:
            if self.state == CacheState.I:
                return (0, True)
            elif self.state == CacheState.S:
                return (0, True)
            elif self.state == CacheState.M:
                cache_event = Event(
                    type=EventType.Data,
                    requestor=self,
                    data=self.data,
                    data_valid=True,
                    is_request=True,
                    is_data_from_owner=True,
                    data_recvers=[llc, event.requestor]
                )
                send_done = self.bus.send_req_event(cache_event)
                assert send_done
                self.state = CacheState.S
                return (0, True)
            else:
                print_driver.print_snh(self.name(), event, self.state)

        elif event.type == EventType.GetM and event.requestor != self:
            if self.state == CacheState.I:
                return (0, True)
            elif self.state == CacheState.S:
                self.state = CacheState.I
                return (0, True)
            elif self.state == CacheState.M:
                cache_event = Event(
                    type=EventType.Data,
                    requestor=self,
                    data=self.data,
                    data_valid=True,
                    is_request=True,
                    is_data_from_owner=True,
                    data_recvers=[event.requestor]
                )
                send_done = self.bus.send_req_event(cache_event)
                assert send_done
                self.state = CacheState.I
                return (0, True)
            else:
                print_driver.print_snh(self.name(), event, self.state)

        elif event.type == EventType.PutM and event.requestor != self:
            if self.state == CacheState.I:
                return (0, True)
            else:
                print_driver.print_snh(self.name(), event, self.state)

    def resend_event(self):
        if not self.retry_send_event is None:
            if self.retry_send_event.type == EventType.GetS and self.state == CacheState.I:
                send_done = self.bus.send_req_event(self.retry_send_event)
                if send_done:
                    self.retry_send_event = None
                    self.state = CacheState.ISD
                return

            if self.retry_send_event.type == EventType.GetM and self.state == CacheState.I:
                send_done = self.bus.send_req_event(self.retry_send_event)
                if send_done:
                    self.retry_send_event = None
                    self.state = CacheState.IMD
                return

            if self.retry_send_event.type == EventType.GetM and self.state == CacheState.S:
                send_done = self.bus.send_req_event(self.retry_send_event)
                if send_done:
                    self.retry_send_event = None
                    self.state = CacheState.SMD
                return

            if self.retry_send_event.type == EventType.PutM and self.state == CacheState.M:
                send_done = self.bus.send_req_event(self.retry_send_event)
                if send_done:
                    self.retry_send_event = None
                    self.state = CacheState.I
                return

    def tick_run(self):
        print_driver.print(self.name(), self.state, self.data, self.data_valid, self.retry_send_event is None, Flag="Cache")
        if self.core_stall_event and self.core_stall_event.type == EventType.Replacement:
            self.process_req_event(self.core_stall_event)

class LLC:
    state = LLCState.IorS
    data = 0
    data_valid = False

    bus = None
    print_driver = None

    def name(self):
        return "LLC"

    def data_init(self, data_value):
        self.data = data_value
        self.data_valid = True

    def connect(self, caches):
        for cache in caches:
            cache.llc = self

    def process_req_event(self, event):
        if event.type == EventType.GetS:
            if self.state == LLCState.IorS:
                llc_event = Event(
                    type=EventType.Data,
                    requestor=self,
                    data=self.data,
                    data_valid=True,
                    is_request=True,
                    data_recvers=[event.requestor]
                )
                send_done = self.bus.send_req_event(llc_event)
                assert send_done
                return (0, True)
            elif self.state == LLCState.IorSD:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == LLCState.M:
                self.state = LLCState.IorSD
                return (0, True)
        
        elif event.type == EventType.GetM:
            if self.state == LLCState.IorS:
                llc_event = Event(
                    type=EventType.Data,
                    requestor=self,
                    data=self.data,
                    data_valid=True,
                    is_request=True,
                    data_recvers=[event.requestor]
                )
                send_done = self.bus.send_req_event(llc_event)
                assert send_done
                self.state = LLCState.M
                return (0, True)
            elif self.state == LLCState.IorSD:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == LLCState.M:
                return (0, True)
        
        elif event.type == EventType.PutM:
            if self.state == LLCState.IorS or self.state == LLCState.IorSD:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == LLCState.M:
                self.state = LLCState.IorSD
                return (0, True)
        
        elif event.type == EventType.Data and event.is_data_from_owner:
            if self.state == LLCState.IorS:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == LLCState.IorSD:
                self.data = event.data
                self.data_valid = True
                self.state = LLCState.IorS
                return (0, True)
            elif self.state == LLCState.M:
                print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()

    def resend_event(self):
        pass

class Core:
    load_data = 0
    store_data = 0
    
    verity_load_times = 0
    verity_store_times = 0

    wait_event = None

    cache = None
    data_driver = None
    print_driver = None

    def name(self):
        return "Core" + str(self.cache.id)

    def connect(self, objects):
        for cache in objects:
            self.cache = cache

    def send_resp_event(self, event):
        if event.type == EventType.Load:
            self.load_data = event.data
            self.wait_event = None
            self.data_driver.verify_load(self)
            return True

        elif event.type == EventType.Store:
            self.wait_event = None
            self.data_driver.verify_store(self)
            return True

    def tick_run(self):
        if not self.wait_event:
            event = None 
            while event is None:
                event = self.make_random_event()
            (resp_data, send_done) = self.cache.process_req_event(event)
            print_driver.print(f"{self.name()} send event to cache", f"event is {event.print()}", f"result is {send_done}", Flag="Core")
            if send_done:
                if event.type == EventType.Load:
                    self.load_data = resp_data
                    self.data_driver.verify_load(self)

                elif event.type == EventType.Store:
                    self.data_driver.verify_store(self)
            else:
                if event.type != EventType.Replacement:
                    self.wait_event = event

        else:
            print_driver.print(f"{self.name()} wait resp event from cache", Flag="Core")

    def make_random_event(self):
        random_integer = random.randrange(0, 3)
        if random_integer == 0:
            return Event(
                type=EventType.Load,
                requestor=self,
                data=0,
                data_valid=False,
                is_request=True
            )
        elif random_integer == 1:
            self.store_data = self.data_driver.get_data()
            return Event(
                type=EventType.Store,
                requestor=self,
                data=self.store_data,
                data_valid=True,
                is_request=True
            )
        elif random_integer == 2:
            if self.cache.state != CacheState.I:
                return Event(
                    type=EventType.Replacement,
                    requestor=self,
                    data=0,
                    data_valid=False,
                    is_request=True
                )
            else:
                return None

class DataDriver:
    drive_data = 0
    verify_data = 0
    verify_data_valid = False
    print_driver = None

    cores = []

    def get_data(self):
        self.drive_data += 1
        return self.drive_data

    def data_init(self, data_value):
        self.drive_data = data_value
        self.verify_data = data_value
        self.verify_data_valid = True

    def connect(self, objects):
        for core in objects:
            core.data_driver = self
            self.cores.append(core)

    def verify_load(self, core):
        if  (not self.verify_data_valid) or core.load_data != self.verify_data:
            print_driver.print("ERROR: Data mismatch", Flag="Verify")
            raise Exception("Should not happen")
            exit()
        else:
            print_driver.print(f"verify: Data match: {core.name()} load {core.load_data}", Flag="Verify")
        core.verity_load_times += 1
    
    def verify_store(self, core):
        self.verify_data = core.store_data
        self.verify_data_valid = True
        print_driver.print(f"verify: Data update: {core.name()} store {core.store_data}", Flag="Verify")
        core.verity_store_times += 1

class TickDriver:
    tick = 0
    max_tick = 1024
    print_driver = None

    tick_objects = []

    def add_objects(self, objects):
        for object in objects:
            self.tick_objects.append(object)

    def run(self):
        while self.tick < self.max_tick:
            for object in self.tick_objects:
                object.tick_run()
            self.tick += 1
        print(f"simulation finished @ {self.tick} Ticks")

class PrintDriver:

    tick_driver = None

    print_flags = []

    def add_flags(self, flags):
        for flag in flags:
            self.print_flags.append(flag)

    def add_tick_driver(self, tick_driver):
        self.tick_driver = tick_driver
    
    def connect(self, objects):
        for object in objects:
            object.print_driver = self
    
    def print(self, *args, **kwargs):  
        # 如果有flag参数但是不在flags数组中，则不打印
        flag = kwargs.pop('Flag', None)
        if not (flag is None or flag in self.print_flags):  
            return

        prefix = str(self.tick_driver.tick) + " Tick: "
        # 使用format方法将前缀和参数格式化输出  
        formatted_args = [prefix] + list(args)  
        formatted_str = " ".join(map(str, formatted_args))  
          
        # 分离出end参数，因为print的end参数在格式化字符串时不需要  
        end = kwargs.pop('end', '\n')  
          
        # 使用内置的print函数打印格式化后的字符串，并传递剩余的kwargs  
        print(formatted_str, end=end, **kwargs)  
    
    def enum_str(self, enum_value):
        return f"{enum_value.__class__.__name__}.{enum_value.name}"

    def print_snh(self, node_name, event, state):  
        self.print(f"ERROR: should not happen: From ({self.enum_str(event.type)}@{event.requestor.name()}) To ({self.enum_str(state)}@{node_name})")


core0 = Core()
core1 = Core()
core2 = Core()
cache0 = Cache()
cache1 = Cache()
cache2 = Cache()
llc = LLC()
bus = Bus()

core0.connect([cache0])
core1.connect([cache1])
core2.connect([cache2])
bus.connect([cache0, cache1, cache2, llc])
llc.connect([cache0, cache1, cache2])

data_driver = DataDriver()
tick_driver = TickDriver()
print_driver = PrintDriver()

data_driver.connect([core0, core1, core2])
tick_driver.add_objects([bus, core0, core1, core2, cache0, cache1, cache2])
print_driver.add_tick_driver(tick_driver)
print_driver.connect([core0, core1, core2, cache0, cache1, cache2, bus, llc, data_driver])
print_driver.add_flags(["Verify", "Core", "Bus"])

data_driver.data_init(0)
llc.data_init(0)

tick_driver.max_tick = 4096
tick_driver.run()

print("core0", core0.verity_load_times, core0.verity_store_times, core0.verity_load_times + core0.verity_store_times)
print("core1", core1.verity_load_times, core1.verity_store_times, core1.verity_load_times + core1.verity_store_times)
print("core2", core2.verity_load_times, core2.verity_store_times, core2.verity_load_times + core2.verity_store_times)
