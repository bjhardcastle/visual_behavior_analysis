import os
# import sys
# import platform
# if platform.system() == 'Linux':
#     # sys.path.append('/allen/programs/braintv/workgroups/nc-ophys/Doug/pbstools')
#     sys.path.append('/allen/programs/braintv/workgroups/nc-ophys/nick.ponvert/src/pbstools')
# from pbstools import PythonJob  # flake8: noqa: E999

from simple_slurm import Slurm

import visual_behavior.data_access.loading as loading

# python file to execute on cluster
python_file = r"/home/marinag/visual_behavior_analysis/scripts/create_multi_session_df.py"

# conda environment to use
conda_environment = 'visual_behavior_sdk'

# build the python path
# this assumes that the environments are saved in the user's home directory in a folder called 'anaconda2'
# this will be user setup dependent.
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

# instantiate a Slurm object
slurm = Slurm(
    mem = '20g', #'24g'
    cpus_per_task=5,
    time = '100:00:00',
    partition = 'braintv',
    job_name= 'multi_session_df',
    output = f'{stdout_location}/{Slurm.JOB_ARRAY_MASTER_ID}_{Slurm.JOB_ARRAY_ID}.out',
)

# get experiments to iterate over
experiments_table = loading.get_filtered_ophys_experiment_table(release_data_only=True)

# call the `sbatch` command to run the jobs.
for project_code in experiments_table.project_code.unique()[:1]:
    for session_number in experiments_table.session_number.unique()[:1]:
        # slurm.sbatch('{} {} --project_code {} --session_number {}'.format(
        #         python_path,
        #         python_file,
        #         project_code,
        #         session_number,
        #     )
        slurm.sbatch(python_path+' '+python_file+' --project_code '+str(project_code)+' --session_number'+' '+str(session_number))
        )



#
# job_settings = {'queue': 'braintv',
#                 'mem': '100g',
#                 'walltime': '20:00:00',
#                 'ppn': 1,
#                 'jobdir': jobdir,
#                 }
#
# experiments_table = loading.get_filtered_ophys_experiment_table(release_data_only=True)
#
# for project_code in experiments_table.project_code.unique():
#     for session_number in experiments_table.session_number.unique():
#
#         PythonJob(
#             python_file,
#             python_executable='/home/marinag/anaconda2/envs/visual_behavior_sdk/bin/python',
#             python_args=[project_code, session_number],
#             conda_env=None,
#             jobname='multi_session_df_' + project_code + '_' + str(session_number),
#             **job_settings
#         ).run(dryrun=False)
