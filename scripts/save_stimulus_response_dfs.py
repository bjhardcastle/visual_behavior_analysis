import os
import argparse
import visual_behavior.data_access.loading as loading
from allensdk.brain_observatory.behavior.behavior_project_cache import VisualBehaviorOphysProjectCache
import mindscope_utilities.visual_behavior_ophys.data_formatting as vb_ophys


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ophys_experiment_id", type=int,
                        help="Experiment ID to process")
    args = parser.parse_args()
    ophys_experiment_id = args.ophys_experiment_id
    print(ophys_experiment_id)

    # set params for
    interpolate = True
    output_sampling_rate = 30
    time_window = [-3, 3.1]

    # set up save folder
    save_dir = loading.get_stimulus_response_df_dir(interpolate, int(output_sampling_rate))
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    # load cache and dataset
    cache_dir = loading.get_platform_analysis_cache_dir()
    cache = VisualBehaviorOphysProjectCache.from_s3_cache(cache_dir)
    dataset = cache.get_behavior_ophys_experiment(ophys_experiment_id)
    # create and save stimulus response df for all data types
    for data_type in ['filtered_events', 'dff', 'events', 'running_speed', 'pupil_diameter', 'lick_rate']:
        for event_type in ['all', 'omissions', 'changes']:
            sdf = vb_ophys.get_stimulus_response_df(dataset, data_type=data_type, event_type=event_type,
                                                    time_window=time_window, interpolate=interpolate,
                                                    output_sampling_rate=output_sampling_rate)
            # if file already exists, overwrite it
            filepath = loading.get_stimulus_response_df_filepath_for_experiment(ophys_experiment_id, data_type, event_type,
                                                                    interpolate=interpolate, output_sampling_rate=output_sampling_rate)
            if os.path.exists(filepath):
                os.remove(filepath)
                print('h5 file exists for', ophys_experiment_id, ' - overwriting')
            sdf.to_hdf(filepath, key='df')
            print('saved response df for', data_type)
