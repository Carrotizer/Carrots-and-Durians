import sys
import getopt

import Checksum
import BasicSender
import sys
'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    # Main sending loop.
    def start(self):
        window = 5
        window_offset = 0
        pack_list  = []  
        
        seqno = 0
        msg_type = 'start'
        data_size = 1472 - sys.getsizeof(0xffffffff) - sys.getsizeof(msg_type) - sys.getsizeof(seqno)
        data = self.infile.read(data_size)
        start_packet = self.make_packet(msg_type, seqno, data)
        pack_list.append(start_packet)
        queue_packets = 1
        
        #send start packet and wait for response??
        
        #make next 4 packets
         
        msg_type = 'data'
        while(queue_packets < window and not (data == '')):
            data_size = 1472 - sys.getsizeof(0xffffffff) - sys.getsizeof(msg_type) - sys.getsizeof(seqno + 1)
            data = self.infile.read(data_size)
            if (data == ''):
                break
            seqno+=1
            pack_list.append(self.make_packet(msg_type, seqno, data))
            queue_packets+=1
        
        for packet in pack_list:
            self.send(packet)
            
        #wait for response
        while(not (msg_type == 'end')):
            response_packet = self.receive()
            if Checksum.validate_checksum(response_packet):
                next_seqno= response_packet.split("|")[1]
                if(next_seqno == seqno + 1):
                    data_size = 1472 - sys.getsizeof(0xffffffff) - sys.getsizeof(msg_type) - sys.getsizeof(seqno + 1)
                    data = self.infile.read(data_size)
                    if (data == ''):
                        msg_type = 'end'
                    seqno+=1
                    packet = self.make_packet(msg_type, seqno, data)
                    window_offset +=1
                    pack_list.pop(0)
                    pack_list.append(packet)
                    self.send(packet)
                else:
                    #resend all of the packets from next_seqno to end of window??  not sure this will solve every case
                        
                    
        

'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:d", ["file=", "port=", "address=", "debug="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True

    s = Sender(dest,port,filename,debug)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
