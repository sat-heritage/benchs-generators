% pigeonhole
% n+1 pigeons in n holes: unsatisfiable, and famously hard for resolution.
% The parameter: minizinc-bridge pigeonhole.mzn -D "n=10"
int: n;
array[1..n+1] of var 1..n: hole;
constraint forall(i, j in 1..n+1 where i < j) (hole[i] != hole[j]);
solve satisfy;
