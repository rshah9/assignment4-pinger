from socket import *
import os
import sys
import struct
import time
import select
import binascii
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

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Fill in start

        # Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]
        type, code, checksum, id, sequence = struct.unpack(
            "bbHHh", icmpHeader)
        if type != ICMP_ECHO_REQUEST: #not
            payloadSize = struct.calcsize("d")
            payload = struct.unpack("d", recPacket[28:28+payloadSize])
            timeStamp = payload[0] #time.time()
            ttl = timeReceived - timeStamp
            return ttl  # Return the time taken to get the response

#         if type != 0:
#             return 'expected type=0, but got {}'.format(type)
#         if code != 0:
#             return 'expected type=0, but got {}'.format(code)
#         if ID != id:
#             return 'expected id={}, but got {}'.format(ID, id)
#         send_time = struct.unpack("d", recPacket[28:36])[0]
#
#         rtt = (timeReceived - send_time) * 1000
#         rtt_count += 1
#         rtt_sum += rtt
#         rtt_stdev = (rtt_sum / rtt_count) - rtt
#         rtt_min = min(rtt_min, rtt)
#         rtt_max = max(rtt_max, rtt)
#         rtt_avg = rtt_sum / rtt_count
#         ip_header = struct.unpack('!BBHHHBBH4s4s', recPacket[:20])
#         ttl = ip_header[2]
#         saddr = socket.inet_ntoa(ip_header[8])
#         length = len(recPacket) - 20
#
#         return '{} bytes from {}: icmp_seq={} ttl={} time={:.3f} ms'.format(
#             length, saddr, sequence, ttl, rtt)


        # Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
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


    # SOCK_RAW is a powerful socket type. For more details:   http://sockraw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,  	# the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Calculate vars values and return them
    #  vars = [str(round(packet_min, 2)), str(round(packet_avg, 2)), str(round(packet_max, 2)),str(round(stdev(stdev_var), 2))]
    # Send ping requests to a server separated by approximately one second
    for i in range(0,4):
        delay = doOnePing(dest, timeout)
        print(delay)
        time.sleep(1)  # one second

    return vars

if __name__ == '__main__':
    ping("google.co.il")