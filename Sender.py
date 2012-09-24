import sys
import getopt

import Checksum
import BasicSender
import socket
'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    
    DEBUG = False
    MAX_PACKET_SIZE = 1472
    WINDOW_SIZE = 5
    
    currentMessageType = "start"
    nextPacketData = "WHAT LE FUDGE"
        
    startSize = MAX_PACKET_SIZE - sys.getsizeof("start") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
    dataSize = MAX_PACKET_SIZE - sys.getsizeof("data") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)        
    endPacketSize = MAX_PACKET_SIZE - sys.getsizeof("end") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
        
    self.packetList = {}  # Keep track of packets.  We may need to resend.
    self.input_complete = False # True only if we have read everything.  No need to make new packets.
    
    # Main sending loop.
    def start(self):
        startPacket = self.make_packet("start", 0, self.infile.read(self.startSize))  
        self.packetList[0] = startPacket
                
        if self.DEBUG:
            print "Made start packet"
                                        
        self.nextPacketData = self.infile.read(self.dataSize)
        
        if self.nextPacketData == "":
            if self.DEBUG:
                print "Special case: one packet only!"
            self.currentMessageType = "end"
        else:
            self.currentMessageType = "data"
        
        # Main loop for sending.                      
        sendLoopCtrl = True
        next_expected_seqno = 0
        
        while(sendLoopCtrl):
            
            #check if last packet has been sent and ACKed
            if self.lastPacketACKed(self.packetList, next_expected_seqno-1):
                if self.DEBUG:
                    print "Last packet ACKed"
                sendLoopCtrl = False
            
            else:#If not done, continue sending new packets 
                packetsToBeSent = self.makePackets(selfpacketList, next_expected_seqno, self.WINDOW_SIZE)
                
                #send packets
                for packet in packetsToBeSent:
                    self.send(packet)
    
                #listen for ACKs
                if self.DEBUG:
                    print "Listening for ACKs"
                seqno_list = self.recvMyACKs()
                
                #find out the highest ACKed packet.  If we have no ACK's, then we need to resend last batch
                # NOTE: empty list, in Python, is False, boolean-wise
                if seqno_list:
                    next_expected_seqno = int(max(seqno_list))
                    if self.DEBUG:
                        print "ACK seqnos returned: ", seqno_list
                
    '''
    Input: current list of packets, seqno of last packet to be ACK'ed
    Used to stop the loop once we get an ACK from the receiver for the 'end' packet
    '''
    def lastPacketACKed(self, packetList, last_acked):
        try:
            if self.DEBUG:
                if(last_acked > 0):
                    print "Testing packet", last_acked, " for end.  Msg_type: ",  packetList[last_acked].split("|")[0]
            if (last_acked > 0 and packetList[last_acked].split('|')[0] == "end"):
                return True
            return False
        except KeyError:
            return False
    
    
    '''
    Input: seq_num of last ACK , how many packets to send
    Returns the list of next batch of packets to be sent
    '''
    def makePackets(self, startNumber, numPackets):
        packetListToSend = [] 
        for seqno in range(0,numPackets):
            seqno += startNumber
            try:
                packet = self.packetList[seqno] # some packets may need to be resent
            except KeyError:
                # create the packet if it doesn't already exist
                packetData = self.nextPacketData
                if (not self.currentMessageType == "end"):
                    self.nextPacketData = self.infile.read(self.dataSize)
                else:
                    # Check if the last packet in the list is already an end packet
                    if packetList[max(packetList.keys())].split('|')[0] == 'end':
                        
                    
                    
                if self.nextPacketData == "":
                    self.currentMessageType = "end"
                packet = self.make_packet(self.currentMessageType, seqno, packetData)
                self.packetList[seqno] = packet
                
            packetListToSend.append(packet)
            
            #check to see if packet is end packet, in which case break out of the loop
            if packet.split('|')[0] == "end":
                break
            
        if self.DEBUG:
            print "Sending ", len(packetListToSend), " packets, starting with number ", startNumber 
        return packetListToSend   
    
    '''            
    # Cumulatively recv's the ACK's from the receiver and processes them.
    # If we don't know that all the packets have been received, e.g., we still need to loop, call sendMyPackets()
    ''' 
    def recvMyACKs(self):
        ACKlist = []
        currentACK = self.receive(0.5)
        while currentACK != None:  # If we get something, then check CHECKSUM
            if Checksum.validate_checksum(currentACK):
                msg_type, seqno, checksum = currentACK.split('|')
                ACKlist.append(seqno) #put the next expected packet number in the list
            elif self.DEBUG:
                print "Received corrupted packet.  Disregarding."
            
            #wait for next packet    
            currentACK = self.receive(0.5)

        # No ACKs to be received.  Act accordingly.
        return ACKlist

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
