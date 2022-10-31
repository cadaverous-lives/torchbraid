# python3 test_spatial_coarsening.py --sgd --lp-levels 1  > ./experiments/grads/ml1_cycle_time.out
# python3 test_spatial_coarsening.py --sgd --lp-levels 3 > ./experiments/grads/ml3_cycle_time.out
# python3 test_spatial_coarsening.py --sgd --lp-levels 3 --lp-sc-levels 1 > ./experiments/grads/ml3_sc1_cycle_time.out
# python3 test_spatial_coarsening.py --sgd --lp-levels 3 --lp-sc-levels -1 > ./experiments/grads/ml3_sc-1_cycle_time.out

echo "python3 test_spatial_coarsening.py --lp-levels 1  > ./experiments/grads/ml1_cycle_time.out"
python3 test_spatial_coarsening.py --lp-levels 1  > ./experiments/grads/ml1_cycle_time.out
echo "python3 test_spatial_coarsening.py --lp-levels 3 > ./experiments/grads/ml3_cycle_time.out"
python3 test_spatial_coarsening.py --lp-levels 3 > ./experiments/grads/ml3_cycle_time.out
echo "python3 test_spatial_coarsening.py --lp-levels 3 --lp-sc-levels 1 > ./experiments/grads/ml3_sc1_cycle_time.out"
python3 test_spatial_coarsening.py --lp-levels 3 --lp-sc-levels 1 > ./experiments/grads/ml3_sc1_cycle_time.out
echo "python3 test_spatial_coarsening.py --lp-levels 3 --lp-sc-levels -1 > ./experiments/grads/ml3_sc-1_cycle_time.out"
python3 test_spatial_coarsening.py --lp-levels 3 --lp-sc-levels -1 > ./experiments/grads/ml3_sc-1_cycle_time.out