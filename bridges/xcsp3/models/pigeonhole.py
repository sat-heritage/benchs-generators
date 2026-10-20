# pigeonhole
# n+1 pigeons in n holes: unsatisfiable, and famously hard for resolution.
# The holes differ pairwise rather than through an all-different: that global
# constraint is settled by propagation before anything is encoded, and the point
# here is to produce the formula.
from pycsp3 import *

n = data or 8

hole = VarArray(size=n + 1, dom=range(n))

satisfy(
    hole[i] != hole[j] for i in range(n + 1) for j in range(i)
)
