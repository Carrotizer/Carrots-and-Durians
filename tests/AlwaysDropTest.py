from BasicTest import *

class AlwaysDropTest(BasicTest):
    def handle_packet(self):
        self.forwarder.out_queue = []
        # empty out the in_queue
        self.forwarder.in_queue = []