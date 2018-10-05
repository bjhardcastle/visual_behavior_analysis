
from visual_behavior.ophys.io.create_analysis_files import create_analysis_files



if __name__ == '__main__':
    import sys

    import matplotlib
    matplotlib.use('Agg')

    experiment_id = sys.argv[1]
    cache_dir = r'/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/visual_behavior_pilot_analysis'
    create_analysis_files(experiment_id, cache_dir, overwrite_analysis_files=True)
