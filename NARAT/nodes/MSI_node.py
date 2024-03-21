from cacheCoherenceSimulate.node import BaseNode
from cacheCoherenceSimulate.sim_enum import *
from cacheCoherenceSimulate.event import *
from enums.MSI_enum import *

# NON-ATOMIC REQUESTS, ATOMIC TRANSACTIONS Node
class NARAT_MSI_Cache(BaseNode):
    CacheState = NARAT_MSI_CacheState
    EventCmd = NARAT_MSI_EventCmd
    CacheEventCmd = NARAT_MSI_CacheEventCmd
    LLCEventCmd = NARAT_MSI_LLCEventCmd

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

    def send_first_data_to_bus(self):
        event = self.data_send_queue.pop(0)
        # if self.state == self.CacheState.M:
        #     self.state = self.send_data_after_state

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
            self.state = self.CacheState.ISAD
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
            if self.state == self.CacheState.I:
                self.state = self.CacheState.IMAD
            elif self.state == self.CacheState.S:
                self.state = self.CacheState.SMAD

        def issue_PutM(self, event):
            cache_event = Event(
                type=EventType.Request,
                cmd=self.EventCmd.PutM,
                requestor=self,
                is_data_from_owner = True,
                broadcast_all = True,
                recivers = [],
                data = None
            )
            cache_event.inqueue_tick = self.tick_driver.tick
            self.req_send_queue.append(cache_event)
            self.state = self.CacheState.MIA
            self.core_stall_event = event

        def snh(self, event):
            self.print_driver.print_snh(self.name(), event, self.state)
            raise Exception("Should not happen")        

        def invalidate(self, event):
            if self.state == self.CacheState.S:
                self.state = self.CacheState.I
            elif self.state == self.CacheState.SMAD:
                self.state = self.CacheState.IMAD

        def doNothing(self, event):
            pass

        def send_data(self, event):
            recivers = []
            eventCmd = self.EventCmd.Data

            if self.state == self.CacheState.M:
                if event.cmd == self.EventCmd.GetS:
                    recivers = [self.llc, event.requestor]
                    self.state = self.CacheState.S
                else:
                    recivers = [event.requestor]
                    self.state = self.CacheState.I

            elif self.state == self.CacheState.MIA:
                if event.cmd == self.EventCmd.GetS:
                    recivers = [self.llc, event.requestor]
                else:
                    recivers = [event.requestor]

                self.state = self.CacheState.IIA
            
            else:
                recivers = [self.llc]
                self.state = self.CacheState.I
                eventCmd = self.EventCmd.NoData
                core_resp_event = Event(
                    type=EventType.Response,
                    cmd=self.EventCmd.Replacement,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [],
                    data = None,
                    id = self.core_stall_event.id
                )
                self.core_resp_send_queue.append(core_resp_event)


            cache_event = Event(
                type=EventType.Data,
                cmd=eventCmd,
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
                    data = self.data,
                    id = event.id
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
                    data = None,
                    id = event.id
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
                    data = None,
                    id = event.id
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

            self.reprocess_core_stall_event()
            return (0, True)

        def issue_Done(self, event):
            if self.state == self.CacheState.ISAD and event.cmd == self.EventCmd.GetS:
                self.state = self.CacheState.ISD
            elif self.state == self.CacheState.IMAD and event.cmd == self.EventCmd.GetM:
                self.state = self.CacheState.IMD
            elif self.state == self.CacheState.SMAD and event.cmd == self.EventCmd.GetM:
                self.state = self.CacheState.SMD
            elif self.state == self.CacheState.MIA and event.cmd == self.EventCmd.PutM:
                cache_data_event = Event(
                    type=EventType.Data,
                    cmd=self.EventCmd.Data,
                    requestor=self,
                    is_data_from_owner = True,
                    broadcast_all = False,
                    recivers = [self.llc],
                    data = self.data,
                    id = event.id
                )
                cache_data_event.inqueue_tick = self.tick_driver.tick
                self.data_send_queue.append(cache_data_event)
                # self.send_data_after_state = self.CacheState.I
                self.state = self.CacheState.I
                core_resp_event = Event(
                    type=EventType.Response,
                    cmd=self.EventCmd.Replacement,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [],
                    data = None,
                    id = self.core_stall_event.id
                )
                self.core_resp_send_queue.append(core_resp_event)

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
        self.issue_Done = issue_Done
        
        self.process_func_table = [
            # State I
            [issue_getS, issue_getM] + [snh] * 4 + [doNothing] * 3 + [snh],

            # State ISAD
            [miss] * 3 + [issue_Done] + [snh] * 2 + [doNothing] * 3 + [snh],

            # State ISD
            [miss] * 3 + [snh] * 6 + [copy_data],

            # State IMAD
            [miss] * 3 + [snh, issue_Done, snh] + [doNothing] * 3,

            # State IMD
            [miss] * 3 + [snh] * 6 + [copy_data],
        
            # State S
            [hit, issue_getM, hit] + [snh] * 3 + [doNothing, invalidate, doNothing, snh],

            # State SMAD
            [hit, miss, miss, snh, issue_Done, snh, doNothing, invalidate, doNothing, snh],

            # State SMD
            [hit, miss, miss] + [snh] * 6 + [copy_data],

            # State M
            [hit] * 2 + [issue_PutM] + [snh] * 3 + [send_data] * 2 + [doNothing, snh],

            # State MIA
            [hit] * 2 + [miss] + [snh] * 2 + [issue_Done] + [send_data] * 2 + [doNothing, snh],

            # State IIA
            [miss] * 3 + [snh] * 2 + [send_data] + [doNothing] * 2 + [doNothing, snh]
        ]

    def process_event(self, event):
        cache_event_trans_table = {
            "Load_False"        : self.CacheEventCmd.Load       ,
            "Store_False"       : self.CacheEventCmd.Store      ,
            "Replacement_False" : self.CacheEventCmd.Replacement,
            "GetS_True"         : self.CacheEventCmd.OwnGetS    ,
            "GetM_True"         : self.CacheEventCmd.OwnGetM    ,
            "PutM_True"         : self.CacheEventCmd.OwnPutM    ,
            "GetS_False"        : self.CacheEventCmd.OtherGetS  ,
            "GetM_False"        : self.CacheEventCmd.OtherGetM  ,
            "PutM_False"        : self.CacheEventCmd.OtherPutM  ,
            "Data_False"        : self.CacheEventCmd.Data       
        }
        cache_event_cmd = cache_event_trans_table[f"{event.cmd.name}_{event.requestor == self}"]
        self.print_driver.print(self.name(), f"@ state{self.state.name} process_event {cache_event_cmd.name} {event.print()}")
        self.excel_driver.pstate("cache", self.state.value, cache_event_cmd.value, self.tick_driver.tick)
        before_state = self.state
        before_data = self.data
        self.process_func_table[self.state.value][cache_event_cmd.value](self, event)
        self.excel_driver.ptrace(self, f"E:{cache_event_cmd.name}<{event.id}>\nS:{before_state.name}->{self.state.name}\nD:{before_data}->{self.data}")

    def tick_run(self):
        self.tick_run_queue(self.req_recv_queue)
        self.tick_run_queue(self.resp_recv_queue)
        self.tick_run_queue(self.data_recv_queue)
        self.tick_run_queue(self.core_req_recv_queue)

    def get_bus_delay(self):
        return 1


class NARAT_MSI_LLC(BaseNode):
    LLCState = NARAT_MSI_LLCState
    EventCmd = NARAT_MSI_EventCmd
    CacheEventCmd = NARAT_MSI_CacheEventCmd
    LLCEventCmd = NARAT_MSI_LLCEventCmd

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
        llc_event_trans_table = {
            "GetS"  : self.LLCEventCmd.GetS  ,
            "GetM"  : self.LLCEventCmd.GetM  ,
            "PutM"  : self.LLCEventCmd.PutM  ,
            "Data"  : self.LLCEventCmd.Data  ,
            "NoData": self.LLCEventCmd.NoData 
        }
        llc_event_cmd = llc_event_trans_table[event.cmd.name]
        self.print_driver.print(self.name(), f"@ state{self.state.name} process_event {llc_event_cmd.name} {event.print()}")
        before_state = self.state
        before_data = self.data
        self.excel_driver.pstate("llc", self.state.value, llc_event_cmd.value, self.tick_driver.tick)
        self.process_func_table[self.state.value][llc_event_cmd.value](self, event)
        self.excel_driver.ptrace(self, f"E:{llc_event_cmd.name}<{event.id}>\nS:{before_state.name}->{self.state.name}\nD:{before_data}->{self.data}")

    def initial_process_func_table(self):
        def snh(self, event):
            self.print_driver.print_snh(self.name(), event, self.state)
            raise Exception("Should not happen")        

        def doNothing(self, event):
            pass

        def send_data(self, event):
            if event.cmd == self.EventCmd.GetM:
                self.state = self.LLCState.M
            
            llc_event = Event(
                type=EventType.Data,
                cmd=self.EventCmd.Data,
                requestor=self,
                is_data_from_owner = True,
                broadcast_all = False,
                recivers = [event.requestor],
                data = self.data,
                id = event.id
            )
            llc_event.inqueue_tick = self.tick_driver.tick
            self.data_send_queue.append(llc_event)

        def copy_data(self, event):
            self.data = event.data
            self.state = self.LLCState.IorS

        def change_state(self, event):
            if self.state == self.LLCState.IorS and event.cmd == self.EventCmd.PutM:
                self.state = self.LLCState.IorSD
            elif self.state == self.LLCState.IorSD and event.cmd == self.EventCmd.NoData:
                self.state = self.LLCState.IorS
            elif self.state == self.LLCState.M and event.cmd == self.EventCmd.GetS:
                self.state = self.LLCState.IorSD
            elif self.state == self.LLCState.M and event.cmd == self.EventCmd.PutM:
                self.state = self.LLCState.MD
            elif self.state == self.LLCState.MD and event.cmd == self.EventCmd.NoData:
                self.state = self.LLCState.M

        self.doNothing  = doNothing
        self.send_data  = send_data
        self.copy_data  = copy_data
        self.change_state = change_state
        self.snh        = snh
        
        self.process_func_table = [
            # State IorS
            [send_data, send_data, change_state, snh, snh],

            # State IorSD
            [snh, snh, snh, copy_data, change_state],

            # State M
            [change_state, doNothing, change_state, snh, snh],

            # State MD
            [snh, snh, snh, copy_data, change_state]
        ]

    def send_first_data_to_bus(self):
        event = self.data_send_queue.pop(0)
        # if self.state == self.LLCState.IorS and event.cmd == self.EventCmd.Data:
        #     self.state = self.send_data_after_state
        #     self.send_data_after_state = None

    def tick_run(self):
        #print("debug tick_run llc", self.req_recv_queue)
        self.tick_run_queue(self.req_recv_queue)
        self.tick_run_queue(self.resp_recv_queue)
        self.tick_run_queue(self.data_recv_queue)

    def get_bus_delay(self):
        return 1
