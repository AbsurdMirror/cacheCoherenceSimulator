global_event_id = 0

class Event:
    def __init__(self, 
                 type,
                 cmd,
                 requestor,
                 is_data_from_owner = False,
                 broadcast_all = True,
                 recivers = [],
                 data = None,
                 id = None
                ):  
        self.type = type 
        self.cmd = cmd 
        self.requestor = requestor  
        self.is_data_from_owner = is_data_from_owner
        self.broadcast_all = broadcast_all
        self.recivers = recivers
        self.data = data  
        self.inqueue_tick = 0
        if id is None:
            global global_event_id
            self.id = global_event_id
            global_event_id += 1
        else:
            self.id = id
    def print(self):
        print_str = f"[Event:"
        print_str += f" {self.id} |"
        print_str += f" {self.type.name} |"
        print_str += f" {self.cmd.__class__.__name__}.{self.cmd.name} |"

        print_str += f" {self.requestor.name()} ->"
        if self.broadcast_all:
            print_str += " all |"
        else:
            print_str += " ("
            for receiver in self.recivers:
                print_str += receiver.name() + ", "
            print_str += ") |"
        
        print_str += " (D: " + str(self.data) + ") |"

        if self.is_data_from_owner:
            print_str += " (from_owner)"

        print_str += " ]"

        return print_str
