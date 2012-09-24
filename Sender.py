import sys
import getopt

import Checksum
import BasicSender
import socket
'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    
    MAX_PACKET_SIZE = 1472
    WINDOW_SIZE = 5
    
    currentMessageType = "start"
    nextPacketData = "WHAT LE FUDGE"
                
    sentPackets = {}   # seqNum : packet
        
    startSize = MAX_PACKET_SIZE - sys.getsizeof("start") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
    dataSize = MAX_PACKET_SIZE - sys.getsizeof("data") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)        
    endPacketSize = MAX_PACKET_SIZE - sys.getsizeof("end") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
        
    # Main sending loop.
    def start(self):
        seqNum = 0      # The packet # that the RECEIVER is expecting
        windowGap = 5   # This is how many "open" spaces we have for more packets
        
        packetList = {}  # Keep track of packets.  We may need to resend. 
                            
        
                             
        startPacket = self.make_packet("start", 0, self.infile.read(self.startSize))  
        packetList[0] = startPacket
        
        ### TODO: NEED TO TAKE CARE OF THE CASE OF EMPTY FILE

                                        
        self.nextPacketData = self.infile.read(self.dataSize)
        
        if self.nextPacketData == "":
            self.currentMessageType = "end"
        else:
            self.currentMessageType = "data"
        
        #send first round of packets
        packetsToBeSent = self.makePackets(packetList, 0, self.WINDOW_SIZE)
        for packet in packetsToBeSent:
            self.send(packet)
        
        # Main loop for sending.                      
        sendLoopCtrl = True
        while(sendLoopCtrl):
            
            #listen for ACKs
            seqno_list = self.recvMyACKs()
            next_expected_seqno = max(seqno_list)
            
            
            #check if last packet has been sent and acked
            if (not (packetList[next_expected_seqno-1] == None)) and (self.split_packet(packetList[next_expected_seqno-1])[0] == "end"):
                sendLoopCtrl = False
            
            #If not done, continue sending new packets 
            else:
                packetsToBeSent = self.makePackets(packetList, next_expected_seqno, self.WINDOW_SIZE)
                for packet in packetsToBeSent:
                    self.send(packet)

                    
    def makePackets(self, existingPackets, startNumber, numPackets):
        packetList = [] 
        for seqno in range(0,numPackets):
            seqno +=startNumber
            if(existingPackets[seqno] == None): #create the packet if it doesn't already exist
                packetData = self.nextPacketData
                self.nextPacketData = self.infile.read(self.dataSize)
                if self.nextPacketData == "":
                    self.currentMessageType = "end"
                packet = self.make_packet(self.currentMessageType, seqno, packetData)
                existingPackets[seqno] = packet
                
            packet = existingPackets[seqno] #get the packet from dictionary and add it to send list
            packetList.append(existingPackets[seqno])
            
            #check to see if packet is end packet, in which case break out of the loop
            msg_type, seqno, data, checksum = self.split_packet(packet)
            if msg_type == 'end':
                break
        return packetList
        
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
        ACKlist = []
        try:
            currentACK = self.receive(0.5)
            while currentACK != None:  # If we get something, then check CHECKSUM
                if Checksum.validate_checksum(currentACK):
                    msg_type, seqno, data, checksum = self.split_packet(currentACK)
                    ACKlist.append(seqno) #put the next expected packet number in the list
                
                #wait for next packet    
                currentACK = self.receive(0.5)

        # No ACKs to be received.  Act accordingly.
        except socket.timeout:
            return ACKlist
            
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
