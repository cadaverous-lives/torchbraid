#!/bin/bash
#SBATCH -p pbatch
#SBATCH -N 4
#SBATCH -A paratime
#SBATCH -t 00:15:00
#SBATCH -o parallel_studies/sc_fmg_out
#SBATCH -e parallel_studies/sc_fmg_err

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !! 
__conda_setup="$('/usr/bin/conda' 'shell.bash' 'hook' 2> /dev/null)" 
if [ $? -eq 0 ]; then
    eval "$__conda_setup" 
else
    if [ -f "/usr/etc/profile.d/conda.sh" ]; then
        . "/usr/etc/profile.d/conda.sh" 
    else
        export PATH="/usr/bin:$PATH" 
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
 
conda activate py37 
 
export OMP_NUM_THREADS=3
 
export PYTHONPATH="$HOME/torchbraid/torchbraid" 
export PYTHONPATH="$HOME/torchbraid:$PYTHONPATH" 

savedir="parallel_studies"

args="--lp-iters 2 --lp-levels 4 --lp-use-fmg"
# args="--lp-iters 2 --lp-levels 4"

echo serial:
echo python3 test_spatial_coarsening.py ${args} --lp-levels 1
srun -N 1 -n 1 --cpu-bind=verbose --mpibind=off python3 test_spatial_coarsening.py ${args} --lp-levels 1 	> ${savedir}/serial.out
 
echo control:
echo python3 test_spatial_coarsening.py ${args}
srun -N 4 -n 64 --cpu-bind=verbose --mpibind=off python3 test_spatial_coarsening.py ${args} 			> ${savedir}/fmg_sc0.out
 
echo coarsening:
echo python3 test_spatial_coarsening.py ${args} --lp-sc-levels 2
srun -N 4 -n 64 --cpu-bind=verbose --mpibind=off python3 test_spatial_coarsening.py ${args} --lp-sc-levels 2	> ${savedir}/fmg_sc2.out

echo coarsening:
echo python3 test_spatial_coarsening.py ${args} --lp-sc-levels 1
srun -N 4 -n 64 --cpu-bind=verbose --mpibind=off python3 test_spatial_coarsening.py ${args} --lp-sc-levels 1	> ${savedir}/fmg_sc1.out

echo coarsening:
echo python3 test_spatial_coarsening.py ${args} --lp-sc-levels 1 2
srun -N 4 -n 64 --cpu-bind=verbose --mpibind=off python3 test_spatial_coarsening.py ${args} --lp-sc-levels 1 2 	> ${savedir}/fmg_sc12.out

echo coarsening:
echo python3 test_spatial_coarsening.py ${args} --lp-sc-levels -1
srun -N 4 -n 64 --cpu-bind=verbose --mpibind=off python3 test_spatial_coarsening.py ${args} --lp-sc-levels -1   > ${savedir}/fmg_sc012.out

