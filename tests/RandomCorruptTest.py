import random

from BasicTest import *

class AlwaysDropTest(BasicTest):
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            if random.choice([True, False]):
                self.forwarder.out_queue.append(p)
    
        # empty out the in_queue
        self.forwarder.in_queue = []
