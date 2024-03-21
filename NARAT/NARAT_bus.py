from cacheCoherenceSimulate.bus import BaseBus
from enums.Bus_enum import *
from enums.MSI_enum import *

# NON-ATOMIC REQUESTS, ATOMIC TRANSACTIONS Bus
class NARAT_RequestBus(BaseBus):
    def __init__(self):
        super().__init__()
        self.req_event_id = None

    def name(self):
        return "ARAT_RequestBus"
    
    def bus_input_func(self):
        selected_event = None
        selected_node = None
        for node in self.connected_nodes:
            #print("debug bus_input_func", node.name(), len(node.req_send_queue), node.req_send_queue)
            if len(node.req_send_queue) > 0:
                if selected_event is None:
                    selected_event = node.req_send_queue[0]
                    selected_node = node
                elif node.req_send_queue[0].inqueue_tick < selected_event.inqueue_tick:
                    selected_event = node.req_send_queue[0]
                    selected_node = node

        if selected_event is not None:
            selected_node.send_first_req_to_bus()
            self.req_event_id = selected_event.id
            self.excel_driver.ptrace(self, f"{selected_node.name()}-{selected_event.cmd.name}<{selected_event.id}>")
            return selected_event
    
    def bus_output_func(self, node, event):
        node.req_recv_queue.append(event)


class NARAT_ResponseBus(BaseBus):
    def name(self):
        return "ARAT_ResponseBus"
    
    def bus_input_func(self):
        selected_event = None
        selected_node = None
        for node in self.connected_nodes:
            if len(node.resp_send_queue) > 0:
                if selected_event is None:
                    selected_event = node.resp_send_queue[0]
                    selected_node = node
                else:
                    self.print_driver.print("Error: ARAT_ResponseBus find more than one event")
                    raise Exception("Error: ARAT_ResponseBus find more than one event")

        if selected_event is not None:
            selected_node.send_first_resp_to_bus()
            return selected_event
    
    def bus_output_func(self, node, event):
        node.resp_recv_queue.append(event)


class NARAT_DataBus(BaseBus):

    def __init__(self):
        super().__init__()
        self.listen_event_id = None

    def name(self):
        return "ARAT_DataBus"
    
    def bus_input_func(self):
        selected_event = None
        selected_node = None
        for node in self.connected_nodes:
            #print("debug data bus_input_func", node.name(), len(node.data_send_queue), node.data_send_queue)
            if len(node.data_send_queue) > 0:
                if self.listen_event_id == node.data_send_queue[0].id:
                    selected_event = node.data_send_queue[0]
                    selected_node = node
                # else:
                #     self.print_driver.print("Error: ARAT_DataBus find more than one event")
                #     raise Exception("Error: ARAT_DataBus find more than one event")

        if selected_event is not None:
            selected_node.send_first_data_to_bus()
            self.excel_driver.ptrace(self, f"{selected_node.name()}-{selected_event.cmd.name}<{selected_event.id}>\nD:{selected_event.data}")
            return selected_event

    def bus_output_func(self, node, event):
        node.data_recv_queue.append(event)


class NARAT_Bus:
    request_bus = None
    response_bus = None
    data_bus = None

    wait_data_event = False
    wait_req_event = False

    def __init__(self):
        self.request_bus = NARAT_RequestBus()
        self.response_bus = NARAT_ResponseBus()
        self.data_bus = NARAT_DataBus()

        self.request_bus.enable_input = True
        self.wait_req_event = True

        self.state = NARAT_BusState.WaitReq

    def connect(self, nodes):
        for node in nodes:
            self.request_bus.connected_nodes.append(node)
            self.response_bus.connected_nodes.append(node)
            self.data_bus.connected_nodes.append(node)

            # import traceback
            # # 打印函数栈
            # traceback.print_stack()

            self.request_bus.broadcasting_delay_dir[node] = 0
            self.response_bus.broadcasting_delay_dir[node] = 0
            self.data_bus.broadcasting_delay_dir[node] = 0

    def name(self):
        return "NARAT_Bus"

    def tick_run(self):
        self.request_bus.tick_run()
        self.response_bus.tick_run()
        self.data_bus.tick_run()

        if self.state == NARAT_BusState.WaitReq:
            if self.request_bus.busy:
                self.state = NARAT_BusState.TransReq
                self.request_bus.enable_input = False
                self.data_bus.listen_event_id = self.request_bus.req_event_id
                self.print_driver.print(self.name(), "bus state from WaitReq to TransReq")
        elif self.state == NARAT_BusState.TransReq:
            if not self.request_bus.busy:
                self.state = NARAT_BusState.WaitData
                self.data_bus.enable_input = True
                self.print_driver.print(self.name(), "bus state from TransReq to WaitData")
        elif self.state == NARAT_BusState.WaitData:
            if self.data_bus.busy:
                self.state = NARAT_BusState.TransData
                self.data_bus.enable_input = False
                self.print_driver.print(self.name(), "bus state from WaitData to TransData")
        elif self.state == NARAT_BusState.TransData:
            if not self.data_bus.busy:
                self.state = NARAT_BusState.WaitReq
                self.request_bus.enable_input = True
                self.print_driver.print(self.name(), "bus state from TransData to WaitReq")
