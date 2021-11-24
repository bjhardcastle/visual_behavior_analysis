#!/usr/bin/env python

import os
import argparse
import numpy as np
import pandas as pd
import visual_behavior.data_access.loading as loading
import visual_behavior.ophys.io.create_multi_session_df as io


if __name__ == '__main__':
    # define args
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_code', type=str, help='project code to use')
    parser.add_argument('--session_number', type=str, help='session number to use')
    args = parser.parse_args()
    project_code = args.project_code
    session_number = float(args.session_number)

    print(project_code, session_number)

    # params for stim response df creation
    time_window = [-3, 3.1]
    interpolate = True
    output_sampling_rate = 30
    response_window_duration_seconds = 0.5
    use_extended_stimulus_presentations = False

    # set up conditions to make multi session dfs for
    physio_data_types = ['filtered_events', 'events', 'dff']
    behavior_data_types = ['pupil_width', 'running_speed', 'lick_rate']

    physio_conditions = [['cell_specimen_id', 'omitted'],
                         ['cell_specimen_id', 'omitted', 'epoch'],
                         ['cell_specimen_id', 'is_change'],
                         ['cell_specimen_id', 'is_change', 'epoch'],
                         ['cell_specimen_id', 'is_change', 'image_name'],
                         ['cell_specimen_id', 'is_change', 'image_name', 'epoch'],
                         ['cell_specimen_id', 'is_change', 'hit'],
                         ['cell_specimen_id', 'is_change', 'pre_change', 'epoch'],
                         ['cell_specimen_id', 'hit', 'miss', 'epoch']]

    behavior_conditions = [['omitted'],
                           ['omitted', 'epoch']
                           ['is_change'],
                           ['is_change', 'epoch'],
                           ['is_change', 'image_name'],
                           ['is_change', 'image_name', 'epoch'],
                           ['is_change', 'hit'],
                           ['is_change', 'pre_change', 'epoch'],
                           ['hit', 'miss', 'epoch']]


    # event types corresponding to the above physio and behavior conditions - must be in same sequential order
    event_types_for_conditions = ['omissions', 'omissions',
                                    'changes', 'changes', 'changes',
                                    'changes', 'changes',
                                    'all', 'all']


    # # create dfs for all data types and conditions for physio data
    # for data_type in physio_data_types:
    #     for i, conditions in enumerate(physio_conditions):
    #         event_type = event_types_for_conditions[i]
    #         print('creating multi_session_df for', data_type, event_type, conditions)
    #         df = io.get_multi_session_df(project_code, session_number, conditions, data_type, event_type,
    #                              time_window=time_window, interpolate=interpolate, output_sampling_rate=output_sampling_rate,
    #                              response_window_duration_seconds=response_window_duration_seconds,
    #                                      use_extended_stimulus_presentations=use_extended_stimulus_presentations)

    # create dfs for all data types and conditions for behavior data
    for data_type in behavior_data_types:
        for i, conditions in enumerate(behavior_conditions):
            event_type = event_types_for_conditions[i]
            print('creating multi_session_df for', data_type, event_type, conditions)
            df = io.get_multi_session_df(project_code, session_number, conditions, data_type, event_type,
                                         time_window=time_window, interpolate=interpolate,
                                         output_sampling_rate=output_sampling_rate,
                                         response_window_duration_seconds=response_window_duration_seconds,
                                         use_extended_stimulus_presentations=use_extended_stimulus_presentations)
