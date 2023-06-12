from DFG import *

#parser for all the input file that generates the DFG

class Parser:
    nodes = []
    edges = []

    def __init__(self):
        self.dfg = DFG()
    
    def __del__(self):
        self.nodes.clear()
        self.edges.clear()
        self.dfg = None

    def parseEdgeFile(self, edgefile):
        with open(edgefile,"r") as fd: 
            for l in fd.read().splitlines():
                self.edges.append([x for x in l.split(' ')])
                #print(self.edges)
    
    def getDFG(self):
        #generate DFG edges
        for e in self.edges:
            #Create Nodes
            tmp = node(int(e[0]))
            self.dfg.addNode(tmp)
            tmp = node(int(e[1]))
            self.dfg.addNode(tmp)
            
            #Create Edge
            source = self.dfg.getNode(int(e[0]))
            destination = self.dfg.getNode(int(e[1]))
            if source == None or destination == None:
                if source == None:
                    print("Source")
                if destination == None:
                    print("Destination")
                print("Error parsing dep " + e[0] + " -> " + e[1])
                exit(0)
            distance = int(e[2])
            latency = int(e[3])

            tmp = edge(source, destination, distance, latency)
            self.dfg.addEdge(tmp)

        return self.dfg
