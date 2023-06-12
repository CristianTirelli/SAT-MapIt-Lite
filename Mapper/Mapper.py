import math
import itertools
import time
from z3 import *


class Mapper:
    
    def __init__(self, x, y, dfg, benchmark):
        
        self.CGRA_X = x
        self.CGRA_Y = y    
        self.s = Solver()
        self.benchmark = benchmark
        
        self.DFG = dfg
        self.ResII = 0
        self.RecII = 0
        self.II = 0
        self.ASAP = {}
        self.ALAP = {}
        self.MS = {}
        self.KMS = {}
        self.scheduleLen = 0
        
        #schedule found by solver that can be modulo scheduled
        self.schedule = {}
        self.prolog = {}
        self.kernel = {}
        self.epilog = {}

        self.init = {}
        self.pke = {}
        self.fini = {}
        #init + pke + fini = mapping
        self.mapping = {}

        self.ra = None

    def __del__(self):

        self.DFG = None
        self.ResII = 0
        self.RecII = 0
        self.II = 0
        self.scheduleLen = 0
        self.ASAP.clear()
        self.ALAP.clear()
        self.MS.clear()
        self.KMS.clear()
        self.schedule.clear()
        self.prolog.clear()
        self.kernel.clear()
        self.epilog.clear()
        self.init.clear()
        self.fini.clear()
        self.mapping.clear()
        self.ra = None

    #Get Resource Iteration Interval
    def computeResII(self):
        #print(self.CGRA_X, self.CGRA_Y)
        self.ResII = math.ceil(len(self.DFG.nodes)/(self.CGRA_X*self.CGRA_Y))

    #Get Recurrence Iteration Interval
    def computeRecII(self):
        
        for s in self.DFG.getSCCs():
            #print("SCC size:" + str(len(s)))
            self.RecII = max(self.DFG.getPathDelay(s), self.RecII)        

    #Get Minimum Iteration Interval (MII)
    def getStartingII(self):            
        self.computeRecII()
        self.computeResII()
        self.II = max(self.RecII, self.ResII)
        print("REC " + str(self.RecII))
        print("RES " + str(self.ResII))
        return self.II

    #Generate As-Soon-As-Possible schedule
    def generateASAP(self):
        self.ASAP.clear()
        self.DFG.resetNodeTime(0)
        to_explore = self.DFG.getStartingNodes()
        phi_nodes_id = []
        for n in self.DFG.getStartingNodes():
            all_phi = True
            for pre in self.DFG.getPredecessors(n):
                if self.DFG.getEdge(pre.id, n.id).distance == 0:
                    all_phi = False
            if all_phi == True:
                phi_nodes_id.append(n.id)

        while to_explore:
            tmp = []
            for n in to_explore:
                for sn in self.DFG.getSuccessors(n):
                    if sn.id not in phi_nodes_id:
                        sn.time = max(sn.time, n.time + 1)
                        tmp.append(sn)
                        self.scheduleLen = max(self.scheduleLen, sn.time)
            to_explore = tmp[:]
            tmp.clear()
        
        for n in self.DFG.nodes:
            if n.time not in self.ASAP:
                self.ASAP[n.time] = []
            self.ASAP[n.time].append(n.id)

        #print(self.ASAP)
        print("\nASAP Schedule")
        for t in range(0, len(self.ASAP)):
            tmp = ""
            for e in self.ASAP[t]:
                tmp+= str(e) + " "
            print(tmp)
        print()
    
    #Generate As-Late-As-Possible schedule
    def generateALAP(self):
        self.DFG.resetNodeTime(0)
        to_explore = self.DFG.getEndingNodes()
        phi_nodes_id = []
        for n in self.DFG.getStartingNodes():
            all_phi = True
            for pre in self.DFG.getPredecessors(n):
                if self.DFG.getEdge(pre.id, n.id).distance == 0:
                    all_phi = False
            if all_phi == True:
                phi_nodes_id.append(n.id)

        while to_explore:
            tmp = []
            for n in to_explore:
                for sn in self.DFG.getPredecessors(n):
                    if sn.id not in phi_nodes_id:
                        sn.time = max(sn.time, n.time + 1)
                        tmp.append(sn)
                        self.scheduleLen = max(self.scheduleLen, sn.time)
                    else:
                        sn.time = max(sn.time, n.time + 1)
                        self.scheduleLen = max(self.scheduleLen, sn.time)

            to_explore = tmp[:]
            tmp.clear()

        for n in self.DFG.nodes:
            if (self.scheduleLen - n.time) not in self.ALAP:
                self.ALAP[self.scheduleLen - n.time] = []
            self.ALAP[self.scheduleLen - n.time].append(n.id)
        
        #print(self.ALAP)
        print("\nALAP Schedule")
        for t in range(0, len(self.ALAP)):
            tmp = ""
            for e in self.ALAP[t]:
                tmp+= str(e) + " "
            print(tmp)
        print()

    def getASAPTime(self, id):
        for t in self.ASAP:
            for nid in self.ASAP[t]:
                if nid == id:
                    return t
        return -1

    def getALAPTime(self, id):
        for t in self.ALAP:
            for nid in self.ALAP[t]:
                if nid == id:
                    return t
        return -1

    #Generate Mobility schedule
    def generateMS(self):
        self.ASAP.clear()
        self.ALAP.clear()
        self.generateASAP()
        self.generateALAP()

        for n in self.DFG.nodes:

            t_asap = self.getASAPTime(n.id)
            t_alap = self.getALAPTime(n.id)

            for t in range(t_asap, t_alap + 1):
                if t not in self.MS:
                    self.MS[t] = []
                self.MS[t].append(n.id)
        
        print("\nMobility Schedule")
        for t in range(0, len(self.MS)):
            tmp = ""
            for e in self.MS[t]:
                tmp+= str(e) + " "
            print(tmp)
        print()
    
    #Generate Kernel Mobility Schedule
    def generateKMS(self, II):
        self.KMS.clear()
        if II <= self.scheduleLen + 1:
            for i in range(0,self.scheduleLen + 1):
                it = i//II
                
                if (i%II) not in self.KMS:
                    self.KMS[i%II] = []
                for nid in self.MS[i]:
                    self.KMS[i%II].append((it, nid))
        else:
            #print(II, self.scheduleLen + 1)
            
            dup = II - (self.scheduleLen + 1)
            it = 0
            tmpKMS = {}
            for d in range(0, dup + 1):
                for i in range(0, self.scheduleLen + 1):
                    if (i + d) not in tmpKMS:
                        tmpKMS[i + d] = []
                    for nid in self.MS[i]:
                        if nid not in tmpKMS[i + d]:
                            tmpKMS[i + d].append(nid)

                d += 1
            
            for t in tmpKMS:
                if t not in self.KMS:
                    self.KMS[t] = []
                for nid in tmpKMS[t]:
                    self.KMS[t].append((it, nid))
            
            #print(dup)
            #for t in tmpKMS:
            #    print(tmpKMS[t])
            #print("TODO: implement", II, self.scheduleLen)
            #exit(0)


        #print(self.KMS)

    #Add constraint1 of the formulation
    #Only one literal for each node must be set to True
    def addConstraint1(self, node_literals):
        print("Adding C1...")
        start = time.time()
        for nodeid in node_literals:
            phi = Or(node_literals[nodeid])
            tmp = []
            for i in range(len(node_literals[nodeid])-1):
                for j in range(i+1, len(node_literals[nodeid])):
                    tmp.append(Not(And(node_literals[nodeid][i], node_literals[nodeid][j])))
            tmp = And(tmp)
            exactlyone = And(phi,tmp)
            self.s.add(exactlyone)
        end = time.time()
        print("Time: " + str(end - start))

    #Add constraint2 of the formulation
    #Avoid two nodes on the same PE at the same time
    def addConstraint2(self, cycle_pe_literals):
        print("Adding C2...")
        start = time.time()
        for cycle in cycle_pe_literals:
            for pe in cycle_pe_literals[cycle]:
                tmp = []
                for i in range(len(cycle_pe_literals[cycle][pe])-1):
                    for j in range(i+1, len(cycle_pe_literals[cycle][pe])):
                        tmp.append(Or(Not(cycle_pe_literals[cycle][pe][i]), Not(cycle_pe_literals[cycle][pe][j])))
                if len(tmp) > 1:
                    tmp = And(tmp)
                elif len(tmp) == 0:
                    continue
                #tmp = And(tmp)
                self.s.add(tmp)
        end = time.time()
        print("Time: " + str(end - start))

    #Add constraint3 of the formulation
    #Map dependent nodes on neibours PEs
    def addConstraint3(self, II, c_n_it_p_literal, cycle_pe_literals):
        print("Adding C3...")
        start = time.time()
        all_dep_encoded = True
        for e in self.DFG.edges:
            if e.distance > 0:
                #backdependencies handled in a different way
                continue
            nodes = [e.source.id, e.destination.id]
            print(nodes)
            tmp = []
            
            for (cs,cd) in itertools.product(c_n_it_p_literal, c_n_it_p_literal):
                if (nodes[0] not in c_n_it_p_literal[cs]) or (nodes[1] not in c_n_it_p_literal[cd]):
                    continue
                ns = nodes[0]
                nd = nodes[1]

                for (it1, it2) in itertools.product(c_n_it_p_literal[cs][ns], c_n_it_p_literal[cd][nd]):
                    if it1 == it2 and cd > cs:
                        for (p1, p2) in itertools.product(c_n_it_p_literal[cs][ns][it1], c_n_it_p_literal[cd][nd][it2]):
                            if(self.isNeighbor(p1, p2)):
                                distance = self.getCycleDistance(cs, cd, II)
                                if distance == 1:
                                    tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))
                                elif distance > 1:
                                    tmp2 = []
                                    for ci in range(cs + 1, cd):
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))
                                    if len(tmp2) > 1:#before was only tmp append tmp2
                                        tmp.append(And(tmp2))
                                    elif len(tmp2) == 1:
                                        tmp.append(tmp2[0])
                                    #tmp.append(And(tmp2))
                                    if p1 == p2:
                                        tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))
                    elif abs(it1 - it2) == 1 and it1 < it2 and cd <= cs:
                        for (p1, p2) in itertools.product(c_n_it_p_literal[cs][ns][it1], c_n_it_p_literal[cd][nd][it2]):
                            if(self.isNeighbor(p1, p2)):
                                distance = self.getCycleDistance(cs, cd, II)
                                if distance == 1:
                                    tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))
                                elif distance > 1:
                                    tmp2 = []
                                    for ci in range(cs + 1, II):
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))
                                    for ci in range(0, cd):
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))

                                    if len(tmp2) > 1:#before was only len(tmp2) != 0:
                                        tmp.append(And(tmp2))
                                    elif len(tmp2) == 1:
                                        tmp.append(tmp2[0])

                                    if p1 == p2:
                                        tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))
                                elif distance == 0:
                                    tmp2 = []
                                    if p1 == p2:
                                        continue
                                    for ci in range(0, II):
                                        if ci == cs:
                                            continue
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))
                                    if len(tmp2) > 1:#before was only len(tmp2) != 0:
                                        tmp.append(And(tmp2))
                                    elif len(tmp2) == 1:
                                        tmp.append(tmp2[0])
                                else:
                                    print("Should not be here 2")
                    
            if len(tmp) == 0:
                print("No constraint for this dep. Need to check")
                all_dep_encoded = False
                print(nodes[0], nodes[1])
                break
            self.s.add(Or(tmp))
        
        if not all_dep_encoded:
            self.s.reset()
            return all_dep_encoded
        all_dep_encoded = True
        #handle backdeps
        print("Adding back...")	
        for e in self.DFG.edges:
            if e.distance < 1:
                #backdependencies handled in a different way
                continue 
            nodes = [e.source.id, e.destination.id]
            print(nodes)
            tmp = []
            for (cs,cd) in itertools.product(c_n_it_p_literal, c_n_it_p_literal):
                if (nodes[0] not in c_n_it_p_literal[cs]) or (nodes[1] not in c_n_it_p_literal[cd]):
                    continue
                ns = nodes[0]
                nd = nodes[1]
                for (it1, it2) in itertools.product(c_n_it_p_literal[cs][ns], c_n_it_p_literal[cd][nd]):
                    if abs(it1 - it2) > 1:
                        continue
                    if it1 == it2 and cs > cd:
                        for (p1, p2) in itertools.product(c_n_it_p_literal[cs][ns][it1], c_n_it_p_literal[cd][nd][it2]):
                            if(self.isNeighbor(p1, p2)):
                                distance = self.getCycleDistance(cs, cd, II)
                                if distance == 1:
                                    tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))
                                elif distance > 1:
                                    tmp2 = []
                                    for ci in range(cs + 1, II):
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))
                                    for ci in range(0, cd):
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))

                                    if len(tmp2) > 1:#before was only len(tmp2) != 0:
                                        tmp.append(And(tmp2))
                                    elif len(tmp2) == 1:
                                        tmp.append(tmp2[0])

                                    if p1 == p2:
                                        tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))

                    elif it1 > it2 and cs < cd:
                        for (p1, p2) in itertools.product(c_n_it_p_literal[cs][ns][it1], c_n_it_p_literal[cd][nd][it2]):
                            if(self.isNeighbor(p1, p2)):
                                distance = self.getCycleDistance(cs, cd, II)
                                if distance == 1:
                                    tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))
                                elif distance > 1:
                                    tmp2 = []
                                    for ci in range(cs + 1, II):
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))
                                    for ci in range(0, cd):
                                        tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))

                                    if len(tmp2) > 1:#before was only len(tmp2) != 0:
                                        tmp.append(And(tmp2))
                                    elif len(tmp2) == 1:
                                        tmp.append(tmp2[0])

                                    if p1 == p2:
                                        tmp.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2]))
                    elif it1 == it2 and cs == cd:
                        #we need this to take care of loop carried dependencies (usually between phi nodes)
                        #I will not find problems in the schedule because if there is a dependency and a
                        #backdependecy for two nodes, the sat solver is not going to take this solution
                        #because it will make the data dependency constraint unusable and viceversa.
                        for (p1, p2) in itertools.product(c_n_it_p_literal[cs][ns][it1], c_n_it_p_literal[cd][nd][it2]):
                            if(self.isNeighbor(p1, p2)):
                                if p1 == p2:
                                    continue
                                tmp2 = []
                                for ci in range(0, II):
                                    if ci == cs:
                                        continue
                                    tmp2.append(And(c_n_it_p_literal[cs][ns][it1][p1], c_n_it_p_literal[cd][nd][it2][p2], cycle_pe_literals[ci][p1]))
                                if len(tmp2) > 1:#before was only len(tmp2) != 0:
                                    tmp.append(And(tmp2))
                                elif len(tmp2) == 1:
                                    tmp.append(tmp2[0])
                                        
                    
            if len(tmp) == 0:
                print("No constraint for this backdep. Need to check")
                print(nodes[0], nodes[1])
                all_dep_encoded = False
                break
            self.s.add(Or(tmp))

        if not all_dep_encoded:
            self.s.reset()
            return all_dep_encoded
        #OUTPUT OF SMT AND CNF FILE
        
        #with open(self.benchmark + "_" + str(II) + ".smt2", "w") as f:
        #    f.write(self.s.to_smt2())
        #with open(self.benchmark + "_" + str(II) + ".cnf", "w") as f:
        #    f.write(self.s.dimacs())
        end = time.time()
        print("Time: " + str(end - start))
        return all_dep_encoded

    #Find mapping of the DFG starting from the MII
    def findMapping(self, node_pes):
        
        II = self.getStartingII()

        self.generateMS()

        solution = False
        while not solution:
            print("II: " + str(II))
            self.generateKMS(II)
            nit = math.ceil((self.scheduleLen + 1) / II)
            print("nit " + str(self.scheduleLen + 1)+"/"+str(II) +"= "+str((self.scheduleLen + 1) / II) +"= "+str(nit))
            
            iterations = {}
            print("KMS")
            for i in range(0,II):
                print(self.KMS[i])

            for it in range(0, nit):
                if it not in iterations:
                    iterations[it] = {}
                for t in self.KMS:
                    if t not in iterations[it]:
                        iterations[it][t] = []
                    for p in self.KMS[t]:
                        if p[0] == it:
                            iterations[it][t].append(p[1])

            #for it in iterations:
            #    print("Iteration " + str(it))
            #    for c in iterations[it]:
            #        print("Cycle: " + str(c) + " " + str(iterations[it][c]))

            #Generate all the literals for the formulation
            literals = []
            for it in iterations:
                for c in iterations[it]:
                    for NodeId in iterations[it][c]:
                        if len(node_pes) != 0:
                            for pe in node_pes[NodeId]:
                                literals.append((Bool("v_%s,%s,%s,%s" % (str(NodeId),str(pe),str(c),str(it))), NodeId, pe, c, it))
                        else:
                            for pe in range(0, self.CGRA_X * self.CGRA_Y):
                                literals.append((Bool("v_%s,%s,%s,%s" % (str(NodeId),str(pe),str(c),str(it))), NodeId, pe, c, it))
            
            #Group literals in Map(nodeid, Value = 'list of literals')
            node_literals = {}
            for l in literals:
                literal = l[0]
                nodeid = l[1]
                if nodeid not in node_literals:
                    node_literals[nodeid] = []
                node_literals[nodeid].append(literal)
            
            #1)
            #exactly one variable True for each node
            self.addConstraint1(node_literals)


            #Group literals in Map(cycle, Value = Map(pe, literal))
            cycle_pe_literals = {}
            for l in literals:
                literal = l[0]
                pe = l[2]
                cycle = l[3]
                
                if cycle not in cycle_pe_literals:
                    cycle_pe_literals[cycle] = {}

                if pe not in cycle_pe_literals[cycle]:
                    cycle_pe_literals[cycle][pe] = []

                cycle_pe_literals[cycle][pe].append(literal)
            #2)
            #At most one node on one PE at a given time
            self.addConstraint2(cycle_pe_literals)
            

            #precompute data
            for ci in cycle_pe_literals:
                for pj in cycle_pe_literals[ci]:
                    #cycle_pe_literals[ci][pj] = Not(Or(cycle_pe_literals[ci][pj]))
                    if len(cycle_pe_literals[ci][pj]) == 1:
                        cycle_pe_literals[ci][pj] = Not(cycle_pe_literals[ci][pj][0])
                        #print(len(cycle_pe_literals[ci][pj]), ci, pj)	
                    else:
                        cycle_pe_literals[ci][pj] = Not(Or(cycle_pe_literals[ci][pj]))

            #Group literals in Map(cycle, Value = Map(nodeid, Map(iteration,Map(pe, literal)))
            c_n_it_p_literal = {}
            for l in literals:

                literal = l[0]
                nodeid = l[1]
                pe = l[2]
                cycle = l[3]
                iteration = l[4]
                
                if cycle not in c_n_it_p_literal:
                    c_n_it_p_literal[cycle] = {}

                if nodeid not in c_n_it_p_literal[cycle]:
                    c_n_it_p_literal[cycle][nodeid] = {}
                
                if iteration not in c_n_it_p_literal[cycle][nodeid]:
                    c_n_it_p_literal[cycle][nodeid][iteration] = {}

                if pe not in c_n_it_p_literal[cycle][nodeid][iteration]:
                    c_n_it_p_literal[cycle][nodeid][iteration][pe] = ''

                c_n_it_p_literal[cycle][nodeid][iteration][pe] = literal
                    
            #3)
            #encode all dependencies
            if not self.addConstraint3(II, c_n_it_p_literal, cycle_pe_literals):
                print("Can't encode all the dependency - II too small\nManually add routing nodes to solve this dep or let the code run.")
                II += 1
                continue

            start = time.time()

            if self.s.check() == sat:
                #model_number = 0
                #while self.s.check() == sat:
                #    
                #    print("MODEL " + str(model_number))
                #    model_number+=1
                #    m = self.s.model()
                #    block = []  
                #    for z3_decl in m: # FuncDeclRef
                #        arg_domains = []
                #        for i in range(z3_decl.arity()):
                #            domain, arg_domain = z3_decl.domain(i), []
                #            for j in range(domain.num_constructors()):
                #                arg_domain.append( domain.constructor(j) () )
                #            arg_domains.append(arg_domain)
                #        for args in itertools.product(*arg_domains):
                #            block.append(z3_decl(*args) != m.eval(z3_decl(*args)))
                #    self.s.add(Or(block))
                #    if model_number == 150:
                #        break
                solution = True
                print("SAT")
                m = self.s.model()
                #parse z3 output
                for t in m.decls():
                    if is_true(m[t]):
                        tmp = str(t).split('_')[1].split(',')
                        p = int(tmp[1])
                        n = int(tmp[0])
                        t = int(tmp[2])
                        it = int(tmp[3])
                        print("Node " + str(n) + " on PE " + str(p) + " at time " + str(t) + " of it " + str(it))
                        if t not in self.kernel:
                            self.kernel[t] = {}
                        if p not in self.kernel[t]:
                            self.kernel[t][p] = -1
                        self.kernel[t][p] = n

                        if (it * II + t) not in self.schedule:
                            self.schedule[it*II + t] = []

                        self.schedule[it*II + t].append(n)

                print("Kernel")
                for i in range(0, len(self.kernel)):
                    tmps = "[ "
                    for p in self.kernel[i]:
                        tmps += str(self.kernel[i][p]) + " "
                    print(tmps + "]")

                print("Schedule")
                for i in range(0, len(self.schedule)):
                    print(self.schedule[i])
                
            else:
                self.s.reset()
                II += 1

            end = time.time()
            print("Time: " + str(end - start))

        if solution == False:
            print("Mapping not found...\nLast II: " + str(II))
            exit(0)

        self.II = II

        
        self.generateProlog()
        self.generateEpilog()
        self.generatePKE()

        
        #The code below needs to be adapted. 
        #It's used to generate more mapping for a given DFG at a given IIå
        #print("Solving...")
        #start = time.time()
        ##TODO: add function to generate different models (useful during RA)
        #model_number = 0
        #while self.s.check() == sat:
        #    solution = "False"
        #    print("MODEL " + str(model_number))
        #    model_number+=1
        #    
        #    block = []
        #    for z3_decl in m: # FuncDeclRef
        #        arg_domains = []
        #        for i in range(z3_decl.arity()):
        #            domain, arg_domain = z3_decl.domain(i), []
        #            for j in range(domain.num_constructors()):
        #                arg_domain.append( domain.constructor(j) () )
        #            arg_domains.append(arg_domain)
        #        for args in itertools.product(*arg_domains):
        #            block.append(z3_decl(*args) != m.eval(z3_decl(*args)))
        #    self.s.add(Or(block))
        #    if model_number == 1:
        #        break
        #print("Number of solutions: " + str(iii))

        #end = time.time()
        #print("Time: " + str(end - start))

    #Return True if pe1 and pe2 are neighbour on a 2D-mesh shaped topology
    #If the topology is different this function must be changed
    def isNeighbor(self, pe1, pe2):
        i1 = pe1 // self.CGRA_Y
        j1 = pe1 % self.CGRA_Y

        i2 = pe2 // self.CGRA_Y
        j2 = pe2 % self.CGRA_Y

        #same row
        if i1 == i2:
            if (pe1 == pe2 + 1) or (pe1 == pe2 - 1):
                return True
            if abs(pe1 - pe2) == self.CGRA_Y - 1:
                return True

        #same col
        if j1 == j2:
            if (pe1 == pe2 + self.CGRA_Y) or (pe1 == pe2 - self.CGRA_Y):
                return True
            if abs(i1 - i2) == self.CGRA_X - 1:
                return True
        #center
        if pe1 == pe2:
            return True

        return False

    def getCycleDistance(self, cs, cd, II):
        return (cd - cs + II) % II

    def generateProlog(self):

        first_row = []
        for p in self.kernel[0]:
            first_row.append(self.kernel[0][p])

        contained = True
        shift = 0

        for t in range(len(self.schedule)-1, -1, -1):

            contained = True
            for n in self.schedule[t]:
                if n not in first_row:
                    contained = False
            
            if contained:
                for i in range(t - 1, -1, -1):
                    for n in self.schedule[i]:
                        if (i + shift) not in self.prolog:
                            self.prolog[i + shift] = []
                        self.prolog[i + shift].append(n)
                shift += self.II
        #print(self.prolog)

    def generateEpilog(self):
        last_row = []
        for p in self.kernel[len(self.kernel) - 1]:
            last_row.append(self.kernel[len(self.kernel) - 1][p])

        contained = True

        for t in range(0, len(self.schedule)):
            
            contained = True
            for n in self.schedule[t]:
                if n not in last_row:
                    contained = False
            
            if contained:
                for i in range(t + 1, len(self.schedule)):
                    for n in self.schedule[i]:
                        if ( i - t - 1) not in self.epilog:
                            self.epilog[i - t - 1] = []
                        self.epilog[i - t - 1].append(n)
        #print(self.epilog)

    #Generate Prolog+Kernel+Epilog
    def generatePKE(self):

        self.pke.clear()
        n_pe = {}

        for t in self.kernel:
            for p in self.kernel[t]:
                if self.kernel[t][p] not in n_pe:
                    n_pe[self.kernel[t][p]] = -1
                n_pe[self.kernel[t][p]] = p

        t = 0

        for i in range(0, len(self.prolog)):
            if t not in self.pke:
                self.pke[t] = {}
            for n in self.prolog[i]:
                if n_pe[n] not in self.pke[t]:
                    self.pke[t][n_pe[n]] = -1
                self.pke[t][n_pe[n]] = n

            t += 1


        for i in range(0, len(self.kernel)):
            if t not in self.pke:
                self.pke[t] = {}
            for p in self.kernel[i]:
                if p not in self.pke[t]:
                    self.pke[t][p] = -1
                self.pke[t][p] = self.kernel[i][p]

            t += 1



        for i in range(0, len(self.epilog)):
            if t not in self.pke:
                self.pke[t] = {}
            for n in self.epilog[i]:
                if n_pe[n] not in self.pke[t]:
                    self.pke[t][n_pe[n]] = -1
                self.pke[t][n_pe[n]] = n

            t += 1

    #Get schedule found by the Z3
    def getSchedule(self):
        if len(self.schedule) > 0:
            return self.schedule
        return None
    
    def getProlog(self):
        if len(self.prolog) > 0:
            return self.prolog
        return None

    def getKernel(self):
        if len(self.kernel) > 0:
            return self.kernel
        return None

    def getEpilog(self):
        if len(self.epilog) > 0:
            return self.epilog
        return None

    def getPKE(self):
        if len(self.pke) > 0:
            return self.pke
        return None
