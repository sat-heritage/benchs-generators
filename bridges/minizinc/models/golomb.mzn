% golomb
% a Golomb ruler with n marks: all the distances between two marks differ.
% The length is bounded by n squared, so this stays a decision problem and n
% alone makes it scale.
% The parameter: minizinc-bridge golomb.mzn -D "n=8"
int: n;
int: len = n * n;
array[1..n] of var 0..len: mark;
constraint mark[1] = 0;
constraint forall(i in 1..n-1) (mark[i] < mark[i+1]);
constraint forall(i, j, k, l in 1..n where i < j /\ k < l /\ (i != k \/ j != l)) (
    mark[j] - mark[i] != mark[l] - mark[k]
);
solve satisfy;
