from socket import *
import os
import sys
import struct
import time
import select
import binascii
import statistics
# Should use stdev

ICMP_ECHO_REQUEST = 8


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time() #current time :) Parse
        recPacket, addr = mySocket.recvfrom(1024)
        
        #Fill in start
       
        #Fetch the ICMP header from the IP packet
        icmp_header = recPacket[20:28]
        icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_sequence = struct.unpack('bbHHh', icmp_header)

        ip_header = recPacket[0:20]
        ip_ttl = ip_header[8:9]
        (ttl,) = struct.unpack('B', ip_ttl)

        # ICMP echo response payload starts after the ICMP header.
        data = recPacket[28:]

        # Data contains the time when echo request was sent.
        (timeSent,) = struct.unpack("d", data)

        # If the packet ID of the response matches that of the request,
        # we have received a reply to our ping.
        if icmp_id == ID:
            delay = (timeReceived - timeSent) * 1000
            print("Reply from {}: bytes={} time={}ms TTL={}".format(addr[0], len(data), round(delay, 7), ttl))
            return delay

        #Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time()) #start time  
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)


    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str

    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")


    # SOCK_RAW is a powerful socket type. For more details:   https://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,  	
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    
    #Send ping requests to a server separated by approximately one second
    #Add something here to collect the delays of each ping in a list so you can calculate vars after your ping
    delayList = []

    for i in range(0,4): # Loop four pings that is sent
        delay = doOnePing(dest, timeout)
        if delay is not None:
            delayList.append(delay)        
        time.sleep(1) 
        
    #You should have the values of delay for each ping here; fill in calculation for packet_min, packet_avg, packet_max, and stdev
    if len(delayList) == 0:
        packet_min = 0
        packet_max = 0
        packet_avg = 0
        stdev_var = 0
    else:
        packet_min = min(delayList)
        packet_max = max(delayList)
        packet_avg = sum(delayList) / len(delayList)
        stdev_var = statistics.stdev(delayList)

    vars = [str(round(packet_min, 8)), str(round(packet_avg, 8)), str(round(packet_max, 8)),str(round(stdev_var, 8))]
    print("4 packets are transmitted, packets received: {}, packet loss: {}%".format(len(delayList), round((4.0-len(delayList))/4.0*100, 1)))
    if len(delayList) > 0:
        print("round-trip value for min/avg/max/stddev = {}/{}/{}/{} ms".format(round(packet_min, 2), round(packet_avg, 2), round(packet_max, 2), round(stdev_var, 2)))    
    else:
        print("round-trip min/avg/max/stddev = 0/0.0/0/0.0 ms")
    return vars
    
if __name__ == '__main__':
    ping("google.co.il")
