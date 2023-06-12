#node of the DFG


class node:
    def __init__(self, id):
        self.id = id
        
        
        self.index = -1
        self.lowlink = 0
        self.onstack = False
        self.time = 1
        self.latency = 1
    def __del__(self):
        self.index = -1
        self.lowlink = 0
        self.onstack = False
        self.time = 1
        self.latency = 1
#edge of the DFG
class edge:
    def __init__(self, source, destination, distance, latency):
        self.source = source
        self.destination = destination
        self.distance = distance
        self.latency = latency

#data flow graph of the loop, with information on livein, liveout and constants
#constants, livein, liveout could be handled better
class DFG:
    
    nodes = []
    edges = []
    index = 0
    stack = []
    
    def __init__(self):
        pass

    def __del__(self):
        self.nodes.clear()
        self.edges.clear()
        self.stack.clear()
        self.index = 0

    def addNode(self, new_node):
        found = False
        for n in self.nodes:
            if n.id == new_node.id:
                found = True 
        if not found:
            self.nodes.append(new_node)
        

    def addEdge(self, n):
        self.edges.append(n)
    
    def getEdge(self, source, destination):
        for e in self.edges:
            if e.source.id == source and e.destination.id == destination:
                return e
        return None

    def resetTime(self):
        for n in self.nodes:
            n.time = 0
    
    def resetNodeTime(self, t):
        for n in self.nodes:
            n.time = t

    def resetLatency(self):
        for n in self.nodes:
            n.latency = 1

    def getSuccessors(self, n):
        succ = []
        for e in self.edges:
            if e.source.id == n.id:
                succ.append(e.destination)
        return succ

    def getPredecessors(self, n):
        preds = []
        for e in self.edges:
            if e.destination.id == n.id:
                preds.append(e.source)
        return preds

    #return nodes that have no predecessor (phi nodes usually)
    def getStartingNodes(self):
        starting_nodes = set()
        for n in self.nodes:
            
            if len(self.getPredecessors(n)) == 0:
                starting_nodes.add(n)
            else:
                all_loop_carried = True
                for pred in self.getPredecessors(n):
                    if self.getEdge(pred.id, n.id).distance == 0:
                        all_loop_carried = False
                if all_loop_carried == True:
                    starting_nodes.add(n)

        return starting_nodes

    #return nodes that have no successor or node whose only successor is a phi node
    def getEndingNodes(self):
        ending_nodes = set()
        
        for n in self.nodes:
            if len(self.getSuccessors(n)) == 0:
                ending_nodes.add(n)
            else:
                allphi = True
                
                for suc in self.getSuccessors(n):
                    if self.getEdge(n.id, suc.id).distance == 0:
                        allphi = False
                
                if allphi == True:
                    ending_nodes.add(n)

        return ending_nodes

    #Get Strongly Connected Components in the DFG
    def getSCCs(self):

        sccs = []
        for n in self.nodes:
            if n.index == -1:
                self.strongConnect(n, sccs)
        
        return sccs
    
    #Utility function used by getSCCs
    def strongConnect(self, n, sccs):
        n.index = self.index
        n.lowlink = self.index
        self.index += 1
        self.stack.append(n)
        n.onstack = True

        for succ in self.getSuccessors(n):
            if succ.index == -1:
                self.strongConnect(succ, sccs)
                n.lowlink = min(n.lowlink, succ.lowlink)
            elif succ.onstack == True:
                n.lowlink = min(n.lowlink, succ.index)
        tmp_sccs = []

        if n.lowlink == n.index:
            while len(self.stack) != 0:
                w = self.stack.pop()
                tmp_sccs.append(w)
                w.onstack = False

                if n.id == w.id:
                    break
        
            if len(tmp_sccs) > 1:
                sccs.append(tmp_sccs[:])

    #Utility function used by getSCCs
    def getPathDelay(self, scc):

        #roots should be only phi nodes
        roots = set()
        starting_nodes_id = []
        phi_nodes_id = []
        for n in self.getStartingNodes():
            all_phi = True
            for pre in self.getPredecessors(n):
                if self.getEdge(pre.id, n.id).distance == 0:
                    all_phi = False
            if all_phi == True:
                phi_nodes_id.append(n.id)
        for n in scc:
            #print(n.id)
            r = None    
            for e in self.edges:
                if e.distance > 0 and n.id == e.destination.id:
                    r = n

            if r == None:
                continue
        
            to_explore = []
            visited = []
            curr = []
            delay = 0 
        
            
            visited.append(r)
            to_explore.append(r)
            explored = 1
            while explored > 0:
                explored = 0
                #print("exploring")
                for n in to_explore:
                    #print(n.id)
                    for succ in self.getSuccessors(n):
                        if succ.id in phi_nodes_id:
                            continue
                        if succ in scc:
                            #print("scc")
                            #print(succ.id)
                            if succ.latency <= n.latency:
                                succ.latency = n.latency + 1
                            
                            delay = max(delay, succ.latency)
                            
                            if succ not in visited:
                                curr.append(succ)
                                visited.append(succ)
                            explored += 1
                
                to_explore = curr[:]#create shadow copy
                curr.clear()
        
        return delay

    def getNode(self, id):
        for n in self.nodes:
            if n.id == id:
                return n
        return None