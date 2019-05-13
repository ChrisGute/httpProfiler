import socket 
import ssl
import ipaddress
from urlparse import urlparse
import datetime
from datetime import timedelta
import json
import time

def validIP(ip):
    ip = unicode(ip)
    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False

def validPort(port):
    try:
        port = int(port)
        if port >= 0 and port <= 65535:
            return True
        else:
            return False
    except:
        return False 

def getSocket(ip, port, use_ssl=False, socket_timeout=4, connection_retries=2):
    '''
    Returns a socket after connecting to the host

    ip
        String IP address for connection

    port
        Int port to use for connection

    use_ssl
        Try and connect using ssl wrapper. Required for https

    socket_timeout
        How long to wait before connecting to the socket

    connection_retries
        How many times to retry connecting
    '''
    if not validPort(port):
        print("Port {} not valid".format(port))
        return False
    if not validIP(ip):
        print("IP not valid: {}".format(ip))
        return False

    # Define socket 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(socket_timeout)

    if use_ssl:
        # Wrap socket with SSL
        s = ssl.wrap_socket(s)

    while connection_retries > 0:
        try:
            s.connect((ip, int(port)))
            return s
        except socket.timeout:
            print('Socket timed out')
            return False
        except:
            raise

        connection_retries -= 1

def getIP(d):
    '''
    This method returns the first IP address string
    that responds as the given domain name

    d
        domain name you want to look up
    '''
    try:
        return socket.gethostbyname(d)
    except:
        return False

def sendData(s, data):
    '''
    Try to send data do a socket

    s
        Connected socket
    data
        String data to send over the socket
    '''
    try:
        s.sendall(data)
        return True
    except:
        print('Failed to send data')
        return False

# TODO
def parseData(samples):
    buckets={}
    bucketms=15
   
    # Store the data as sample buckets
    startTime = samples[0][0]
    print 'StartTime:', startTime
    endTime = samples[-1][0]
    print 'EndTime:', endTime

    bucketEnd = startTime + timedelta(milliseconds=bucketms)
    buckets[unicode(bucketEnd)] = 0

    # Chcek each sample to see what bucket it belongs in
    for sample in samples:
        # If the current samples time is larger that the bucket
        # window we know that we have entered a new bucket
        if sample[0] > bucketEnd:
            # Make a new bucket "bucketms" in the future
            bucketEnd = bucketEnd + timedelta(milliseconds=bucketms)
            buckets[unicode(bucketEnd)] = 0

        # Add the bits to the bucket
        buckets[unicode(bucketEnd)] += int(sample[1])


    timeMultiplayer = 1000 / bucketms
    bucketsMbps = {}
    for timeStamp, bits in buckets.items():
        mbps = (bits*timeMultiplayer)/1024.0/1024.0
        bucketsMbps[timeStamp] = {
            'bits': bits,
            'Mbps': round(mbps, 2)
        }
    return bucketsMbps

# TODO
def timedRecv(s):
    samples = []
    while 1:
        data = s.recv(100000)
        if not data: 
            break
        t = datetime.datetime.now()

        samples.append((t, len(data)*8))
        #print "received data {} bits {}".format(len(data)*8, time.time())

        # Sleep ms 1/1000 of a sec
        time.sleep(0.001)
    
    #for sample in samples:
    #    print sample
    #print json.dumps(parseData(samples), indent=4, sort_keys=True)
    return parseData(samples)
    
def httpGet(url):
    # Parse Url into parts
    pUrl = urlparse(url)

    ip = getIP(pUrl.netloc)

    # Get socket 
    if pUrl.scheme == 'https':
        s = getSocket(ip, 443, use_ssl=True)
    else:
        s = getSocket(ip, 80)
    
    if s == False:
        print('Failed to get socket for {}'.format(pUrl.netloc))
        return False

    # Remove protocal and domain
    stripString = '{}://{}'.format(pUrl.scheme, pUrl.netloc)
    getPath = pUrl.geturl().replace(stripString, '', 1)

    # Get string for the request
    getString='GET {} HTTP/1.1\r\n'.format(
        getPath
    )

    # Headeds for for the get request
    headers = [
        'Host: {}'.format(pUrl.netloc),
        'User-Agent: PyPerf/0.1'
    ]

    # Build get request 
    getReqString = getString + "\r\n".join(headers) + '\r\n\r\n'

    # Send request
    sendData(s, getReqString)

    # Get the timed data responce
    d = timedRecv(s)
    s.close()

    for time_stamp in d:
        print time_stamp, ",", d[time_stamp]['Mbps']



httpGet('http://https://www.lipsum.com/')
