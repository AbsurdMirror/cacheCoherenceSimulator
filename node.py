from cacheCoherenceSimulate.sim_enum import *
from cacheCoherenceSimulate.event import *

class BaseNode:
    id = None
    print_driver = None
    tick_driver = None

    state = None
    data = None

    # process_func_table[State][Event]
    process_func_table = None

    req_send_queue = []
    req_recv_queue = []
    resp_send_queue = []
    resp_recv_queue = []
    data_send_queue = []
    data_recv_queue = []

    def __init__(self, id):
        self.id = id
        self.initial_process_func_table()
        self.req_send_queue = []
        self.req_recv_queue = []
        self.resp_send_queue = []
        self.resp_recv_queue = []
        self.data_send_queue = []
        self.data_recv_queue = []

    def name(self):
        return "BaseNode" + str(self.id)

    def data_init(self, data):
        self.data = data

    def initial_process_func_table(self):
        self.print_driver.print("Error: BaseNode not implement initial_process_func_table function")
        raise Exception("Error: BaseNode not implement initial_process_func_table function")

    def send_first_req_to_bus(self):
        self.print_driver.print("Error: BaseNode not implement send_first_req_to_bus function")
        raise Exception("Error: BaseNode not implement send_first_req_to_bus function")

    def tick_run_queue(self, queue):
        if len(queue) > 0:
            event = queue.pop(0)
            self.process_event(event)

    def tick_run(self):
        self.print_driver.print("Error: BaseNode not implement tick_run function")
        raise Exception("Error: BaseNode not implement tick_run function")

    def get_bus_delay(self):
        self.print_driver.print("Error: BaseNode not implement get_bus_delay function")
        raise Exception("Error: BaseNode not implement get_bus_delay function")

# ATOMIC REQUESTS, ATOMIC TRANSACTIONS Node
class ARAT_Cache(BaseNode):
    CacheState = ARAT_MSI_CacheState
    EventCmd = ARAT_MSI_EventCmd

    def __init__(self, id):
        super().__init__(id)
        self.id = id
        self.initial_process_func_table()
        self.state = self.CacheState.I
        self.send_data_after_state = None
        self.core_stall_event = None
        self.core_req_recv_queue = []
        self.core_resp_send_queue = []
        self.llc = None

    def name(self):
        return "Cache" + str(self.id)

    def send_first_req_to_bus(self):
        event = self.req_send_queue.pop(0)
        if self.state == self.CacheState.I:
            if event.cmd == self.EventCmd.GetS:
                self.state = self.CacheState.ISD
            elif event.cmd == self.EventCmd.GetM:
                self.state = self.CacheState.IMD
        elif self.state == self.CacheState.S:
            if event.cmd == self.EventCmd.GetM:
                self.state = self.CacheState.SMD
        elif self.state == self.CacheState.M:
            if event.cmd == self.EventCmd.PutM:
                pass

    def send_first_data_to_bus(self):
        event = self.data_send_queue.pop(0)
        if self.state == self.CacheState.M:
            self.state = self.send_data_after_state


    # def send_core_resp(self, data, result):
    #     self.core_stall_event.requestor.process_resp_event(data, result)

    def reprocess_core_stall_event(self):
        if self.core_stall_event:
            self.process_event(self.core_stall_event)

    def initial_process_func_table(self):
        def issue_getS(self, event):
            cache_event = Event(
                type=EventType.Request,
                cmd=self.EventCmd.GetS,
                requestor=self,
                is_data_from_owner = False,
                broadcast_all = True,
                recivers = [],
                data = None
            )
            cache_event.inqueue_tick = self.tick_driver.tick
            self.req_send_queue.append(cache_event)
            #print("debug issue_getS", len(self.req_send_queue), self.req_send_queue)
            self.miss(self, event)
    
        def issue_getM(self, event):
            cache_event = Event(
                type=EventType.Request,
                cmd=self.EventCmd.GetM,
                requestor=self,
                is_data_from_owner = False,
                broadcast_all = True,
                recivers = [],
                data = None
            )
            cache_event.inqueue_tick = self.tick_driver.tick
            self.req_send_queue.append(cache_event)
            self.miss(self, event)

        def issue_PutM(self, event):
            cache_event = Event(
                type=EventType.Request,
                cmd=self.EventCmd.PutM,
                requestor=self,
                is_data_from_owner = True,
                broadcast_all = False,
                recivers = [self.llc],
                data = None
            )
            cache_event.inqueue_tick = self.tick_driver.tick
            self.req_send_queue.append(cache_event)
            cache_data_event = Event(
                type=EventType.Data,
                cmd=self.EventCmd.Data,
                requestor=self,
                is_data_from_owner = True,
                broadcast_all = False,
                recivers = [self.llc],
                data = self.data,
                id = cache_event.id
            )
            cache_data_event.inqueue_tick = self.tick_driver.tick
            self.data_send_queue.append(cache_data_event)
            self.send_data_after_state = self.CacheState.I

        def snh(self, event):
            self.print_driver.print_snh(self.name(), event, self.state)
            raise Exception("Should not happen")        

        def invalidate(self, event):
            self.state = self.CacheState.I

        def doNothing(self, event):
            pass

        def send_data(self, event):
            recivers = []
            if event.cmd == self.EventCmd.GetS:
                recivers.append(self.llc)
                self.send_data_after_state = self.CacheState.S
            else:
                self.send_data_after_state = self.CacheState.I
            recivers.append(event.requestor)

            cache_event = Event(
                type=EventType.Data,
                cmd=self.EventCmd.Data,
                requestor=self,
                is_data_from_owner = True,
                broadcast_all = False,
                recivers = recivers,
                data = self.data,
                id = event.id
            )
            cache_event.inqueue_tick = self.tick_driver.tick
            self.data_send_queue.append(cache_event)

        def miss(self, event):
            self.core_stall_event = event

        def hit(self, event):
            cache_event = None
            if event.cmd == self.EventCmd.Load:
                cache_event = Event(
                    type=EventType.Response,
                    cmd=self.EventCmd.Load,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [],
                    data = self.data
                )
            elif event.cmd == self.EventCmd.Store:
                self.data = event.data
                cache_event = Event(
                    type=EventType.Response,
                    cmd=self.EventCmd.Store,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [],
                    data = None
                )
            elif event.cmd == self.EventCmd.Replacement:
                self.invalidate(self, event)
                cache_event = Event(
                    type=EventType.Response,
                    cmd=self.EventCmd.Replacement,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [],
                    data = None
                )
            self.core_resp_send_queue.append(cache_event)

        def copy_data(self, event):
            self.data = event.data

            if self.state == self.CacheState.ISD:
                self.state = self.CacheState.S
            elif self.state == self.CacheState.IMD:
                self.state = self.CacheState.M
            elif self.state == self.CacheState.SMD:
                self.state = self.CacheState.M
            else:
                self.print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")

            self.reprocess_core_stall_event()
            return (0, True)

        self.issue_getS = issue_getS
        self.issue_getM = issue_getM
        self.issue_PutM = issue_PutM
        self.invalidate = invalidate
        self.doNothing  = doNothing
        self.send_data  = send_data
        self.miss       = miss
        self.hit        = hit
        self.copy_data  = copy_data
        self.snh        = snh
        
        self.process_func_table = [
            # State I
            [issue_getS, issue_getM] + [snh] * 5 + [doNothing] * 3,

            # State ISD
            [miss] * 2 + [miss, doNothing] + [snh] * 2 + [copy_data] + [snh] * 3,

            # State IMD
            [miss] * 2 + [miss, snh, doNothing, snh, copy_data] + [snh] * 3,
        
            # State S
            [hit, issue_getM, hit] + [snh] * 4 + [doNothing, invalidate, snh],

            # State SMD
            [hit, miss, miss, snh, doNothing, snh, copy_data] + [snh] * 3,

            # State M
            [hit] * 2 + [issue_PutM] + [snh] * 4 + [send_data] * 2 + [snh]
        ]

    def process_event(self, event):
        cache_event_cmd = event.cmd
        if cache_event_cmd in [self.EventCmd.GetS, self.EventCmd.GetM, self.EventCmd.PutM]:
            cache_event_trans_table = {
                "GetS_True": ARAT_MSI_EventCmd.OwnGetS,
                "GetS_False": ARAT_MSI_EventCmd.OtherGetS,
                "GetM_True": ARAT_MSI_EventCmd.OwnGetM,
                "GetM_False": ARAT_MSI_EventCmd.OtherGetM,
                "PutM_True": ARAT_MSI_EventCmd.OwnPutM,
                "PutM_False": ARAT_MSI_EventCmd.OtherPutM
            }
            cache_event_cmd = cache_event_trans_table[f"{cache_event_cmd.name}_{event.requestor == self}"]
        
        self.print_driver.print(self.name(), f"@ state{self.state.name} process_event {cache_event_cmd.name} {event.print()}")
        #print("debug process event", self.state.value, cache_event_cmd.value, self.process_func_table[self.state.value][cache_event_cmd.value])
        self.process_func_table[self.state.value][cache_event_cmd.value](self, event)

    def tick_run(self):
        self.tick_run_queue(self.req_recv_queue)
        self.tick_run_queue(self.resp_recv_queue)
        self.tick_run_queue(self.data_recv_queue)
        self.tick_run_queue(self.core_req_recv_queue)

    def get_bus_delay(self):
        return 1


class ARAT_LLC(BaseNode):
    LLCState = ARAT_MSI_LLCState
    EventCmd = ARAT_MSI_EventCmd

    def __init__(self, id):
        super().__init__(id)
        self.id = id
        self.state = self.LLCState.IorS
        self.send_data_after_state = None

    def name(self):
        return "LLC" + str(self.id)

    def bind_caches(self, caches):
        for cache in caches:
            cache.llc = self

    def process_event(self, event):
        self.print_driver.print(self.name(), f"@ state{self.state.name} process_event {event.cmd.name} {event.print()}")
        if event.cmd == self.EventCmd.GetS:
            if self.state == self.LLCState.IorS:
                llc_event = Event(
                    type=EventType.Data,
                    cmd=self.EventCmd.Data,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [event.requestor],
                    data = self.data,
                    id = event.id
                )
                llc_event.inqueue_tick = self.tick_driver.tick
                self.data_send_queue.append(llc_event)
                self.send_data_after_state = self.LLCState.IorS
            elif self.state == self.LLCState.IorSD:
                self.print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == self.LLCState.M:
                self.state = self.LLCState.IorSD
        
        elif event.cmd == self.EventCmd.GetM:
            if self.state == self.LLCState.IorS:
                llc_event = Event(
                    type=EventType.Data,
                    cmd=self.EventCmd.Data,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [event.requestor],
                    data = self.data,
                    id = event.id
                )
                llc_event.inqueue_tick = self.tick_driver.tick
                self.data_send_queue.append(llc_event)
                self.send_data_after_state = self.LLCState.M
            elif self.state == self.LLCState.IorSD:
                self.print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")  
                exit()
            elif self.state == self.LLCState.M:
                pass
        
        elif event.cmd == self.EventCmd.PutM:
            if self.state == self.LLCState.IorS or self.state == self.LLCState.IorSD:
                self.print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == self.LLCState.M:
                self.state = self.LLCState.IorSD
        
        elif event.cmd == self.EventCmd.Data and event.is_data_from_owner:
            if self.state == self.LLCState.IorS:
                self.print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()
            elif self.state == self.LLCState.IorSD:
                self.data = event.data
                self.state = self.LLCState.IorS
            elif self.state == self.LLCState.M:
                self.print_driver.print_snh(self.name(), event, self.state)
                raise Exception("Should not happen")        
                exit()

    def initial_process_func_table(self):
        pass

    def send_first_data_to_bus(self):
        event = self.data_send_queue.pop(0)
        if self.state == self.LLCState.IorS and event.cmd == self.EventCmd.Data:
            self.state = self.send_data_after_state
            self.send_data_after_state = None

    def tick_run(self):
        #print("debug tick_run llc", self.req_recv_queue)
        self.tick_run_queue(self.req_recv_queue)
        self.tick_run_queue(self.resp_recv_queue)
        self.tick_run_queue(self.data_recv_queue)

    def get_bus_delay(self):
        return 1
