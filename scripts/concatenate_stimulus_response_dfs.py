#!/usr/bin/env python

import os
import numpy as np
import pandas as pd
import visual_behavior.data_access.loading as loading


if __name__ == '__main__':
    import sys
    project_code = sys.argv[1][1:-1]
    session_number = int(sys.argv[2][:-1])
    print(project_code, session_number)
    print(type(project_code), type(session_number))
    save_dir = r'/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/decoding/data'

    experiments_table = loading.get_filtered_ophys_experiment_table()
    experiments = experiments_table[(experiments_table.project_code == project_code) &
                                    (experiments_table.session_number == session_number)].copy()

    response_df = pd.DataFrame()
    for ophys_experiment_id in experiments.index.values:
        try:
            print(ophys_experiment_id, '-', np.where(experiments.ophys_experiment_id.unique() == ophys_experiment_id)[0][0],
                  'out of ', len(experiments.ophys_experiment_id.unique()))
            dataset = loading.get_ophys_dataset(ophys_experiment_id)
            analysis = ResponseAnalysis(dataset, use_extended_stimulus_presentations=False)

            stim_response_df = analysis.get_response_df(df_name='stimulus_response_df')
            sdf = stim_response_df.copy()
            sdf['trace'] = [sdf.iloc[index].trace[sdf.iloc[index].trace_timestamps < 0] for index in sdf.index.values]
            sdf['ophys_experiment_id'] = ophys_experiment_id
            sdf['ophys_session_id'] = loading.get_ophys_session_id_for_ophys_experiment_id(ophys_experiment_id)
            sdf['ophys_frame_rate'] = analysis.ophys_frame_rate
            sdf = sdf[['ophys_experiment_id', 'ophys_session_id','stimulus_presentations_id', 'cell_specimen_id', 'trace',
                       'trace_timestamps', 'mean_response', 'baseline_response', 'ophys_frame_rate']]
            response_df = pd.concat([response_df, sdf])
        except Exception as e:
            print('problem for ophys_session_id:', ophys_session_id)
            print(e)
    response_df.to_hdf(os.path.join(save_dir, 'stimulus_response_df_'+project_code+'_session_'+str(session_number)+'.h5'), key='df')
    print('done')

