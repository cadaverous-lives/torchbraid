#!/bin/bash
#SBATCH -p pdebug
#SBATCH -N 1
#SBATCH -A paratime
#SBATCH -t 00:15:00
#SBATCH -o parallel_studies/test_out
#SBATCH -e parallel_studies/test_err

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
 
srun -N 1 -n 2 --cpus-per-task=9 --cpu-bind=verbose --mpibind=off python3 test_spatial_coarsening.py --lp-levels 4 --lp-sc-levels 2
 
echo " "
echo Run String Used here is:
echo python3 test_spatial_coarsening.py --lp-levels 4 --lp-sc-levels 2
