% magicsquare
% a magic square of order n: every row, column and diagonal of the same sum.
% The parameter: minizinc-bridge magicsquare.mzn -D "n=4"
int: n;
int: total = n * (n * n + 1) div 2;
array[1..n*n] of var 1..n*n: x;
constraint forall(i, j in 1..n*n where i < j) (x[i] != x[j]);
constraint forall(i in 1..n) (sum(j in 1..n) (x[(i-1)*n + j]) = total);
constraint forall(j in 1..n) (sum(i in 1..n) (x[(i-1)*n + j]) = total);
constraint sum(i in 1..n) (x[(i-1)*n + i]) = total;
constraint sum(i in 1..n) (x[(i-1)*n + n - i + 1]) = total;
solve satisfy;
