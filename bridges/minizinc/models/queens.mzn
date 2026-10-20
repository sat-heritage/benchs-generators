% queens
% n queens on an n by n board, no two on a line or a diagonal.
% The parameter: minizinc-bridge queens.mzn -D "n=12"
int: n;
array[1..n] of var 1..n: q;
constraint forall(i, j in 1..n where i < j) (
    q[i] != q[j] /\ q[i] + i != q[j] + j /\ q[i] - i != q[j] - j
);
solve satisfy;
