
# coding: utf-8

# In[247]:

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
        self.state = Global.HALT
        self.timeToNextTask = Global.maxTime +1
        self.nav = Global.nav
        self.checkACK = 0
        self.backoffStage = Global.contentionWindow
        self.backoffTime = 0#randint(0, 2 ** min(self.backoffStage, 10))
        self.tranTime = fix(((packetLength * 8) / Global.slotTime) / Global.dataRate)
        self.queuingData = 1#randint(0, 1000)
        self.collision = 0
        self.AID = AID
        self.transmittTimes = 0
        self.expectedUsingTimePerBeacon = fix((self.tranTime * (samplingRate / 60)) * Global.beacon_sec)
        Global.nodeCounts += 1
        
    def sendPacket(self):
        '''
        to AP: send request
        to other nodes: message "transmitting"
        '''
        Statistic.packetCount += 1
        Global.channelUser += 1
        self.transmittTimes += 1
        self.timeToNextTask = Global.currentTime + self.tranTime
        self.state = Global.sendPacket
        #print "Node: %d, send packet" % self.AID
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket()
        return self
            
    
    def receivePacket(self):
        'Carrier sense'
        self.channelBusyCount += 1
        if (self.state == Global.waitDIFS) or (self.state == Global.backoff):
            if self.state == Global.backoff:
                self.backoffTime = self.backoffTime - (Global.currentTime - self.backoffStartTime)
            self.state = Global.carrierSense
            #print "Node: %d, carrier sense" % self.AID
            self.timeToNextTask = Global.maxTime +1
        if self.channelBusyCount >1:
            self.nav = 0
            self.checkACK = 0
            
        
    def changeState(self):
        "change state when it's the node's turn"
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
        #print "Node: %d, wait response" % self.AID
        self.timeToNextTask = Global.currentTime + Global.nav
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].channelUserDecrease()
        Global.channelUser -= 1 
            
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
            #print "Node: %d, transmitt success!" % self.AID
            'transmitted sucessfully'
            Statistic.success += 1
            self.queuingData -= 1
            if self.queuingData > 0:
                if self.channelBusyCount > 0:
                    self.state = Global.carrierSense
                    self.timeToNextTask = Global.maxTime +1
                else:
                    self.state = Global.waitDIFS
                    self.timeToNextTask = Global.currentTime + Global.DIFS
            else:
                self.state = Global.HALT
                self.timeToNextTask = Global.maxTime +1
            self.checkACK = 0
        elif self.checkACK == 0:
            #print "Node: %d, collision occured" % self.AID
            self.collision += 1
            Statistic.collisionTimes += 1
            if self.channelBusyCount > 0:
                self.state = Global.carrierSense
                self.timeToNextTask = Global.maxTime +1
            else:
                self.state = Global.waitDIFS
                self.timeToNextTask = Global.currentTime + Global.DIFS
        
    def readyToWork(self):
        #self.backoffStage = Global.contentionWindow
        self.backoffTime = 0
        if Global.currentTime < Global.holdingPeriodInterval:
            self.state = Global.READY
        else:
            self.state = Global.HALT
            self.timeToNextTask = Global.maxTime +1
        
        
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
        
    def dataInterval(self):
        self.queuingData += 1
        '''if self.state == Global.HALT:
            self.state = Global.waitDIFS
            self.timeToNextTask = Global.currentTime + Global.DIFS'''
        
    def wakeUp(self):
        if self.queuingData > 0:
            self.state = Global.waitDIFS
            self.timeToNextTask = Global.currentTime + Global.DIFS
        #print "node: %d, state: %d" % (self.AID, self.state)
            
    def goSleep(self):
        self.state = Global.HALT
        self.timeToNextTask = Global.maxTime +1
        
    def calcRange(self, others):
        if (((self.x- others.x) ** 2) + ((self.y - others.y) ** 2)) <= 4000000:
            self.nodeInRange.append(others)
            others.nodeInRange.append(self)
    
    def displayNodesInRange(self):
        for x in range(len(self.nodeInRange)):
            print self.nodeInRange[x].displayStatus()
        
    def displayStatus(self):
        print "x: %d, y: %d,\nType: %s, group: %d" %(self.x, self.y, self.device, self.group)
                    
    def displayNodeCounts(self):
        print "Total nodes: %d" % Global.nodeCounts
        


# In[248]:

class AP:
    'common access point'
    #DIVICE = "access point"
    from random import randint
    
    def __init__(self, x, y, numOfGroup):
        self.x = x
        self.y = y
        self.group = []
        self.groupWeight = []
        self.expectedGroupWeight = []
        self.groupUtilization = []
        self.incrementalGain = []
        self.expectedGroupUtilization = []
        self.channelBusyCount = 0
        self.state = Global.IDLE
        self.timeToNextTask = Global.maxTime +1
        self.nodeInRange = []
        self.DEVICE = "access point"
        for groups in range(numOfGroup):
            self.group.append([self])
            self.groupWeight.append(1)
            self.expectedGroupWeight.append(0)
            self.groupUtilization.append(0)
            self.expectedGroupUtilization.append(0)
            self.incrementalGain.append(0)
            
            
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
                #print "prefer collision"
                self.timeToNextTask = max(self.timeToNextTask, (Global.currentTime + node.tranTime + SIFS))
        #print "AP channel busy count: %d" % self.channelBusyCount
            
    def sendPacket(self):
        'send ACK'
        #print "AP send ACK to %d" % self.respondTarget.AID
        self.timeToNextTask = Global.currentTime + ACKTime
        self.state = Global.sendPacket
        for x in range(len(self.nodeInRange)):
            self.nodeInRange[x].receivePacket()
        self.respondTarget.checkACK = 1
        self.respondTarget = 0
        Global.channelUser += 1
        
    def changeState(self):
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
        if self.state == Global.sendPacket:
            Global.channelUser -= 1
        self.respondTarget = 0
        self.state = Global.IDLE
        self.timeToNextTask = Global.maxTime +1
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
        
    def randomGroup(self, points):
        for x in range(1, len(points)):
            choiceGroup = choice(self.group)
            while(len(choiceGroup) > (6000 / len(self.group))):
                choiceGroup = choice(self.group)
            choiceGroup.append(points[x])
    
    def loadBalancedGrouping(self, points):
        for x in range(1, len(points)):
            self.updateGain(points[x])
            
            
    def updateGain(self, node):
        for x in range(len(self.group)):
            
        


# In[249]:

from numpy import *
class Eventlist:
    #currentTime = 0
    #collision = 0
    #maxTime = 0
    def __init__(self, endTime):
        self.event = []
        self.workList = []
        Global.maxTime = fix(endTime*1000000/52)
        self.nextTime = Global.rawInterval

        
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
        self.nextTime = Global.rawInterval
        
    def changeState(self):
        for x in range(len(self.event)):
            self.event[x].changeState()
            #print "AID: %d , state: %d" % (self.event[x].AID, self.event[x].state)
            if self.event[x].state == Global.READY:
                self.workList.append(self.event[x])
    
    def timeToSendPacket(self, AP):
        if len(self.workList)>0:
            if self.workList[0].DEVICE == "access point":
                self.workList[0].sendPacket()
                del self.workList[0]            
        for x in range(len(self.workList)):
           AP.receivePacket(self.workList[x].sendPacket())
        
    def checkChannelState(self):
        if Global.channelState == Global.IDLE:
            if Global.channelUser > 0:
                Global.channelBusyStartTime = Global.currentTime
                Global.channelState = Global.carrierSense
        elif Global.channelState == Global.carrierSense:
            if Global.channelUser == 0:
                Global.channelUsingTime = Global.channelUsingTime + (Global.currentTime - Global.channelBusyStartTime)
                Global.channelState = Global.IDLE          
        #print "check channel: %d" % Global.channelUser
    
    def wakeUpGroup(self, group):
        for x in range(1, len(group)):
            group[x].wakeUp()
    
    def groupGoSleep(self, group):
        for x in range(1, len(group)):
            group[x].goSleep()
    
    def showList():
        for x in range(len(event)):
            print Eventlist.event[x]
    


# In[250]:

from random import randint
class DataInterval:
    def __init__(self):
        self.arrivalTimeList = [Global.maxTime]
        self.nodeArrivalTime = [Global.maxTime]
        
    def checkDataArrival(self, points):
        for x in range(1, len(points)):
            if self.arrivalTimeList[x] < Global.currentTime:
                points[x].dataInterval()
                #print "data arrival: node %d" % points[x].AID
                self.arrivalTimeList[x] = Global.currentTime + self.nodeArrivalTime[x]
                
    def getSamplingRate(self, points):
        for x in range(1, len(points)):
            self.nodeArrivalTime.append(fix(((60 * 1000000) / Global.slotTime) / points[x].samplingRate))
            self.arrivalTimeList.append((randint(0 , 4) * Global.beaconTime) + self.nodeArrivalTime[x])


# In[251]:

class Statistic:
    
    packetCount = 0
    collisionTimes = 0
    success = 0


# In[252]:

class Global:
    SIFS = 3
    DIFS = 5
    ACKTime = 5
    slotTime = 52
    dataRate = 0.65
    
    group = 4
    
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
    maxTime = 0
    
    beacon_sec = 0.45
    
    beaconTime = fix((beacon_sec * 1000000) / slotTime)
    beaconInterval = currentTime + beaconTime
    rawTime = (beaconTime / group)
    rawInterval = currentTime + rawTime
    holdingPeriod = (rawTime * 0.2)
    holdingPeriodInterval = rawInterval - holdingPeriod
    
    channelUser = 0
    channelBusyStartTime = 0
    channelUsingTime = 0
    channelState = IDLE
    


# In[253]:

from random import choice, randint
from numpy import *
SIFS = 3
DIFS = 5
ACKTime = 5
RADIUS = 1000
SQUERE_RADIUS = RADIUS ** 2
packetLengthList = [64, 128, 256]
samplingRateList = [2, 4, 8, 16, 32] #per minute
points = []
Global.nodeCounts = 0

eventController = Eventlist(60)
dataIntervalController = DataInterval()

points.append(AP(0,0,Global.group))

while Global.nodeCounts < 1000:
    x, y = randint(-RADIUS,RADIUS), randint(-RADIUS,RADIUS)
    if (x*x + y*y) <= SQUERE_RADIUS:
        points.append(Node(x, y, choice(packetLengthList), choice(samplingRateList), Global.nodeCounts))        

points[0].randomGroup(points)

for x in range(Global.group):
    for node1 in range(1, len(points[0].group[x])):
        points[0].calcRange(points[0].group[x][node1])
        for node2 in range(node1+1, len(points[0].group[x])):
            points[0].group[x][node1].calcRange(points[0].group[x][node2])
        
dataIntervalController.getSamplingRate(points)

    
while Global.currentTime < Global.maxTime:
    while Global.currentTime < min(Global.maxTime, Global.beaconInterval):
        for x in range(Global.group):
            dataIntervalController.checkDataArrival(points)
            #wake up group x
            eventController.wakeUpGroup(points[0].group[x])
            while Global.currentTime < min(Global.maxTime, Global.rawInterval):
                eventController.findNextTimeEvents(points[0].group[x])
                eventController.goToNextTime()
                eventController.changeState()
                eventController.timeToSendPacket(points[0])
                eventController.checkChannelState()
            #group x go to sleep
            eventController.groupGoSleep(points[0].group[x])
            print "group %d end a raw time" % x
            Global.rawInterval = Global.currentTime + Global.rawTime
            Global.holdingPeriodInterval = Global.rawInterval - Global.holdingPeriod
    Global.beaconInterval = Global.currentTime + Global.beaconTime
    print "beacon check, %d" % Global.currentTime
    #dataIntervalController.checkDataArrival(points)

print "end"


# In[254]:

from numpy import *
from __future__ import division
print "send packets: %d" % Statistic.packetCount
print "collision times: %d" % Statistic.collisionTimes
print "transmitt success: %d " % Statistic.success
print "collision probability: %f" % float(Statistic.collisionTimes / Statistic.packetCount)
print "Throughput: %d" % (Statistic.success * 128)
print "channel utilization: %f" % float(Global.channelUsingTime / Global.maxTime)
#print Global.channelUsingTime
for x in range(1,len(points)):
    print "Node: %d, sampling rate: %d per min, packet length: %d, transmitt times: %d, collision times: %d, queuing data: %d" % (points[x].AID, points[x].samplingRate, points[x].packetLength, points[x].transmittTimes, points[x].collision, points[x].queuingData)


# In[209]:

#print points[5].timeToNextTask
#print points[:]
from numpy import *
'''
for x in range(len(points)):
    print "X: %d, Y: %d" % (points[x].x, points[x].y)'''
#print fix(((60 * 1000000) / Global.slotTime) / points[3].samplingRate)
print Global.currentTime
print Global.rawInterval
print (Global.rawTime * 4)
print Global.beaconTime
#print points[0].group[1]
#points[0].randomGroup(points)
#print points[0].group[1][3]
#print Global.group
#print points[0].nodeInRange[0].DEVICE
    


# In[ ]:



