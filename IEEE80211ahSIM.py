
# coding: utf-8

# In[12]:

class Node:
    'Common base class for all nodes'
    '''
    Time unit: slot time = 52
    data rate: 1 Mbps
    '''
    
    #nodeCounts = 0
    #packetCount = 0
    DEVICE = "node"
    
    from random import randint
    
    def __init__(self, x, y, packetLength, samplingRate, AID):
        self.x = x
        self.y = y
        self.packetLength = packetLength
        self.samplingRate = samplingRate
        self.nodeInRange = []
        self.channelBusyCount = 0
        self.state = Global.waitDIFS
        self.timeToNextTask = Global.currentTime + DIFS
        self.nav = Global.nav
        self.checkACK = 0
        self.backoffStage = Global.contentionWindow
        self.backoffTime = 0#randint(0, 2 ** min(self.backoffStage, 10))
        self.tranTime = fix((packetLength*8)/52)
        self.queuingData = 9999#randint(0, 1000)
        self.collision = 0
        self.AID = AID
        self.transmittTimes = 0
        Global.nodeCounts += 1
        
    def sendPacket(self):
        '''
        to AP: send request
        to other nodes: message "transmitting"
        '''
        Statistic.packetCount += 1
        self.transmittTimes += 1
        self.timeToNextTask = Global.currentTime + self.tranTime
        self.state = Global.sendPacket
        print "Node: %d, send packet" % self.AID
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket()
        return self
            
    
    def receivePacket(self):
        'Carrier sense'
        '''if self.state == Node.READY: #While sending packet simultaneously
            print "sending packet simultaneously\n"
            return
        if self.state == Node.receiveACK:  #collision
            self.checkACK = 0
        self.state = Node.channelBusy
        if self.timeToNextTask < (Global.currentTime+ time):
            self.timeToNextTask = Global.currentTime + time'''
            
        '''rewrite'''    
        self.channelBusyCount += 1
        if (self.state == Global.waitDIFS) or (self.state == Global.backoff):
            if self.state == Global.backoff:
                self.backoffTime = self.backoffTime - (Global.currentTime - self.backoffStartTime)
            self.state = Global.carrierSense
            #print "Node: %d, carrier sense" % self.AID
            self.timeToNextTask = Eventlist.maxTime+1
        if self.channelBusyCount >1:
            self.nav = 0
            self.checkACK = 0
            
        
    def changeState(self):
        "change state when it's the node's turn"
        '''
        return {
            Global.sendPacket: self.toWaitResponse(),  
            Global.waitResponse: self.toCheckACK(),
            Global.waitDIFS: self.toBackoff(),  
            Global.backoff: self.readyToWork(),        
        }[self.state]'''
        if self.state == Global.sendPacket:
            return self.toWaitResponse()
        elif self.state == Global.waitResponse:
            return self.toCheckACK()
        elif self.state == Global.waitDIFS:
            return self.toBackoff()
        elif self.state == Global.backoff:
            return self.readyToWork()
    
    def toWaitResponse(self):
        self.state = Global.waitResponse
        print "Node: %d, wait response" % self.AID
        self.timeToNextTask = Global.currentTime + Global.nav
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].channelUserDecrease()
            
    def channelUserDecrease(self):
        self.channelBusyCount -= 1
        if (self.channelBusyCount < 1) and (self.state == Global.carrierSense):
            #print "Node: %d, carrier sense over,  backoff time: %d" % (self.AID, self.backoffTime)
            self.state = Global.waitDIFS
            self.timeToNextTask = Global.currentTime + self.nav + Global.DIFS
            self.nav = Global.nav
        
        
    def toCheckACK(self):
        'check whether ACK is transmitted sucessfully'
        #print "Node: %d, check ACK" % self.AID
        'if failed => toBackoff'
        if self.checkACK == 1:
            self.backoffStage = Global.contentionWindow
            print "Node: %d, transmitt success!" % self.AID
            'transmitted sucessfully'
            Statistic.success += 1
            self.queuingData -= 1
            if self.queuingData > 0:
                if self.channelBusyCount > 0:
                    self.state = Global.carrierSense
                    self.timeToNextTask = Eventlist.maxTime + 1
                else:
                    self.state = Global.waitDIFS
                    self.timeToNextTask = Global.currentTime + Global.DIFS
            else:
                self.state = Global.HALT
                self.timeToNextTask = Eventlist.maxTime+1
            self.checkACK = 0
        elif self.checkACK == 0:
            print "Node: %d, collision occured" % self.AID
            self.collision += 1
            Statistic.collisionTimes += 1
            if self.channelBusyCount > 0:
                self.state = Global.carrierSense
                self.timeToNextTask = Eventlist.maxTime + 1
            else:
                self.state = Global.waitDIFS
                self.timeToNextTask = Global.currentTime + Global.DIFS
        
    def readyToWork(self):
        #self.backoffStage = Global.contentionWindow
        self.backoffTime = 0
        self.state = Global.READY
        
        
    def toBackoff(self):
        #self.nav = 0
        self.state = Global.backoff
        if self.backoffTime == 0:
            self.backoffStage += 1
            self.backoffTime = randint(1, 2 ** min(self.backoffStage, 10))
            self.timeToNextTask = Global.currentTime + self.backoffTime
        else:
            self.timeToNextTask = Global.currentTime + self.backoffTime
        self.backoffStartTime = Global.currentTime
        #print "Node: %d, wait backoff: %d" % (self.AID, self.backoffTime)
        
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
        print "Total nodes: %d" % Global.nodeCounts
        


# In[13]:

class AP:
    'common access point'
    #DIVICE = "access point"

    
    def __init__(self, x, y, numOfGroup):
        self.x = x
        self.y = y
        self.group = []
        self.channelBusyCount = 0
        self.state = Global.IDLE
        self.timeToNextTask = Eventlist.maxTime + 1
        self.nodeInRange = []
        self.DEVICE = "access point"
        for groups in range(numOfGroup):
            self.group.append([0])
            
            
            
            '''
            送封包當下不收封包
            '''
    def receivePacket(self, node):
        'receivePacket'
        self.channelBusyCount += 1
        if self.state != Global.sendPacket:
            if self.channelBusyCount == 1:
                self.state = Global.carrierSense
                self.timeToNextTask = Global.currentTime + node.tranTime + SIFS
                self.respondTarget = node
                #print "AP response Target: %d" % node.AID
            else:
                self.respondTarget = 0
                print "prefer collision"
                self.timeToNextTask = max(self.timeToNextTask, (Global.currentTime + node.tranTime + SIFS))
            
    def sendPacket(self):
        'send ACK'
        print "AP send ACK to %d" % self.respondTarget.AID
        self.timeToNextTask = Global.currentTime + ACKTime
        self.state = Global.sendPacket
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket()
        self.respondTarget.checkACK = 1
        self.respondTarget = 0
        
    def changeState(self):
        '''return {
            Global.sendPacket: self.toIDLE(),
            Global.carrierSense: self.checkRespondTarget(),
        }[self.state]'''
        self.channelBusyCount = 0
        if self.state == Global.sendPacket:
            return self.toIDLE()
        elif self.state == Global.carrierSense:
            return self.checkRespondTarget()
    
    def processEnd(self):
        print "process end"
        return 0
    
    def toIDLE(self):
        #self.channelBusyCount = 0
        self.respondTarget = 0
        self.state = Global.IDLE
        self.timeToNextTask = Eventlist.maxTime + 1
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].channelBusyCount -= 1
            if (self.nodeInRange[x].channelBusyCount < 1) and (self.nodeInRange[x].state == Global.carrierSense):
                #print "Node: %d, carrier sense over,  backoff time: %d" % (self.nodeInRange[x].AID, self.nodeInRange[x].backoffTime)
                self.nodeInRange[x].state = Global.waitDIFS
                self.nodeInRange[x].timeToNextTask = Global.currentTime + Global.DIFS
                self.nodeInRange[x].nav = Global.nav
        
    def checkRespondTarget(self):
        #self.channelBusyCount = 0
        if self.respondTarget == 0:
            self.toIDLE()
        else:
            self.state = Global.READY       
        
    def calcRange(self, node):
        self.nodeInRange.append(node)

    def displayStatus(self):
        print "x: %d, y: %d,\nType: %s, number of group: %d" %(self.x, self.y, self.device, len(self.group))
        


# In[14]:

from numpy import *
class Eventlist:
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
        self.event = []
        self.workList = []
        for pointCount in range(len(points)):
            if self.nextTime > points[pointCount].timeToNextTask:
                self.nextTime = points[pointCount].timeToNextTask
                self.event = [points[pointCount]]
            elif self.nextTime == points[pointCount].timeToNextTask:
                self.event.append(points[pointCount])
    
    def goToNextTime(self):
        Global.currentTime = self.nextTime
        self.nextTime = Eventlist.maxTime
        
    def changeState(self):
        for x in range(len(self.event)):
            self.event[x].changeState()
            #print "AID: %d , state: %d" % (self.event[x].AID, self.event[x].state)
            if self.event[x].state == Global.READY:
                self.workList.append(self.event[x])
    
    def sendTime(self, AP):
        if len(self.workList)>0:
            if self.workList[0].DEVICE == "access point":
                self.workList[0].sendPacket()
                del self.workList[0]            
        for x in range(len(self.workList)):
           AP.receivePacket(self.workList[x].sendPacket())
        
    
    def showList():
        for x in range(len(event)):
            print Eventlist.event[x]
    


# In[15]:

class Statistic:
    
    packetCount = 0
    collisionTimes = 0
    success = 0


# In[16]:

class Global:
    SIFS = 3
    DIFS = 5
    ACKTime = 5
    
    carrierSense = 635
    sendPacket = 531 
    waitDIFS = 564 
    waitResponse = 315 #wait for ACK
    backoff = 615
    READY = 534
    HALT = 5843
    IDLE = 655
    
    nav = SIFS + ACKTime
    contentionWindow = 4
    nodeCounts = 0
    currentTime = 0


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
Global.nodeCounts = 0

eventController = Eventlist(2)

points.append(AP(0,0,4))

while Global.nodeCounts < 50:
    x, y = randint(-RADIUS,RADIUS), randint(-RADIUS,RADIUS)
    if (x*x + y*y) <= SQUERE_RADIUS:
        points.append(Node(x, y, 128, choice(samplingRateList), Global.nodeCounts))        

for node1 in range(1, len(points)):
    points[0].calcRange(points[node1])
    for node2 in range(node1+1, len(points)):
        points[node1].calcRange(points[node2])        
    #points[node1].displayNodesInRange()
    
while(Global.currentTime < Eventlist.maxTime):
#for x in range(10):    
    eventController.findNextTimeEvents(points)
    eventController.goToNextTime()
    print Global.currentTime
    eventController.changeState()
    eventController.sendTime(points[0])

print "end"


# In[18]:

from numpy import *
from __future__ import division
print Statistic.packetCount
print Statistic.collisionTimes
print Statistic.success
print "collision probability: %f" % float(Statistic.collisionTimes / Statistic.packetCount)
for x in range(1,len(points)):
    print "Node: %d, transmitt times: %d, collision times: %d" % (points[x].AID, points[x].transmittTimes, points[x].collision)


# In[181]:

#print points[5].timeToNextTask
#print points[:]
from numpy import *

for x in range(len(points)):
    print "X: %d, Y: %d" % (points[x].x, points[x].y)


# In[ ]:



