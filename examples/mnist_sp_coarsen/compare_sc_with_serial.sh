# python3 main.py --percent-data 0.1 --lp-levels 1 > experiments/training_fashion/serial_tanh_2stp.out
# mpirun python3 main.py --percent-data 0.1 --lp-levels 3 --lp-braid-print 2 > experiments/training_fashion/parallel_tanh_2stp.out
# mpirun python3 main.py --percent-data 0.1 --lp-levels 3 --lp-braid-print 2 --lp-sc-levels 1 > experiments/training_fashion/parallel_sc_tanh_2stp.out
# mpirun python3 main.py --percent-data 0.1 --lp-levels 3 --lp-braid-print 2 --lp-sc-levels -1 > experiments/training_fashion/parallel_sc_tanh_full_2stp.out
# mpirun python3 main.py --percent-data 0.1 --lp-levels 2 --lp-braid-print 2 --lp-sc-levels -1 > experiments/training_fashion/parallel_sc_tanh_2stp_2lvl.out

# for SEED in {2..16}
 for SEED in {1..4}
 do
     echo $SEED
     python3 main.py --percent-data 0.1 --lp-levels 1 --seed $SEED                          | awk NF | grep -v 'Braid' > experiments/training/serial_tanh_$SEED.out
     mpirun python3 main.py --percent-data 0.1 --lp-levels 3 --seed $SEED                   | awk NF | grep -v 'Braid' > experiments/training/parallel_tanh_$SEED.out
     mpirun python3 main.py --percent-data 0.1 --lp-levels 3 --seed $SEED --lp-sc-levels 1  | awk NF | grep -v 'Braid' > experiments/training/parallel_sc_tanh_$SEED.out
     mpirun python3 main.py --percent-data 0.1 --lp-levels 3 --seed $SEED --lp-sc-levels -1 | awk NF | grep -v 'Braid' > experiments/training/parallel_sc_tanh_full_$SEED.out
     mpirun python3 main.py --percent-data 0.1 --lp-levels 2 --seed $SEED --lp-sc-levels -1 | awk NF | grep -v 'Braid' > experiments/training/parallel_sc_tanh_2lvl_$SEED.out
 done

# for SEED in {1..2}
# for SEED in "4"
# do
#     echo $SEED
#     python3 main.py --percent-data 0.1 --lp-levels 1 --seed $SEED                          | awk NF | grep -v 'Braid' > experiments/training/serial_tanh_$SEED.out
#     python3 main.py --percent-data 0.1 --lp-levels 3 --seed $SEED                   | awk NF | grep -v 'Braid' > experiments/training/parallel_tanh_$SEED.out
#     python3 main.py --percent-data 0.1 --lp-levels 3 --seed $SEED --lp-sc-levels 1  | awk NF | grep -v 'Braid' > experiments/training/parallel_sc_tanh_$SEED.out
#     python3 main.py --percent-data 0.1 --lp-levels 3 --seed $SEED --lp-sc-levels -1 | awk NF | grep -v 'Braid' > experiments/training/parallel_sc_tanh_full_$SEED.out
#     python3 main.py --percent-data 0.1 --lp-levels 2 --seed $SEED --lp-sc-levels -1 | awk NF | grep -v 'Braid' > experiments/training/parallel_sc_tanh_2lvl_$SEED.out
# done
