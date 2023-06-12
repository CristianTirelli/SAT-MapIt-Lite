from Mapper import *
from Parser import *


#CGRA size
n_cols = 4
n_rows = 4


def main():
    
    #Name of the benchmark file
    bench = "stringsearch1"
    #Path to the folder containing the benchmark
    path = "../benchmarks/StringSearch/"

    edgefile = path + bench + "_edges"

    #DFG parser
    p = Parser()
    p.parseEdgeFile(edgefile)
    
    #Get the parsed DFG
    DFG = p.getDFG()
    print("#nodes: " + str(len(DFG.nodes)))

    
    #Initialize the mapper with the CGRA dimensions,
    #number of registers of each PE and the DFG
    m = Mapper(n_rows, n_cols, DFG, bench)


    # If some nodes can be mapped only on specific PEs
    # populate the dict below (id, list_of_pes)
    # Example 
    # Suppose you have the following DFG: {(1,2), (1,3), (2,4)}
    # and that Node 1 can be mapped only on PE 1,2 of a 2x2 CGRA
    # then you will have: 
    # node_pes[1] = [1, 2]
    # node_pes[2] = [1, 2, 3, 4]
    # node_pes[3] = [1, 2, 3, 4]
    # node_pes[4] = [1, 2, 3, 4]
    node_pes = {}

    #Find the mapping and get the mapped kernel
    m.findMapping(node_pes)
    


if __name__ == "__main__":
    main()