# SAT-MapIt: A SAT-based Modulo Scheduling Mapper for Coarse Grain Reconfigurable Architectures

This is a Lite version of the original tool. It does not generate assembly code or do Register Allocation.

### Abstract:

Coarse-Grain Reconfigurable Arrays (CGRAs) are emerging low-power architectures aimed at accelerating compute-intensive application loops.
The acceleration that a CGRA can ultimately provide, however, heavily depends on the quality of the mapping, i.e. on how effectively the loop is compiled onto the given platform. State of the Art compilation techniques achieve mapping through modulo scheduling, a strategy which  attempts to minimize the II (Iteration Interval) needed to execute a loop, and they do so usually through well known graph algorithms, such as Max-Clique Enumeration.


We address the mapping problem through a SAT formulation, instead, and thus explore the solution space more effectively than current SoA tools.
To formulate the SAT problem, we introduce an ad-hoc schedule called the Kernel Mobility Schedule (KMS), which we use in conjunction with  the data-flow graph and the architectural information of the CGRA in order to create a set of boolean statements that describe all constraints to be obeyed by the mapping for a given II. We then let  the SAT solver efficiently navigate this complex space. As in other SoA techniques, the process is iterative: if a valid mapping does not exist for the given II, the II is increased and a new KMS and set of constraints is generated and solved.

Our experimental results show that SAT-MapIt obtains better results compared to SoA alternatives in 47.72% of the benchmarks explored: sometimes finding a lower II, and others even finding a valid mapping when none could previously be found.


### Usage
SAT-MapIt Lite inputs and usage.

1) Install python dependency: `python3 -m install z3-solver`
2) Setup input file and CGRA dimensions:
	`path="/home/my/path/to/files/"`
	`benchmark="sqrt321"`
	
	To change the CGRA dimensions update:
	`n_cols = 4`
	`n_rows = 4`

	To change the topology of the CGRA the method `isNeighbor` in `mapper.py` needs to be updated.

3) Execute the script and wait for the output: `python3 main.py`



The output of the script includes:
- mapping result
- running times of the different steps of the algorithm
- schedule obtained


