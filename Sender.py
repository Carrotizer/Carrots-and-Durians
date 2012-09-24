import sys
import getopt

import Checksum
import BasicSender
import socket
'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    
    DEBUG = True
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
        packetList = {}  # Keep track of packets.  We may need to resend. 
                                        
        startPacket = self.make_packet("start", 0, self.infile.read(self.startSize))  
        packetList[0] = startPacket
        
        ### TODO: NEED TO TAKE CARE OF THE CASE OF EMPTY FILE
        
        if self.DEBUG:
            print "Made start packet"
                                        
        self.nextPacketData = self.infile.read(self.dataSize)
        
        if self.nextPacketData == "":
            if self.DEBUG:
                print "Special case: one packet only!"
            self.currentMessageType = "end"
            #handle this case!!
        else:
            self.currentMessageType = "data"
        
        
        # Main loop for sending.                      
        sendLoopCtrl = True
        next_expected_seqno = 0
        if self.DEBUG:
            print "Entering loop"
        while(sendLoopCtrl):
            #check if last packet has been sent and acked
            try:
                if self.DEBUG:
                    if(next_expected_seqno > 0):
                        print "Testing packet", next_expected_seqno-1, " for end: ",  packetList[next_expected_seqno-1].split("|")[0]
                if (next_expected_seqno > 0 and packetList[next_expected_seqno-1].split('|')[0] == "end"):
                    if self.DEBUG:
                        print "Last packet ACKed"
                    sendLoopCtrl = False
            except KeyError:
                noop = 1
            
            #If not done, continue sending new packets 
            packetsToBeSent = self.makePackets(packetList, next_expected_seqno, self.WINDOW_SIZE)
            for packet in packetsToBeSent:
                self.send(packet)


            if self.DEBUG:
                print "Listening for ACKs"
            #listen for ACKs
            seqno_list = self.recvMyACKs()
            if not(seqno_list == []):
                next_expected_seqno = int(max(seqno_list))
                if self.DEBUG:
                    print "ACK seqnos returned: ", seqno_list
            else:
                if self.DEBUG:
                    print "seqno_list: ", seqno_list
            
            
                    
    def makePackets(self, existingPackets, startNumber, numPackets):
        packetList = [] 
        for seqno in range(0,numPackets):
            seqno +=startNumber
            try:
                packet = existingPackets[seqno]
            except KeyError:
                #create the packet if it doesn't already exist
                packetData = self.nextPacketData
                if(not self.currentMessageType == "end"):
                    self.nextPacketData = self.infile.read(self.dataSize)
                if self.nextPacketData == "":
                    self.currentMessageType = "end"
                packet = self.make_packet(self.currentMessageType, seqno, packetData)
                existingPackets[seqno] = packet
                packet = existingPackets[seqno] 
                
            packetList.append(packet)
            
            #check to see if packet is end packet, in which case break out of the loop
            msg_type = packet.split('|')[0]
            if msg_type == 'end':
                break
        if self.DEBUG:
            print "Sending ", len(packetList), " packets, starting with number ", startNumber 
        return packetList      
                
    # Cumulatively recv's the ACK's from the receiver and processes them.
    # If we don't know that all the packets have been received, e.g., we still need to loop, call sendMyPackets() 
    def recvMyACKs(self):
        ACKlist = []
        currentACK = self.receive(0.5)
        while currentACK != None:  # If we get something, then check CHECKSUM
            if Checksum.validate_checksum(currentACK):
                msg_type, seqno, checksum = currentACK.split('|')
                ACKlist.append(seqno) #put the next expected packet number in the list
            
            #wait for next packet    
            currentACK = self.receive(0.5)

        # No ACKs to be received.  Act accordingly.
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
