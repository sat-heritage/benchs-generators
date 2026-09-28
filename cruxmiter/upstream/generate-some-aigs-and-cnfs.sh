#!/bin/sh

size=10
while [ $size -le 32 ]
do
  seed=0
  while [ $seed -lt 10 ]
  do
    base=cruxmiter${size}seed$seed
    echo $base
    ./gencruxmitersmt $size $seed > smt/$base.smt
    boolector -nadd 0 -db smt/$base.smt > btor/$base.btor
    boolector -nadd 0 -dai btor/$base.btor > aig/$base.aig
    aigtocnf aig/$base.aig > cnf/$base.cnf
    seed=`expr $seed + 1`
  done
  size=`expr $size + 1`
done
