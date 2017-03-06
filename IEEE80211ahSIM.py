
# coding: utf-8

# In[85]:

class Node:
    'Common base class for all nodes'
    '''
    Time unit: slot time = 52
    data rate: 1 Mbps
    '''
    sendRequest = 531 
    waitDIFS = 564 
    waitResponse = 315 #wait for ACK
    countDownBackoff = 615
    channelBusy = 213
    waitOthersACK = 843
    READY = 534
    waitNextState = 123 #part 1 end
    
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
        self.state = Node.waitDIFS
        self.timeToNextTask = Eventlist.currentTime + DIFS
        self.nav = 0
        self.backoffStage = 3
        self.backoffTime = 0
        self.tranTime = fix((packetLength*8)/52)
        Node.nodeCounts += 1
        
    def sendRequest(self):
        '''
        to AP: send request
        to other nodes: message "transmitting"
        '''
        self.timeToNextTask = Eventlist.currentTime + self.tranTime + SIFS
        self.state = Node.sendRequest
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket(self.tranTime)
        return self
            
    
    def receivePacket(self, time):
        'receivePacket'
        if self.state == Node.READY:
            continue
        self.state = Node.waitTransmit
        self.timeToNextTask = Eventlist.currentTime + time
        
    def changeState(self):
        'change state'
        return {
            sendRequest: self.toWaitResponse(),
            waitResponse: self.toCheckACK(),
            waitDIFS: self.readyToWork(),
            countDownBackoff: self.readyToWork(),
            channelBusy: self.setNav(),
            waitOthersACK: self.toBackoff()            
        }[self.state]
    
    def toWaitResponse(self):
        self.state = Node.waitResponse
        self.timeToNextTask = Eventlist.currentTime + ACKTime
        
    def toCheckACK(self):
        'check whether ACK is transmitted sucessfully'
        'if failed => toBackoff'
        'if success => part 1 end'
        
    def readyToWork(self):
        self.state = Node.READY
        
    def setNav(self):
        self.nav = SIFS + ACKTime
        self.state = waitOthersACK
        self.timeToNextTask = Eventlist.currentTime + self.nav
        
    def toBackOff(self):
        self.nav = 0
        self.state = countDownBackoff
        if self.backoffTime = 0:
            self.backoffStage += 1
            self.backoffTime = randint(0, 2 ** max(self.backoffStage, 10))
            self.timeToNextTask = Eventlist.currentTime + self.backoffTime
        else:
            self.timeToNextTask = Eventlist.currentTime + self.backoffTime
        
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
        


# In[6]:

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
        


# In[13]:

from random import choice, randint
from numpy import *
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


# In[14]:

#print points[5].timeToNextTask
print points[:]


# In[15]:

class Eventlist:
    currentTime = 0
    def __init__(self):
        self.event = []
        
    def insert(e):
        Eventlist.event.append(e)
    
    def showList():
        for x in range(len(event)):
            print Eventlist.event[x]
    


# In[84]:

class Test:
    var = 'a'
    def __init__(self, x):
        self.x = x
        
    def find(self, value):
        return {
          'a': lambda x: x + 5,
        }[value]
        #print result
        
    def exec_a(self):
        print "execute a"
        self.x = 0
    
    def do(self, node):
        node.find('a')
        
test1 = Test(1)
test2 = Test(2)
test1.do(test2)
print test1.x
print test2.x


# In[ ]:



