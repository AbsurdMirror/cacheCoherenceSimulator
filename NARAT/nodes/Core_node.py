from enums.MSI_enum import *
from cacheCoherenceSimulate.event import *
from cacheCoherenceSimulate.sim_enum import *
import random

class CoreNode:
    EventCmd = NARAT_MSI_EventCmd
    CacheState = NARAT_MSI_CacheState

    def __init__(self, id):
        self.id = id
        self.load_data = 0
        self.store_data = 0
        
        self.verity_load_times = 0
        self.verity_store_times = 0

        self.wait_resp_event = None

        self.cache = None
        self.data_driver = None
        self.print_driver = None

    def name(self):
        return "Core" + str(self.id)

    def connect_cache(self, cache):
        self.cache = cache

    def process_resp_event(self, event):
        if self.wait_resp_event.id == event.id:
            self.wait_resp_event = None
            self.excel_driver.ptrace(self, f"Recv {event.cmd.name}<{event.id}> D:{event.data}")

            if event.cmd == self.EventCmd.Load:
                self.load_data = event.data
                self.data_driver.verify_load(self)

            elif event.cmd == self.EventCmd.Store:
                self.data_driver.verify_store(self)

    def tick_run(self):
        if not self.wait_resp_event:
            event = None 
            while event is None:
                event = self.make_random_event()

            self.cache.core_req_recv_queue.append(event)
            self.print_driver.print(self.name(), " Send req event: ", event.print())
            self.excel_driver.ptrace(self, f"Send {event.cmd.name}<{event.id}> D:{event.data}")
            self.wait_resp_event = event                    

        elif len(self.cache.core_resp_send_queue) > 0:
            self.process_resp_event(self.cache.core_resp_send_queue.pop(0))

    def make_random_event(self):
        random_integer = random.randrange(0, 3)
        if random_integer == 0:
            return Event(
                type=EventType.Request,
                cmd=self.EventCmd.Load,
                requestor=self,
                is_data_from_owner = False,
                broadcast_all = False,
                recivers = [self.cache],
                data = None
            )
        elif random_integer == 1:
            self.store_data = self.data_driver.get_data()
            return Event(
                type=EventType.Request,
                cmd=self.EventCmd.Store,
                requestor=self,
                is_data_from_owner = False,
                broadcast_all = False,
                recivers = [self.cache],
                data=self.store_data
            )
        elif random_integer == 2:
            if self.cache.state != self.CacheState.I:
                return Event(
                    type=EventType.Request,
                    cmd=self.EventCmd.Replacement,
                    requestor=self,
                    is_data_from_owner = False,
                    broadcast_all = False,
                    recivers = [self.cache],
                    data=None
                )
            else:
                return None
