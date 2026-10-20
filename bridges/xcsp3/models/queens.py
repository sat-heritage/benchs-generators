# queens
# n queens on an n by n board, no two on a line or a diagonal.
from pycsp3 import *

n = data or 8

q = VarArray(size=n, dom=range(n))

satisfy(
    AllDifferent(q),
    [q[i] + i != q[j] + j for i in range(n) for j in range(i)],
    [q[i] - i != q[j] - j for i in range(n) for j in range(i)],
)
