from sim_enum import *

class BaseBus:
    print_driver = None

    def __init__(self):
        self.connected_nodes = []
        self.enable_input = False
        self.busy = False
        self.broadcasting_event = None
        self.broadcasting_delay_dir = {}

    def connect(self, nodes):
        for node in nodes:
            self.connected_nodes.append(node)
            self.broadcasting_delay_dir[node] = 0

    def name(self):
        return "BaseBus"
    
    def bus_input_func(self):
        self.print_driver.print("Error: BaseBus not implement input function")
        raise Exception("Error: BaseBus not implement input function")

    def bus_output_func(self, node, event):
        self.print_driver.print("Error: BaseBus not implement output function")
        raise Exception("Error: BaseBus not implement output function")

    def tick_run(self):
        if self.busy:
            broadcast_done_num = 0

            for node in self.connected_nodes:
                #print("debug--", self.connected_nodes)
                #print("debug", self.name(), node.name(), self.broadcasting_delay_dir[node])
                if self.broadcasting_delay_dir[node] > 1:
                    self.broadcasting_delay_dir[node] -= 1
                
                elif self.broadcasting_delay_dir[node] == 1:
                    self.bus_output_func(node, self.broadcasting_event)
                    self.broadcasting_delay_dir[node] -= 1
                
                elif self.broadcasting_delay_dir[node] == 0:
                    broadcast_done_num += 1
            
            if broadcast_done_num == len(self.connected_nodes):
                self.busy = False
            else:
                return

        if not self.enable_input:
            return

        selected_event = self.bus_input_func()

        if selected_event is None:
            return
        
        #print("debug", selected_event.print())
        self.print_driver.print(self.name(), "selected event: ", selected_event.print())

        self.busy = True
        self.broadcasting_event = selected_event

        if selected_event.broadcast_all:
            for node in self.connected_nodes:
                self.broadcasting_delay_dir[node] = node.get_bus_delay()
        else:
            for node in selected_event.recivers:
                self.broadcasting_delay_dir[node] = node.get_bus_delay()

# ATOMIC REQUESTS, ATOMIC TRANSACTIONS Bus
class ARAT_RequestBus(BaseBus):

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
            return selected_event
    
    def bus_output_func(self, node, event):
        node.req_recv_queue.append(event)

class ARAT_ResponseBus(BaseBus):
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

class ARAT_DataBus(BaseBus):

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
            return selected_event

    def bus_output_func(self, node, event):
        node.data_recv_queue.append(event)

class ARAT_Bus:
    request_bus = None
    response_bus = None
    data_bus = None

    wait_data_event = False
    wait_req_event = False

    def __init__(self):
        self.request_bus = ARAT_RequestBus()
        self.response_bus = ARAT_ResponseBus()
        self.data_bus = ARAT_DataBus()

        self.request_bus.enable_input = True
        self.wait_req_event = True

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
        return "ARAT_Bus"

    def tick_run(self):
        self.request_bus.tick_run()
        self.response_bus.tick_run()
        self.data_bus.tick_run()

        if self.request_bus.enable_input and self.request_bus.busy:
            self.request_bus.enable_input = False
            self.wait_data_event = True
            self.wait_req_event = False
            self.data_bus.enable_input = True
            self.data_bus.listen_event_id = self.request_bus.req_event_id
            self.print_driver.print(self.name(), "request bus busy. close request bus input; open data bus input")
        
        if self.data_bus.enable_input and self.data_bus.busy:
            self.data_bus.enable_input = False
            self.wait_data_event = False
            self.print_driver.print(self.name(), "data bus busy. close data bus input")

        if (not self.data_bus.enable_input) and (not self.data_bus.busy) and (not self.request_bus.enable_input):
            self.request_bus.enable_input = True
            self.wait_req_event = True
            self.print_driver.print(self.name(), "data bus done. reopen request bus input")



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

        # if self.request_bus.enable_input and self.request_bus.busy:
            
        #     self.wait_data_event = True
        #     self.wait_req_event = False
            
            
        
        # if self.data_bus.enable_input and self.data_bus.busy:
            
        #     self.wait_data_event = False
        #     self.print_driver.print(self.name(), "data bus busy. close data bus input")

        # if (not self.data_bus.enable_input) and (not self.data_bus.busy) and (not self.request_bus.enable_input):
            
        #     self.wait_req_event = True
        #     self.print_driver.print(self.name(), "data bus done. reopen request bus input")


