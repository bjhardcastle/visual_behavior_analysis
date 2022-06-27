
import os
import argparse
import sys
import time
import pandas as pd
import numpy as  np
from simple_slurm import Slurm

# define the conda environment
conda_environment = 'vba'

# define the job record output folder
job_dir = r"//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/cluster_jobs/clustering"
# make the job record location if it doesn't already exist
os.mkdir(job_dir) if not os.path.exists(job_dir) else None

# env path
python_path = os.path.join(
    os.path.expanduser("~"),
    'anaconda3',
    'envs',
    conda_environment,
    'bin',
    'python'
)

# create slurm instance
slurm = Slurm(
    cpus_per_task=10,
    job_name='shuffle_clustering',
    mem = '8g',
    time = '2:00:00',
    partition = 'braintv',
    output=f'{job_dir}/{Slurm.JOB_ARRAY_MASTER_ID}_{Slurm.JOB_ARRAY_ID}.out',
)

shuffle_types = ['experience', 'experience_within_cell', 'regressors', 'all']
n_boots = int(10)

for shuffle_type in shuffle_types:
    print('running ' + method + ' ' + str(n_cluster))
    slurm.sbatch('{} ../scripts/run_shuffle_clustering.py --shuffle_type {}  --n_boots {}'.format(
                python_path,
                shuffle_type,
                n_boots,
                )
            )
