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
        
    startSize = MAX_PACKET_SIZE - sys.getsizeof("start") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
    dataSize = MAX_PACKET_SIZE - sys.getsizeof("data") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)        
    endSize = MAX_PACKET_SIZE - sys.getsizeof("end") - 3*sys.getsizeof("|") - sys.getsizeof(0) - sys.getsizeof(0xffffffff)
    
    currentMessageType = "start"
    currentMessageSize = dataSize   # We manually read in start packet.  This needs to change to endSize at appropriate times.
    currentPacketData = "FUDGE FUDGE FUDGE"
    nextPacketData = "WHAT LE FUDGE"
        
    packetList = {}  # Keep track of packets.  We may need to resend.
    input_complete = False # True only if we have read everything.  No need to make new packets.
    last_seq_num = -1   # seq_num of the 'end' packet
    current_seq_num = 0   # seqNum to SEND
    
    numSentPackets = 0
    
    # Main sending loop.
    def start(self):
        if self.DEBUG:
            print "Starting..."
            
        packetsToBeSent = []
        
        self.currentPacketData = self.infile.read(self.startSize)
        self.nextPacketData = self.infile.read(self.dataSize) 
        startPacket = self.make_packet(self.currentMessageType, self.current_seq_num, self.currentPacketData)
        self.packetList[0] = startPacket
        packetsToBeSent.append(startPacket)
        self.updateAndCheck()
        
        ### NEED TO TAKE CARE OF SPECIAL CASE
        

        # Manually make the first batch                
        while len(self.packetList) < 5:
            self.packetList[self.current_seq_num] = self.make_packet(self.currentMessageType, self.current_seq_num, self.currentPacketData)
            packetsToBeSent.append(self.make_packet(self.currentMessageType, self.current_seq_num, self.currentPacketData))
            self.updateAndCheck()     
        
        # Main loop for sending.                      
        sendLoopCtrl = True
        next_expected_seqno = 0
        
        while(sendLoopCtrl):
            if self.DEBUG:
                print "NOTICE: current_seq_num: %d. Sending %d packets.  last_seq_num = %d " % (self.current_seq_num, len(packetsToBeSent), self.last_seq_num)
            
            #send packets
            for packet in packetsToBeSent:
                self.send(packet)
                self.numSentPackets += 1
                if self.DEBUG:
                    temp_packet_num = -1
                    for key in self.packetList:
                        if self.packetList[key] == packet:
                            temp_packet_num = key
                    print "Sent packet #%d (%d byes)" % (temp_packet_num     , sys.getsizeof(packet))
            
            #listen for ACKs
            if self.DEBUG:
                print "NOTICE: Listening for ACKs..."
            seqno_list = self.recvMyACKs()
            if not seqno_list:  # if the list is empty
                if self.DEBUG:
                    print "Received NO ACK's.  Resending current packets......"
                
                continue        # resend the same packets
            
            #check if last packet has been sent and ACKed
            next_expected_seqno = max(seqno_list)
            
            if self.last_seq_num == next_expected_seqno - 1:
                if self.DEBUG:
                    print "Last packet ACKed.  End packet # is: %d" % self.last_seq_num
                    print "Sent %d total packets." % self.numSentPackets
                sendLoopCtrl = False
                break
            else:   #If not done, continue sending new packets 
                packetsToBeSent = self.makeNextBatch(next_expected_seqno, self.WINDOW_SIZE)

    
            
    '''
    Reads in the next data to update nextPacketData
    Check if the next input line is empty.  
    Update current message type if necessary
    ASSUMES that 'end' packet has not yet been reached.  If it has, then you are screwed.
    '''
    def updateAndCheck(self):
        self.currentPacketData = self.nextPacketData[:]
        self.nextPacketData = self.infile.read(self.currentMessageSize)
        if not self.nextPacketData: # if it's ""
            if self.DEBUG:
                print "CURRENT PACKET SHOULD BE THE LAST ONE.  current_seq_num: %d" % self.current_seq_num
            self.currentMessageType = "end"
            #self.currentMessageSize = endSize
            self.last_seq_num = self.current_seq_num
        else:
            self.current_seq_num += 1
                                        
    
    '''
    Input: seq_num of last ACK , how many packets to send
    Returns the list of next batch of packets to be sent
    '''
    def makeNextBatch(self, startNumber, numPackets):
        batchToSend = []
        
        if self.input_complete: # All the input is complete.  Just send all packets from startNum to max.
            for seq_num in range(startnumber, max(self.packetList.keys()) + 1):
                batchToSend.append(self.packetList[seq_num])
        else:   # We didn't read all the packets yet
         
            # First add all the packets that we have
            for seq_num in range(startNumber, max(self.packetList.keys()) + 1):
                batchToSend.append(self.packetList[seq_num])
            
            # If we need to throw in more packets, do so now.
            while len(batchToSend) < 5 and self.current_seq_num <= self.last_seq_num:
                new_packet = self.make_packet(self.currentMessageType, self.current_seq_num, self.currentPacketData)
                self.packetList[self.current_seq_num] = new_packet
                batchToSend.append(new_packet)
                self.updateAndCheck()
                 
            if self.DEBUG:
                batchKeys = []
                for packet in batchToSend:
                    for key in self.packetList.keys():
                        if self.packetList[key] == packet:
                            batchKeys.append(key) 
                    
                print "Sending %s" % batchKeys 
                
            return batchToSend   
        
    '''            
    # Cumulatively recv's the ACK's from the receiver and processes them.
    # If we don't know that all the packets have been received, e.g., we still need to loop, call sendMyPackets()
    ''' 
    def recvMyACKs(self):
        ACKlist = []
        currentACK = self.receive(0.5)
        while currentACK != None:  # If we get something, then check CHECKSUM
            temp = currentACK.split("|")
            if not (len(temp) == 3 and temp[1].isdigit() and temp[2].isdigit() and temp[0] == "ack"):  # ignore
                if self.DEBUG:
                    print "Disregarding corrupted packet: %s" % currentACK
                currentACK = self.receive(0.5)
                continue
            
            if Checksum.validate_checksum(currentACK):
                msg_type, seqno, checksum = currentACK.split('|')
                ACKlist.append(seqno) #put the next expected packet number in the list
            elif self.DEBUG:
                print "Received corrupted packet.  Disregarding."
            
            #wait for next packet    
            currentACK = self.receive(0.5)


        ACKlist = map(int, ACKlist)
        
        if self.DEBUG:
            print "Received %d ACK's.  Highest is %d: the receiver has everything to %d" % (len(ACKlist), max(ACKlist) if ACKlist else -1, max(ACKlist)-1 if ACKlist else -1)

        # No ACKs to be received.  Act accordingly.
        if ACKlist:
            for key in self.packetList.keys():    # Cleaning up packets stored
                if key < max(ACKlist) and len(self.packetList) > 1:
                    del self.packetList[key]
            
        return ACKlist
    
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
