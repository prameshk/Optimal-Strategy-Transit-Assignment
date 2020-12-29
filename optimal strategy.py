# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 09:45:58 2020
The script codes optimal strategy transit assignment. 

@author: kumar372
"""
import time, math
import heapq

################################################################################################+
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    mi = 3959 * c
    return mi



class Node:
    '''
    Defines attributes of a node
    '''
    def __init__(self, _tmpIn):
        self.id = _tmpIn[0]
        self.name = _tmpIn[1]
        self.lat = float(_tmpIn[2])
        self.long = float(_tmpIn[3])
        self.type = _tmpIn[4] # can be 'stop' or particular line_id or 'zone'
        self.outLinks = []
        self.inLinks = []
        self.label = 0
        self.pred = ""
        self.flow = 0.0
        self.u = float("inf") # expected cost to go from here
        self.f = 0.0
class Link:
    '''
    Defines attributes of a link
    '''
    def __init__(self, _tmpIn):
        self.fromNode = _tmpIn[0]
        self.toNode = _tmpIn[1]
        self.time = _tmpIn[2] # in seconds
        self.routeId =  _tmpIn[3]
        self.dir = int(_tmpIn[4])
        self.name =  _tmpIn[5]
        try:
            self.headway = float(_tmpIn[6]) # in minutes
        except:
             self.headway = 60.0 # in minutes
        self.type = _tmpIn[7]
        self.seq = int(_tmpIn[8])
        self.wait = 0
        self.passengers = []
        self.flow = 0.0
        
class Line:
    def __init__(self, _tmpIn):
        self.lineId = _tmpIn[0]
        self.headway = _tmpIn[1]
        
class Demand:
    '''
    Demand between nodes
    '''
    def __init__(self, _tmpIn):
        self.fromZone = _tmpIn[0]
        self.toZone = _tmpIn[1]
        self.demand = float(_tmpIn[2])
        
        
        
##############################################################################################       
def readNodes():
    """
    Read zones, road nodes, and transit stopID from files
    """
    # Reading transit stops
    inFile = open('nodes.dat')
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        nodeId = (tmpIn[0] , tmpIn[4])
        if nodeId not in nodeSet:
            nodeSet[nodeId] = Node(tmpIn)
        else:
            print(tmpIn[0], " stop already present ")
    inFile.close()
    
    # Reading zones
    inFile = open('ft_input_zones.dat')
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        nodeId = (tmpIn[0] , 'zone')
        if nodeId not in nodeSet:
            nodeSet[nodeId] = Node([tmpIn[0], tmpIn[0], tmpIn[1], tmpIn[2], 'zone'])
        else:
            print(tmpIn[0], " stop already present ")
    inFile.close()

    
    

        
def readTransitLinks():
    inFile = open("links.dat")
    tmpIn = inFile.readline().strip().split("\t")
    prevNodeId = ""
    for x in inFile:
        tmpIn = x.strip().split("\t")
        routeId = tmpIn[0]
        nodeId = (tmpIn[3], routeId) # Stop Id and route Id 
        seq = tmpIn[4]
        if int(seq)==1:
            prevNodeId = nodeId
            tmpTime = tmpIn[2].split(":")
            prevNodeTime = int(tmpTime[0]) * 3600 + int(tmpTime[1]) * 60 + int(tmpTime[2]) 
        if int(seq)>1:            
            dist = haversine(nodeSet[prevNodeId].long, nodeSet[prevNodeId].lat, nodeSet[nodeId].long, nodeSet[nodeId].lat)
            tmpTime = tmpIn[2].split(":")
            time = int(tmpTime[0]) * 3600 + int(tmpTime[1]) * 60 + int(tmpTime[2]) 
            linkId = (prevNodeId, nodeId)            
                
            if prevNodeId not in nodeSet:
                print(prevNodeId, 'node not in nodeset')
                
            if nodeId not in nodeSet:
                print(prevNodeId, 'node not in nodeset')
                
            if linkId not in linkSet:
                linkSet[linkId] = Link([prevNodeId, nodeId, (time - prevNodeTime)/60, tmpIn[0], tmpIn[8], tmpIn[11], tmpIn[12], 'transit', tmpIn[4]])
                if linkId not in nodeSet[prevNodeId].outLinks:
                    nodeSet[prevNodeId].outLinks.append(linkId)
                if linkId not in nodeSet[nodeId].inLinks:
                    nodeSet[nodeId].inLinks.append(linkId)
            prevNodeId = nodeId # Changing the previous node to current node (This will take care of the stop seq = 1 also)
            prevNodeTime = time
        else:
            continue
    inFile.close()        

        
        
def readAccessLinks():
    inFile = open("ft_input_accessLinks.dat")
    tmpIn = inFile.readline().strip().split("\t")
    prevNodeId = ""
    for x in inFile:
        tmpIn = x.strip().split("\t")          
        if (tmpIn[0], 'zone') in nodeSet and (tmpIn[1], 'stop') in nodeSet:            
            linkId = ((tmpIn[0], 'zone'), (tmpIn[1], 'stop'))
            if linkId not in linkSet:                  
                linkSet[linkId] = Link([(tmpIn[0], 'zone'), (tmpIn[1], 'stop'), float(tmpIn[2])*60, '', 0, '', "inf", 'access', '0' ])
                if linkId not in nodeSet[(tmpIn[0], 'zone')].outLinks:
                    nodeSet[(tmpIn[0], 'zone')].outLinks.append(linkId)
                if linkId not in nodeSet[(tmpIn[1], 'stop')].inLinks:
                    nodeSet[(tmpIn[1], 'stop')].inLinks.append(linkId)
                    
            linkId = ((tmpIn[1], 'stop'), (tmpIn[0], 'zone'))
            if linkId not in linkSet:                  
                linkSet[linkId] = Link([(tmpIn[1], 'stop'), (tmpIn[0], 'zone'), float(tmpIn[2])*60, '', 1, '', "inf", 'egress', '0'])
                if linkId not in nodeSet[(tmpIn[1], 'stop')].outLinks:
                    nodeSet[(tmpIn[1], 'stop')].outLinks.append(linkId)
                if linkId not in nodeSet[(tmpIn[0], 'zone')].inLinks:
                    nodeSet[(tmpIn[0], 'zone')].inLinks.append(linkId)


def createBoardAlightLinks():
    for s in stops:
        for n in [k for k in nodeSet if k[0] == s[0] and k != s and k[1] != 'zone']:
            linkId = (s, n)
            if linkId not in linkSet:
                linkSet[linkId] = Link([s, n, 0.0, n[1], 0, '', float("inf"), 'board', 0])
                if linkId not in nodeSet[s].outLinks:
                    nodeSet[s].outLinks.append(linkId)
                if linkId not in nodeSet[n].inLinks:
                    nodeSet[n].inLinks.append(linkId)
                    
            linkId = (n, s)
            if linkId not in linkSet:
                linkSet[linkId] = Link([n, s, 0.0, n[1], 0, '', float("inf"), 'alight', 0])
                if linkId not in nodeSet[n].outLinks:
                    nodeSet[n].outLinks.append(linkId)
                if linkId not in nodeSet[s].inLinks:
                    nodeSet[s].inLinks.append(linkId)
                    
    for k in {k for k in nodeSet if len(nodeSet[k].inLinks) ==0 and len(nodeSet[k].outLinks) ==0}:
        del nodeSet[k]
            
            
def defineLineFreq():
    for k in {k for k in linkSet if linkSet[k].type == 'transit'}:
        if k[1][1] not in lineSet:
            lineSet[k[1][1]] = Line([k[1][1], linkSet[k].headway])
        
        
def readDemand():
    '''
    Reads demand data
    '''
    inFile = open('demand.dat')
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        
        if (tmpIn[0], 'zone') in nodeSet and (tmpIn[1], 'zone') in nodeSet:   
            Id = ((tmpIn[0], 'zone'), (tmpIn[1], 'zone'))
            if Id not in tripSet:
                tripSet[Id] = Demand(tmpIn)
            else:
                print(tmpIn[0], " demand pair already present ")
            
    
    inFile.close()

################################################################################################################        
def optimalStrategy():
    for s in destSet:
        for n in nodeSet: nodeSet[n].u = float("inf"); nodeSet[s].u = 0.0;
        for n in nodeSet: nodeSet[n].f = 0.0;
        S = list(linkSet.keys()); Abar = []; 
        start = time.time()
        while S:     
            Sheap = []
            for (i, j) in S: heapq.heappush(Sheap, [nodeSet[j].u + linkSet[i, j].time, (i, j)]);
            cost, (i, j) = heapq.heappop(Sheap);
            S.remove((i, j))
            if linkSet[(i, j)].type == 'board':
                freq = 1.0/lineSet[j[1]].headway
            else:
                freq = float("inf")                
            if nodeSet[i].u >= cost:
                first = nodeSet[i].u * nodeSet[i].f
                if math.isnan(first):
                    first = 1.0
                first = 1.0 / (nodeSet[i].f + freq)
                second = freq/(nodeSet[i].f + freq)
                if math.isnan(second):
                    second = 1.0                    
                g = second
                second = second * cost   
                if math.isnan(second):
                    print(g, nodeSet[i].f , freq,cost)
                    break
                    second = 0.0
                nodeSet[i].u = first + second      
                nodeSet[i].f += freq
                Abar.append((i, j))
        print(time.time() - start)               
        
            
        for r in originSet:
            if (r, s) in tripSet:
                nodeSet[r].flow = tripSet[r, s].demand
        nodeSet[s].flow = sum([-tripSet[r, s].demand for r in originSet if (r, s) in tripSet])
        A = {(i, j): nodeSet[j].u + linkSet[i, j].time for (i, j) in Abar}
        A = dict(sorted(A.items(), key=lambda item: item[1]))
        for (i, j) in A:
            if linkSet[(i, j)].type == 'board':
                freq = 1.0/lineSet[j[1]].headway
            else:
                freq = float("inf")
            first = nodeSet[i].f/freq
            if math.isnan(first) or nodeSet[i].f == float("inf"):
                first = 1.0
            if math.isnan(first*nodeSet[i].flow) == True:
                linkSet[i, j].flow = 0.0
            else:
                linkSet[i, j].flow = first*nodeSet[i].flow
            if math.isnan(linkSet[i, j].flow) == True:
                print(first, nodeSet[i].flow)
            nodeSet[j].flow += linkSet[i, j].flow
                
        print(time.time() - start)
        
                
                    
                    
                    
        
        
                
        
                
                        
                        
                        
                    
                
            
        
        
        
################################################################################################################       
start = time.time()
nodeSet = {}; linkSet = {}; tripSet = {}; lineSet = {}
readNodes(); readTransitLinks(); readAccessLinks(); 
stops = list({k for k in nodeSet if nodeSet[k].type == 'stop'})
createBoardAlightLinks(); readDemand() ; defineLineFreq()      
destSet = list({k[1] for k in tripSet})
originSet = list({k[0] for k in tripSet})

print('Reading the network took %d seconds' % (time.time() -start))
print('Network has %d nodes, %d links, %d O-D pairs' % (len(nodeSet), len(linkSet), len(tripSet)))
        
        
        
        
        
        
        
        
        
        

