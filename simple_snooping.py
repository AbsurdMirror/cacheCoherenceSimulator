
class RequestBus(BaseBus):
    def name(self):
        return "RequestBus"
    
    def select_arbit(self):
        selected_event = None
        selected_node = None
        for node in self.connected_nodes:
            if len(node.req_queue) > 0:
                if selected_event is None:
                    selected_event = node.req_queue[0]
                    selected_node = node
                elif node.req_queue[0].inqueue_tick < selected_event.inqueue_tick:
                    selected_event = node.req_queue[0]
                    selected_node = node

        if selected_event is not None:
            selected_node.req_queue.pop(0)
            return selected_event

class ResponseBus(BaseBus):
    def name(self):
        return "ResponseBus"
    
    def select_arbit(self):
        selected_event = None
        selected_node = None
        for node in self.connected_nodes:
            if len(node.resp_queue) > 0:
                if selected_event is None:
                    selected_event = node.resp_queue[0]
                    selected_node = node
                elif node.resp_queue[0].inqueue_tick < selected_event.inqueue_tick:
                    selected_event = node.resp_queue[0]
                    selected_node = node

        if selected_event is not None:
            selected_node.resp_queue.pop(0)
            return selected_event

