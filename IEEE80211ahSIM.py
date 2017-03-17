
# coding: utf-8

# In[1]:

class Node:
    'Common base class for all nodes'
    '''
    Time unit: slot time = 52
    data rate: 1 Mbps
    '''
    sendPacket = 531 
    waitDIFS = 564 
    waitResponse = 315 #wait for ACK
    countDownBackoff = 615
    channelBusy = 213
    waitOthersACK = 843
    READY = 534
    HALT = 5843
    
    nodeCounts = 0
    packetCount = 0
    DEVICE = "node"
    SIFS = 3
    DIFS = 5
    ACKTime = 5
    from random import randint
    
    def __init__(self, x, y, packetLength, samplingRate, loop):
        self.x = x
        self.y = y
        self.packetLength = packetLength
        self.samplingRate = samplingRate
        self.nodeInRange = []
        self.channelBusyCount = 0
        self.state = Global.waitDIFS
        self.timeToNextTask = Eventlist.currentTime + DIFS
        self.nav = 0
        self.checkACK = 0
        self.backoffStage = 4
        self.backoffTime = randint(0, 2 ** max(self.backoffStage, 10))
        self.tranTime = fix((packetLength*8)/52)
        self.loop = loop
        Node.nodeCounts += 1
        
    def sendPacket(self):
        '''
        to AP: send request
        to other nodes: message "transmitting"
        '''
        Node.packetCount += 1
        self.timeToNextTask = Eventlist.currentTime + self.tranTime
        self.channelState = Node.sendPacket
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket(self.tranTime)
        return self
            
    
    def receivePacket(self, time):
        'Carrier sense'
        if self.channelState == Node.READY: #While sending packet simultaneously
            print "sending packet simultaneously\n"
            return
        if self.channelState == Node.receiveACK:  #collision
            self.checkACK = 0
        self.channelState = Node.channelBusy
        if self.timeToNextTask < (Eventlist.currentTime+ time):
            self.timeToNextTask = Eventlist.currentTime + time
            
        '''rewrite'''    
        self.channelBusyCount += 1
        if self.state != Global.RAEDY:
            self.state = Global.carrierSense
            self.timeToNextTask = Eventlist.maxTime+1
        if self.channelBusyCount >1:
            self.nav = 0
            
        
    def changeState(self):
        "change state when it's the node's turn"
        return {
            sendPacket: self.toWaitResponse(),
            waitResponse: self.toCheckACK(),
            waitDIFS: self.toBackoff(),
            countDownBackoff: self.readyToWork(),
            channelBusy: self.setNav(),
            waitOthersACK: self.toBackoff()            
        }[self.channelState]
    
    def toWaitResponse(self):
        self.channelState = Node.waitResponse
        self.timeToNextTask = Eventlist.currentTime + Global.nav
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].channelBusyCount -= 1
            self.nodeInRange[x].timeToNextTask = Eventlist.currentTime + self.nodeInRange[x].nav
            self.nodeInRange[x].nav = Global.nav
        
    def toCheckACK(self):
        'check whether ACK is transmitted sucessfully'
        'if failed => toBackoff'
        if self.checkACK == 1:
            'transmitted sucessfully'
            if self.loop:
                self.channelState = Node.waitDIFS
                self.timeToNextTask = Eventlist.currentTime + DIFS
            else:
                self.channelState = Node.HALT
                self.timeToNextTask = Eventlist.maxTime+1
        elif self.checkACK == 0:
            Eventlist.collision += 1
            self.collisionTimes += 1
            self.toBackoff()
        
    def readyToWork(self):
        self.backoffStage = 3
        self.backoffTime = 0
        self.channelState = Node.READY
        
    def setNav(self):
        self.nav = SIFS + ACKTime + DIFS
        self.channelState = Node.waitOthersACK
        self.timeToNextTask = Eventlist.currentTime + self.nav
        
    def toBackOff(self):
        self.nav = 0
        self.channelState = Node.countDownBackoff
        if self.backoffTime == 0:
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
        


# In[13]:

class AP:
    'common access point'
    DIVICE = "access point"
    SIFS = 3
    DIFS = 5
    ACKTime = 5
    
    IDLE = 655
    sendPacket = 531 
    channelBusy = 213
    READY = 534
    
    def __init__(self, x, y, numOfGroup):
        self.x = x
        self.y = y
        self.group = []
        self.channelState = AP.IDLE
        self.timeToNextTask = Eventlist.maxTime
        self.nodeInRange = []
        for groups in range(numOfGroup):
            self.group.append([0])
            
            
            
            '''
            需要重寫!
            >>>>>>>因應送封包時收封包
            1.將狀態分為收&送
            '''
    def receivePacket(self, node):
        'receivePacket'
        if self.channelState == AP.IDLE:
            self.channelState = AP.channelBusy
            self.timeToNextTask = Eventlist.currentTime + node.tranTime + SIFS
            self.respondTarget = node
        elif self.channelState == AP.channelBusy:
            'collision'
            self.channelState = AP.IDLE
            self.respondTarget = 0
            self.timeToNextTask = Eventlist.maxTime+1  # wrong!!!
            
    def sendACK(self):
        'send ACK'
        self.timeToNextTask = Eventlist.current + ACKTime
        self.channelState = AP.sendPacket
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket(ACKTime)
        self.respondTarget.checkACK = 1
        
    def changeState(self):
        return {
            IDLE: self.processEnd(),
            sendPacket: self.toIDLE(),
            channelBusy: self.readyToWork(),
        }[self.channelState]
    
    def processEnd(self):
        print "process end"
        return 0
    
    def toIDLE(self):
        self.respondTarget = 0
        self.channelState = IDLE
        self.timeToNextTask = Eventlist.maxTime
        
    def readyToWork(self):
        self.channelState = READY
        
    def calcRange(self, node):
        self.nodeInRange.append(node)

    def displayStatus(self):
        print "x: %d, y: %d,\nType: %s, number of group: %d" %(self.x, self.y, self.device, len(self.group))
        


# In[17]:

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

eventController = Eventlist(1)

points.append(AP(0,0,4))

while Node.nodeCounts < 10:
    x, y = randint(-RADIUS,RADIUS), randint(-RADIUS,RADIUS)
    if (x*x + y*y) <= SQUERE_RADIUS:
        points.append(Node(x, y, 32, choice(samplingRateList),1))        

for node1 in range(1, len(points)):
    points[0].calcRange(points[node1])
    for node2 in range(node1+1, len(points)):
        points[node1].calcRange(points[node2])        
    #points[node1].displayNodesInRange()
    
while(Eventlist.currentTime < Eventlist.maxTime):
    


# In[23]:

#print points[5].timeToNextTask
print points[:]


# In[15]:

class Eventlist:
    from numpy import *
    currentTime = 0
    collision = 0
    maxTime = 0
    def __init__(self, endTime):
        self.event = []
        self.workList = []
        Eventlist.maxTime = fix(endTime*1000000/52)
        self.nextTime = Eventlist.maxTime
        
        
    def insert(self, e):
        self.event.append(e)
        
    def findNextTimeEvents(self, points):
        for pointCount in range(len(points))
            if self.nextTime > points[pointCount].timeToNextTask:
                self.nextTime = points[pointCount].timeToNextTask
                self.event = [points[pointCount]]
            elif self.nextTime == points[pointCount].timeToNextTask:
                self.event.append(points[pointCount])
    
    def goToNextTime(self):
        self.currentTime = self.nextTime
        self.nextTime = Eventlist.maxTime
        
    def changeState(self):
        for x in range(len(event)):
            event[x].changeState()
            if event[x].state == Node.READY:
                self.workList.append(event[x])
            
    def checkAP(self):
        
    
    def showList():
        for x in range(len(event)):
            print Eventlist.event[x]
    


# In[1]:

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

class Global:
    SIFS = 3
    DIFS = 5
    ACKTime = 5
    sendPacket = 531 
    waitDIFS = 564 
    waitResponse = 315 #wait for ACK
    countDownBackoff = 615
    channelBusy = 213
    waitOthersACK = 843
    READY = 534
    HALT = 5843
    collision = 0
    IDLE = 655

