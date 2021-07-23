import os
from simple_slurm import Slurm

import visual_behavior.data_access.loading as loading

# python file to execute on cluster
python_file = r"/home/marinag/visual_behavior_analysis/scripts/create_multi_session_df.py"

# conda environment to use
conda_environment = 'visual_behavior_sdk'

# build the python path
# this assumes that the environments are saved in the user's home directory in a folder called 'anaconda2'
python_path = os.path.join(
    os.path.expanduser("~"),
    'anaconda2',
    'envs',
    conda_environment,
    'bin',
    'python'
)

# define the job record output folder
stdout_location = r'/allen/programs/braintv/workgroups/nc-ophys/Marina/ClusterJobs/JobRecords'



# get experiments to iterate over
experiments_table = loading.get_filtered_ophys_experiment_table(release_data_only=True)

# call the `sbatch` command to run the jobs.
for project_code in experiments_table.project_code.unique()[:1]:
    for session_number in experiments_table.session_number.unique()[:3]:

        # instantiate a Slurm object
        slurm = Slurm(
            mem='60g',  # '24g'
            cpus_per_task=10,
            time='60:00:00',
            partition='braintv',
            job_name='multi_session_df_'+project_code+'_'+str(session_number),
            output=f'{stdout_location}/{Slurm.JOB_ARRAY_MASTER_ID}_{Slurm.JOB_ARRAY_ID}.out',
        )

        slurm.sbatch(python_path+' '+python_file+' --project_code '+str(project_code)+' --session_number'+' '+str(session_number))


