import sys
import getopt

import Checksum
import BasicSender
import sys
'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    
    MAX_PACKET_SIZE = 1472
    
    currentMessageType = "start"
    nextPacketData = "WHAT LE FUDGE"
                
    sentPackets = {}   # seqNum : packet
        
    startSize = self.MAX_PACKET_SIZE - sys.getsizeof("start") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
    dataSize = self.MAX_PACKET_SIZE - sys.getsizeof("data") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)        
    endPacketSize = self.MAX_PACKET_SIZE - sys.getsizeof("end") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
        
    # Main sending loop.
    def start(self):
        seqNum = 0      # The packet # that the RECEIVER is expecting
        windowGap = 5   # This is how many "open" spaces we have for more packets
        
        packetList = {}  # Keep track of packets.  We may need to resend. 
                            
        
                             
        startPacket = self.make_packet("start", 0, self.infile.read(startSize))  
        packetList[0] = startPacket
        
        ### TODO: NEED TO TAKE CARE OF THE CASE OF EMPTY FILE

                                        
        self.nextPacketData = self.infile.read(startSize)
        
        if self.nextPacketData == "":
            self.currentMessageType = "end"
        else:
            self.currentMessageType = "data"
        
        # Main loop for sending.
                 
        
                 
                 
        sendLoopCtrl = True
        while(sendLoopCtrl):
            
            nextPacketData = 
            self.send
            
            
            
            
            
            if windowGap == 0:
                sendLoopCtrl = False
         
        
        
        
        
        
        
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
       
    
    # Send the packets to fill up the remaining window
    def sendMyPackets(self, packetsToBeSent):
        for packet in packetsToBeSent:
            if (windowGap == 0):
                break
            else:
                self.send(packet)
                windowGap -= windowGap
                packetsToBeACKed.append(packet)
                packetsToBeSent.remove(packet)
        self.recvMyACKs()        
        
        
    # Cumulatively recv's the ACK's from the receiver and processes them.
    # If we don't know that all the packets have been received, e.g., we still need to loop, call sendMyPackets() 
    def recvMyACKs(self):
        try:
            currentACK = self.receive(0.5)
            while currentACK != None:  # If we get something, then check CHECKSUM
                msg_typeself.split_packet()
                
                Checksum.validate_checksum()
    
    
                currentACK = self.receive(0.5)

        # No ACKs to be received.  Act accordingly.
        except socket.timeout:
            
    # How specific do we have to be?  Check if the fields are numeric?            
    def checkACKPacket(self, packet):
        splitPacket = packet.split("|")
        if len(splitPacket) != 3:
            return False
        elif Checksum.validate_checksum(packet):
            return True

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
