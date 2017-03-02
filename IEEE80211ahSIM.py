
# coding: utf-8

# In[18]:

class Node:
    'Common base class for all nodes'
    '''
    Time unit: slot time = 52
    data rate: 1 Mbps
    '''
    STARTING = 65
    waitDIFS = 564
    waitForACK = 315
    waitNextState = 123
    waitBackoff = 651
    waitTransmit = 213
    READY = 534
    
    nodeCounts = 0
    DEVICE = "node"
    SIFS = 3
    DIFS = 5
    ACKTime = 5
    from random import randint
    
    def __init__(self, x, y, packetLength, samplingRate):
        self.x = x
        self.y = y
        self.packetLength = packetLength
        self.samplingRate = samplingRate
        self.nodeInRange = []
        self.group = -1
        self.state = STARTING
        self.timeToNextTask = DIFS
        self.tranTime = fix((packetLength*8)/52)
        Node.nodeCounts += 1
        
    def sendRequest(self):
        '''
        to AP: send request
        to other nodes: message "transmitting"
        '''
        self.timeToNextTask = Eventlist.currentTime + self.tranTime + SIFS
        self.state = waitForACK
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket(self.timeToNextTask)
        return self
            
    
    def receivePacket(self, dur):
        'receivePacket'
        
    def changeState(self):
        'change state'
        
    def calcRange(self, others):
        if (((self.x- others.x) ** 2) + ((self.y - others.y) ** 2)) <= 1000000:
            self.nodeInRange.append(others)
            others.nodeInRange.append(self)
    
    def displayNodesInRange(self):
        for x in range(len(self.nodeInRange)):
            print self.nodeInRange[x].displayStatus()
        
    def displayStatus(self):
        print "x: %d, y: %d,\nType: %s, group: %d" %(self.x, self.y, self.device, self.group)
                    
    def displayNodeCounts(self):
        print "Total nodes: %d" % Node.nodeCounts
        


# In[14]:

class AP:
    'common access point'
    DIVICE = "access point"
    SIFS = 3
    DIFS = 5
    ACKTime = 5
    
    def __init__(self, x, y, numOfGroup):
        self.x = x
        self.y = y
        self.group = []
        self.state = "grouping"
        self.timeToNextTask = 100000
        for x in range(numOfGroup):
            self.group.append([0])
            
    def receivePacket(self):
        'receivePacket'

    def displayStatus(self):
        print "x: %d, y: %d,\nType: %s, number of group: %d" %(self.x, self.y, self.device, len(self.group))
        


# In[21]:

from random import choice, randint
SIFS = 3
DIFS = 5
ACKTime = 5
RADIUS = 1000
SQUERE_RADIUS = RADIUS ** 2
packetLengthList = [32, 64, 128]
samplingRateList = [2, 4, 8, 16]
points = []
Node.nodeCounts = 0

points.append(AP(0,0,4))

while Node.nodeCounts < 10:
    x, y = randint(-RADIUS,RADIUS), randint(-RADIUS,RADIUS)
    if (x*x + y*y) <= SQUERE_RADIUS:
        points.append(Node(x, y, 32, choice(samplingRateList)))        

for node1 in range(1, len(points)):
    for node2 in range(node1+1, len(points)):
        points[node1].calcRange(points[node2])        
    #points[node1].displayNodesInRange()


# In[29]:

#print points[5].timeToNextTask
print points[:]


# In[3]:

class Eventlist:
    currentTime = 0
    def __init__(self):
        self.event = []
        
    def insert(e):
        Eventlist.event.append(e)
    
    def showList():
        for x in range(len(event)):
            print Eventlist.event[x]
    

