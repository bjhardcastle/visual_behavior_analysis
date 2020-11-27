from allensdk.internal.api import PostgresQueryMixin
from allensdk.internal.api.behavior_ophys_api import BehaviorOphysLimsApi
from allensdk.brain_observatory.behavior.behavior_ophys_session import BehaviorOphysSession
from allensdk.brain_observatory.behavior.behavior_project_cache import BehaviorProjectCache as bpc
# from allensdk.core.lazy_property import LazyProperty, LazyPropertyMixin
from visual_behavior.ophys.response_analysis import response_processing as rp
from visual_behavior.data_access import filtering
from visual_behavior.data_access import reformat
from visual_behavior.data_access import processing
from visual_behavior.data_access import utilities
import visual_behavior.database as db

import os
import glob
import h5py  # for loading motion corrected movie
import numpy as np
import pandas as pd
import configparser as configp  # for parsing scientifica ini files

import warnings

try:
    lims_dbname = os.environ["LIMS_DBNAME"]
    lims_user = os.environ["LIMS_USER"]
    lims_host = os.environ["LIMS_HOST"]
    lims_password = os.environ["LIMS_PASSWORD"]
    lims_port = os.environ["LIMS_PORT"]

    mtrain_dbname = os.environ["MTRAIN_DBNAME"]
    mtrain_user = os.environ["MTRAIN_USER"]
    mtrain_host = os.environ["MTRAIN_HOST"]
    mtrain_password = os.environ["MTRAIN_PASSWORD"]
    mtrain_port = os.environ["MTRAIN_PORT"]

    lims_engine = PostgresQueryMixin(
        dbname=lims_dbname,
        user=lims_user,
        host=lims_host,
        password=lims_password,
        port=lims_port
    )

    mtrain_engine = PostgresQueryMixin(
        dbname=mtrain_dbname,
        user=mtrain_user,
        host=mtrain_host,
        password=mtrain_password,
        port=mtrain_port
    )

except Exception as e:
    warn_string = 'failed to set up LIMS/mtrain credentials\n{}\n\ninternal AIBS users should set up environment variables appropriately\nfunctions requiring database access will fail'.format(
        e)
    warnings.warn(warn_string)

config = configp.ConfigParser()


# function inputs
# ophys_experiment_id
# ophys_session_id
# behavior_session_id
# ophys_container_id


#  RELEVANT DIRECTORIES

def get_super_container_plots_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/qc_plots/super_container_plots'


def get_container_plots_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/qc_plots/container_plots'


def get_session_plots_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/qc_plots/session_plots'


def get_experiment_plots_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/qc_plots/experiment_plots'


def get_analysis_cache_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/visual_behavior_production_analysis'


def get_events_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/event_detection'


def get_behavior_model_outputs_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/behavior_model_output'


def get_decoding_analysis_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/decoding'


def get_ophys_glm_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/ophys_glm'


# LOAD MANIFEST FILES (TABLES CONTAINING METADATA FOR BEHAVIOR & OPHYS DATASETS) FROM SDK CACHE (RECORD OF AVAILABLE DATASETS)


def get_cache_dir():
    """Get directory of data cache for analysis - this should be the standard cache location"""
    cache_dir = "//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/2020_cache/production_cache"
    return cache_dir


def get_manifest_path():
    """Get path to default manifest file for analysis"""
    manifest_path = os.path.join(get_cache_dir(), "manifest.json")
    return manifest_path


def get_visual_behavior_cache(manifest_path=None):
    """Get cache using default QC manifest path"""
    if manifest_path is None:
        manifest_path = get_manifest_path()
    cache = bpc.from_lims(manifest=get_manifest_path())
    return cache


def get_filtered_ophys_experiment_table(include_failed_data=False):
    """get ophys experiments table from cache, filters based on a number of criteria
        and adds additional useful columns to the table
        Saves a reformatted version of the table with additional columns
        added for future loading speed.
            filtering criteria:
                 project codes: VisualBehavior, VisualBehaviorTask1B,
                                visualBheaviorMultiscope, VisualBheaviorMultiscope4areasx2d
                experiment_workflow_state: "passed"
                "session_type": OPHYS_1_images_A', 'OPHYS_1_images_B',  'OPHYS_1_images_G',
                            'OPHYS_2_images_A_passive',  'OPHYS_2_images_B_passive',  'OPHYS_2_images_G_passive'
                            'OPHYS_3_images_A',  'OPHYS_3_images_B', 'OPHYS_3_images_G',
                            'OPHYS_4_images_A', 'OPHYS_4_images_B',  'OPHYS_4_images_H'
                            'OPHYS_5_images_A_passive', 'OPHYS_5_images_B_passive', 'OPHYS_5_images_H_passive'
                            'OPHYS_6_images_A',  'OPHYS_6_images_B',   'OPHYS_6_images_H'


    Keyword Arguments:
        include_failed_data {bool} -- If True, return all experiments including those from
                                        failed containers and receptive field mapping
                                        experiments. (default: {False})

    Returns:
        dataframe -- returns a dataframe with the following columns:
                    "ophys_experiment_id":
                    "ophys_session_id":
                    "ophys_behavior_session_id":
                    "container_id":
                    "project_code":
                    "container_workflow_state":
                    "experiment_workflow_state":
                    "session_name":
                    "session_number":
                    "equipment_name":
                    "date_of_acquisition":
                    "isi_experiment_id":
                    "specimen_id":
                    "sex":
                    "age_in_days":
                    "full_genotype":
                    "reporter_line":
                    "driver_line":
                    "imaging_depth":
                    "targeted_structure":
                    "published_at":
                    "super_container_id":
                    "cre_line":
                    "session_tags":
                    "failure_tags":
                    "exposure_number":
                    "location":
    """
    if 'filtered_ophys_experiment_table.csv' in os.listdir(get_cache_dir()):
        experiments = pd.read_csv(os.path.join(get_cache_dir(), 'filtered_ophys_experiment_table.csv'))
    else:
        cache = get_visual_behavior_cache()
        experiments = cache.get_experiment_table()
        experiments = reformat.reformat_experiments_table(experiments)
        experiments = filtering.limit_to_production_project_codes(experiments)
        experiments['has_events'] = [check_for_events_file(ophys_experiment_id) for ophys_experiment_id in
                                     experiments.index.values]
        experiments = experiments.set_index('ophys_experiment_id')
        experiments.to_csv(os.path.join(get_cache_dir(), 'filtered_ophys_experiment_table.csv'))
        experiments = experiments.reset_index()
        experiments = experiments.drop(columns='index', errors='ignore')
    if include_failed_data:
        experiments = filtering.limit_to_experiments_with_final_qc_state(experiments)
    else:
        experiments = filtering.limit_to_passed_experiments(experiments)
        experiments = filtering.limit_to_valid_ophys_session_types(experiments)
        experiments = filtering.remove_failed_containers(experiments)
    experiments['session_number'] = [int(session_type[6]) if 'OPHYS' in session_type else None for session_type in
                                     experiments.session_type.values]
    experiments = experiments.drop_duplicates(subset='ophys_experiment_id')
    experiments = experiments.set_index('ophys_experiment_id')
    return experiments


def get_filtered_ophys_session_table():
    """Get ophys sessions table from SDK, and add container_id and container_workflow_state to table,
        add session_workflow_state to table (defined as >1 experiment within session passing),
        and return only sessions where container and session workflow states are 'passed'.
        Includes Multiscope data.
            filtering criteria:
                project codes: VisualBehavior, VisualBehaviorTask1B,
                            VisualBehaviorMultiscope, VisualBehaviorMultiscope4areasx2d
                session workflow state: "passed"
                session_type: OPHYS_1_images_A', 'OPHYS_1_images_B',  'OPHYS_1_images_G',
                            'OPHYS_2_images_A_passive',  'OPHYS_2_images_B_passive',  'OPHYS_2_images_G_passive'
                            'OPHYS_3_images_A',  'OPHYS_3_images_B', 'OPHYS_3_images_G',
                            'OPHYS_4_images_A', 'OPHYS_4_images_B',  'OPHYS_4_images_H'
                            'OPHYS_5_images_A_passive', 'OPHYS_5_images_B_passive', 'OPHYS_5_images_H_passive'
                            'OPHYS_6_images_A',  'OPHYS_6_images_B',   'OPHYS_6_images_H'
    Returns:
        dataframe -- filtered version of the ophys sessions table(filtering criteria above) with the
                        following columns:
                        "ophys_session_id": df index, 9 digit unique identifier for an ophys session
                        "ophys_experiment_id": 9 digit unique identifier for an ophys experiment
                        "project_code": project code associated with the experiment and session
                        "session_name":
                        "session_type":
                        "equipment_name":
                        "date_of_acquisition":
                        "specimen_id":
                        "reporter_line":
                        "driver_line":
                        "at_least_one_experiment_passed":
                        "session_workflow_state":
                        "container_id":
                        "container_workflow_state":
    """
    cache = get_visual_behavior_cache()
    sessions = cache.get_session_table()
    sessions = filtering.limit_to_production_project_codes(sessions)
    sessions = reformat.add_all_qc_states_to_ophys_session_table(sessions)
    sessions = filtering.limit_to_valid_ophys_session_types(sessions)
    sessions = filtering.limit_to_passed_ophys_sessions(sessions)
    sessions = filtering.remove_failed_containers(sessions)
    sessions = reformat.add_model_outputs_availability_to_table(sessions)
    # sessions = sessions.reset_index()

    return sessions


# INSERT get_filtered_behavior_sessions_table() FUNCTION HERE #####


# LOAD OPHYS DATA FROM SDK AND EDIT OR ADD METHODS/ATTRIBUTES WITH BUGS OR INCOMPLETE FEATURES #

class BehaviorOphysDataset(BehaviorOphysSession):
    """Takes SDK ophys session object attributes and filters/reformats to compensate for bugs and missing SDK features.
        This class should eventually be entirely replaced by the BehaviorOphysSession SDK class when all requested features have been implemented.

        Returns:
            BehaviorOphysDataset object -- class with attributes & methods to access ophys and behavior data
                                                associated with an ophys_experiment_id (single imaging plane)
        """

    def __init__(self, api, include_invalid_rois=False,
                 eye_tracking_z_threshold: float = 3.0, eye_tracking_dilation_frames: int = 2):
        """
        :param session: BehaviorOphysSession {class} -- instance of allenSDK BehaviorOphysSession object for one ophys_experiment_id
        :param _include_invalid_rois: if True, do not filter out invalid ROIs from cell_specimens_table and dff_traces
        """
        super().__init__(api, eye_tracking_z_threshold=eye_tracking_z_threshold,
                         eye_tracking_dilation_frames=eye_tracking_dilation_frames)

        self._include_invalid_rois = include_invalid_rois

    @property
    def analysis_folder(self):
        analysis_cache_dir = get_analysis_cache_dir()
        candidates = [file for file in os.listdir(analysis_cache_dir) if str(self.ophys_experiment_id) in file]
        if len(candidates) == 1:
            self._analysis_folder = candidates[0]
        elif len(candidates) == 0:
            print('unable to locate analysis folder for experiment {} in {}'.format(self.ophys_experiment_id,
                                                                                    analysis_cache_dir))
            print('creating new analysis folder')
            m = self.metadata.copy()
            date = m['experiment_datetime']
            date = str(date)[:10]
            date = date[2:4] + date[5:7] + date[8:10]
            self._analysis_folder = str(m['ophys_experiment_id']) + '_' + str(m['donor_id']) + '_' + date + '_' + m[
                'targeted_structure'] + '_' + str(m['imaging_depth']) + '_' + m['driver_line'][0] + '_' + m[
                                        'rig_name'] + '_' + m['session_type']
            os.mkdir(os.path.join(analysis_cache_dir, self._analysis_folder))
        elif len(candidates) > 1:
            raise OSError('{} contains multiple possible analysis folders: {}'.format(analysis_cache_dir, candidates))
        return self._analysis_folder

    @property
    def analysis_dir(self):
        self._analysis_dir = os.path.join(get_analysis_cache_dir(), self.analysis_folder)
        return self._analysis_dir

    @property
    def cell_specimen_table(self):
        cell_specimen_table = super().cell_specimen_table
        if self._include_invalid_rois == False:
            cell_specimen_table = cell_specimen_table[cell_specimen_table.valid_roi == True]
        cell_specimen_table = cell_specimen_table.copy()
        # add cell index corresponding to the index of the cell in dff_traces_array
        cell_specimen_ids = np.sort(cell_specimen_table.index.values)
        if 'cell_index' not in cell_specimen_table.columns:
            cell_specimen_table['cell_index'] = [np.where(cell_specimen_ids == cell_specimen_id)[0][0] for
                                                 cell_specimen_id in cell_specimen_table.index.values]
        cell_specimen_table = processing.shift_image_masks(cell_specimen_table)
        self._cell_specimen_table = cell_specimen_table
        return self._cell_specimen_table

    @property
    def cell_indices(self):
        self._cell_indices = self.cell_specimen_table.cell_index
        return self._cell_indices

    @property
    def cell_specimen_ids(self):
        self._cell_specimen_ids = np.sort(self.cell_specimen_table.index.values)
        return self._cell_specimen_ids

    @property
    def roi_masks(self):
        cell_specimen_table = super().cell_specimen_table
        cell_specimen_table = processing.shift_image_masks(cell_specimen_table)
        self._roi_masks = get_sdk_roi_masks(cell_specimen_table)
        return self._roi_masks

    @property
    def corrected_fluorescence_traces(self):
        if self._include_invalid_rois == False:
            corrected_fluorescence_traces = super().corrected_fluorescence_traces
            cell_specimen_table = super().cell_specimen_table[super().cell_specimen_table.valid_roi == True]
            valid_cells = cell_specimen_table.cell_roi_id.values
            self._corrected_fluorescence_traces = corrected_fluorescence_traces[
                corrected_fluorescence_traces.cell_roi_id.isin(valid_cells)]
        else:
            self._corrected_fluorescence_traces = super().corrected_fluorescence_traces
        return self._corrected_fluorescence_traces

    @property
    def dff_traces(self):
        if self._include_invalid_rois == False:
            dff_traces = super().dff_traces
            cell_specimen_table = super().cell_specimen_table[super().cell_specimen_table.valid_roi == True]
            valid_cells = cell_specimen_table.cell_roi_id.values
            self._dff_traces = dff_traces[dff_traces.cell_roi_id.isin(valid_cells)]
        else:
            self._dff_traces = super().dff_traces
        return self._dff_traces

    def get_events_array(self):
        events_folder = get_events_dir()
        if os.path.exists(events_folder):
            events_file = [file for file in os.listdir(events_folder) if
                           str(self.ophys_experiment_id) in file]
            if len(events_file) > 0:
                print('getting L0 events')
                f = np.load(os.path.join(events_folder, events_file[0]))
                events = np.asarray(f['events'])
                f.close()
            else:
                print('no events for this experiment')
                events = None
        else:
            print('no events for this experiment')
            events = None
        self.events_array = events
        return self.events_array

    @property
    def events(self):
        events_folder = get_events_dir()
        if os.path.exists(events_folder):
            events_file = [file for file in os.listdir(events_folder) if str(self.ophys_experiment_id) in file]
            if len(events_file) > 0:
                print('getting L0 events')
                f = np.load(os.path.join(events_folder, events_file[0]), allow_pickle=True)

                event_dict = f['event_dict'].item()
                cell_roi_ids = list(event_dict.keys())
                events_array = np.asarray([event_dict[cell_roi_id]['event_trace'] for cell_roi_id in cell_roi_ids])
                cell_specimen_ids = [self.get_cell_specimen_id_for_cell_roi_id(cell_roi_id) for cell_roi_id in cell_roi_ids]
                self._events = pd.DataFrame({'events': [x for x in events_array],
                                        'filtered_events': [x for x in rp.filter_events_array(events_array)]},
                                         index=pd.Index(cell_specimen_ids, name='cell_specimen_id'))
        #
        # self._events = pd.DataFrame({'events': [x for x in self.get_events_array()],
        #                              'filtered_events': [x for x in rp.filter_events_array(self.get_events_array())]},
        #                             index=pd.Index(self.cell_specimen_ids, name='cell_specimen_id'))
        return self._events

    @property
    def timestamps(self):
        # need to get full set of timestamps because SDK only provides stimulus and ophys timestamps (not eye tracking for example)
        lims_data = utilities.get_lims_data(self.ophys_experiment_id)
        self._timestamps = utilities.get_timestamps(lims_data, self.analysis_dir)
        return self._timestamps

    @property
    def ophys_timestamps(self):
        if super().metadata['rig_name'] == 'MESO.1':
            ophys_timestamps = self.timestamps['ophys_frames']['timestamps'].copy()
            self._ophys_timestamps = ophys_timestamps
            # correct metadata frame rate
            self._metadata['ophys_frame_rate'] = 1 / np.diff(ophys_timestamps).mean()
        else:
            self._ophys_timestamps = super().ophys_timestamps
        return self._ophys_timestamps

    @property
    def behavior_movie_timestamps(self):
        # note that due to sync line label issues, 'eye_tracking' timestamps are loaded here instead of 'behavior_movie' timestamps
        self._behavior_movie_timestamps = self.timestamps['eye_tracking']['timestamps'].copy()
        return self._behavior_movie_timestamps

    @property
    def metadata(self):
        metadata = super().metadata
        # reset ophys frame rate for accuracy & to account for mesoscope resampling
        # causes recursion error
        # metadata['ophys_frame_rate'] = 1 / np.diff(self.ophys_timestamps).mean()
        if 'donor_id' not in metadata.keys():
            metadata['donor_id'] = metadata.pop('LabTracks_ID')
            metadata['behavior_session_id'] = utilities.get_behavior_session_id_from_ophys_experiment_id(
                self.ophys_experiment_id, get_visual_behavior_cache())
        self._metadata = metadata
        return self._metadata

    @property
    def metadata_string(self):
        # for figure titles & filenames
        m = self.metadata
        rig_name = m['rig_name'].split('.')[0] + m['rig_name'].split('.')[1]
        self._metadata_string = str(m['donor_id']) + '_' + str(m['ophys_experiment_id']) + '_' + m['driver_line'][
            0] + '_' + m['targeted_structure'] + '_' + str(m['imaging_depth']) + '_' + m['session_type'] + '_' + rig_name
        return self._metadata_string

    @property
    def licks(self):
        self._licks = super().licks
        if 'timestamps' not in self._licks.columns:
            self._licks = reformat.convert_licks(self._licks)
        return self._licks

    @property
    def rewards(self):
        self._rewards = super().rewards
        if 'timestamps' not in self._rewards.columns:
            self._rewards = reformat.convert_rewards(super().rewards)
        return self._rewards

    @property
    def running_speed(self):
        self._running_speed = super().running_speed
        if type(self._running_speed) != pd.core.frame.DataFrame:
            self._running_speed = reformat.convert_running_speed(self._running_speed)
        return self._running_speed

    @property
    def stimulus_presentations(self):
        stimulus_presentations = super().stimulus_presentations.copy()
        if 'orientation' in stimulus_presentations.columns:
            stimulus_presentations = stimulus_presentations.drop(columns=['orientation', 'image_set', 'index'])
        stimulus_presentations = reformat.add_change_each_flash(stimulus_presentations)
        stimulus_presentations['pre_change'] = stimulus_presentations['change'].shift(-1)
        stimulus_presentations = reformat.add_epoch_times(stimulus_presentations)
        stimulus_presentations = reformat.add_mean_running_speed(stimulus_presentations, self.running_speed)
        stimulus_presentations = reformat.add_licks_each_flash(stimulus_presentations, self.licks)
        stimulus_presentations = reformat.add_response_latency(stimulus_presentations)
        stimulus_presentations = reformat.add_rewards_each_flash(stimulus_presentations, self.rewards)
        stimulus_presentations['licked'] = [True if len(licks) > 0 else False for licks in
                                            stimulus_presentations.licks.values]
        stimulus_presentations['lick_rate'] = stimulus_presentations['licked'].rolling(window=320, min_periods=1,
                                                                                       win_type='triang').mean() / .75
        stimulus_presentations['rewarded'] = [True if len(rewards) > 0 else False for rewards in
                                              stimulus_presentations.rewards.values]
        stimulus_presentations['reward_rate'] = stimulus_presentations['rewarded'].rolling(window=320, min_periods=1,
                                                                                           win_type='triang').mean() / .75
        stimulus_presentations = reformat.add_response_latency(stimulus_presentations)
        stimulus_presentations = reformat.add_epoch_times(stimulus_presentations)
        self._stimulus_presentations = stimulus_presentations
        return self._stimulus_presentations

    @property
    def extended_stimulus_presentations(self):
        stimulus_presentations = self.stimulus_presentations.copy()
        if 'orientation' in stimulus_presentations.columns:
            stimulus_presentations = stimulus_presentations.drop(columns=['orientation', 'image_set', 'index',
                                                                          'phase', 'spatial_frequency'])
        stimulus_presentations = reformat.add_time_from_last_lick(stimulus_presentations, self.licks)
        stimulus_presentations = reformat.add_time_from_last_reward(stimulus_presentations, self.rewards)
        stimulus_presentations = reformat.add_time_from_last_change(stimulus_presentations)
        stimulus_presentations = reformat.add_time_from_last_omission(stimulus_presentations)
        stimulus_presentations['flash_after_omitted'] = stimulus_presentations['omitted'].shift(1)
        stimulus_presentations['flash_after_change'] = stimulus_presentations['change'].shift(1)
        stimulus_presentations['image_name_next_flash'] = stimulus_presentations['image_name'].shift(-1)
        stimulus_presentations['image_index_next_flash'] = stimulus_presentations['image_index'].shift(-1)
        stimulus_presentations['image_name_previous_flash'] = stimulus_presentations['image_name'].shift(1)
        stimulus_presentations['image_index_previous_flash'] = stimulus_presentations['image_index'].shift(1)
        stimulus_presentations['lick_on_next_flash'] = stimulus_presentations['licked'].shift(-1)
        stimulus_presentations['lick_rate_next_flash'] = stimulus_presentations['lick_rate'].shift(-1)
        stimulus_presentations['lick_on_previous_flash'] = stimulus_presentations['licked'].shift(1)
        stimulus_presentations['lick_rate_previous_flash'] = stimulus_presentations['lick_rate'].shift(1)
        if check_if_model_output_available(self.metadata['behavior_session_id']):
            stimulus_presentations = add_model_outputs_to_stimulus_presentations(
                stimulus_presentations, self.metadata['behavior_session_id'])
        else:
            print('model outputs not available')
        self._extended_stimulus_presentations = stimulus_presentations
        return self._extended_stimulus_presentations

    @property
    def trials(self):
        trials = super().trials.copy()
        trials = reformat.add_epoch_times(trials)
        trials = reformat.add_trial_type_to_trials_table(trials)
        self._trials = trials
        return self._trials

    @property
    def behavior_movie_pc_masks(self):
        cache = get_visual_behavior_cache()
        ophys_session_id = utilities.get_ophys_session_id_from_ophys_experiment_id(self.ophys_experiment_id, cache)
        self._behavior_movie_pc_masks = get_pc_masks_for_session(ophys_session_id)
        return self._behavior_movie_pc_masks

    @property
    def behavior_movie_pc_activations(self):
        cache = get_visual_behavior_cache()
        ophys_session_id = utilities.get_ophys_session_id_from_ophys_experiment_id(self.ophys_experiment_id, cache)
        self._behavior_movie_pc_activations = get_pc_activations_for_session(ophys_session_id)
        return self._behavior_movie_pc_activations

    @property
    def behavior_movie_predictions(self):
        cache = get_visual_behavior_cache()
        ophys_session_id = utilities.get_ophys_session_id_from_ophys_experiment_id(self.ophys_experiment_id, cache)
        movie_predictions = get_behavior_movie_predictions_for_session(ophys_session_id)
        movie_predictions.index.name = 'frame_index'
        movie_predictions['timestamps'] = self.behavior_movie_timestamps[:len(
            movie_predictions)]  # length check will trim off spurious timestamps at the end
        self._behavior_movie_predictions = movie_predictions
        return self._behavior_movie_predictions

    def get_cell_specimen_id_for_cell_index(self, cell_index):
        cell_specimen_id = self.cell_specimen_table[self.cell_specimen_table.cell_index == cell_index].index.values[0]
        return cell_specimen_id

    def get_cell_index_for_cell_specimen_id(self, cell_specimen_id):
        cell_index = self.cell_specimen_table[self.cell_specimen_table.index == cell_specimen_id].cell_index.values[0]
        return cell_index

    def get_cell_specimen_id_for_cell_roi_id(self, cell_roi_id):
        cell_specimen_id = self.cell_specimen_table[self.cell_specimen_table.cell_roi_id == cell_roi_id].index.values[0]
        return cell_specimen_id


def get_ophys_dataset(ophys_experiment_id, include_invalid_rois=False):
    """Gets behavior + ophys data for one experiment (single imaging plane), using the SDK LIMS API, then reformats & filters to compensate for bugs and missing SDK features.
        This functionality should eventually be entirely replaced by the SDK when all requested features have been implemented.

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID
        include_invalid_rois {Boolean} -- if True, return all ROIs including invalid. If False, filter out invalid ROIs

    Returns:
        BehaviorOphysDataset {object} -- BehaviorOphysDataset instance, inherits attributes & methods from SDK BehaviorOphysSession class
    """
    api = BehaviorOphysLimsApi(ophys_experiment_id)
    dataset = BehaviorOphysDataset(api, include_invalid_rois)
    print('loading data for {}'.format(dataset.analysis_folder))  # required to ensure analysis folder is created before other methods are called
    return dataset


def get_ophys_container_ids():
    """Get container_ids that meet the criteria in get_filtered_ophys_experiment_table(). """
    experiments = get_filtered_ophys_experiment_table()
    container_ids = np.sort(experiments.container_id.unique())
    return container_ids


def get_ophys_session_ids_for_ophys_container_id(ophys_container_id):
    """Get ophys_session_ids belonging to a given ophys_container_id. Ophys session must pass QC.

            Arguments:
                ophys_container_id -- must be in get_ophys_container_ids()

            Returns:
                ophys_session_ids -- list of ophys_session_ids that meet filtering criteria
            """
    experiments = get_filtered_ophys_experiment_table()
    ophys_session_ids = np.sort(experiments[(experiments.container_id == ophys_container_id)].ophys_session_id.unique())
    return ophys_session_ids


def get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id):
    """Get ophys_experiment_ids belonging to a given ophys_container_id. ophys container must meet the criteria in
        sdk_utils.get_filtered_session_table()

                Arguments:
                    ophys_container_id -- must be in get_filtered_ophys_container_ids()

                Returns:
                    ophys_experiment_ids -- list of ophys_experiment_ids that meet filtering criteria
                """
    experiments = get_filtered_ophys_experiment_table()
    ophys_experiment_ids = np.sort(experiments[(experiments.container_id == ophys_container_id)].index.values)
    return ophys_experiment_ids


def get_session_type_for_ophys_experiment_id(ophys_experiment_id):
    experiments = get_filtered_ophys_experiment_table()
    session_type = experiments.loc[ophys_experiment_id].session_type
    return session_type


def get_session_type_for_ophys_session_id(ophys_session_id):
    sessions = get_filtered_ophys_session_table()
    session_type = sessions.loc[ophys_session_id].session_type
    return session_type


def get_ophys_experiment_id_for_ophys_session_id(ophys_session_id):
    experiments = get_filtered_ophys_experiment_table()
    ophys_experiment_id = experiments[(experiments.ophys_session_id == ophys_session_id)].index.values[0]
    return ophys_experiment_id


def get_ophys_session_id_for_ophys_experiment_id(ophys_experiment_id):
    experiments = get_filtered_ophys_experiment_table()
    ophys_session_id = experiments.loc[ophys_experiment_id].ophys_session_id
    return ophys_session_id


def get_pc_masks_for_session(ophys_session_id):
    facemap_output_dir = r'//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/facemap_results'
    session_file = [file for file in os.listdir(facemap_output_dir) if
                    (str(ophys_session_id) in file) and ('motMask' in file)]
    try:
        pc_masks = np.load(os.path.join(facemap_output_dir, session_file[0]))
    except Exception as e:
        print('could not load PC masks for ophys_session_id', ophys_session_id)
        print(e)
        pc_masks = []
    return pc_masks


def get_pc_activations_for_session(ophys_session_id):
    facemap_output_dir = r'//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/facemap_results'
    session_file = [file for file in os.listdir(facemap_output_dir) if
                    (str(ophys_session_id) in file) and ('motSVD' in file)]
    try:
        pc_activations = np.load(os.path.join(facemap_output_dir, session_file[0]))
    except Exception as e:
        print('could not load PC activations for ophys_session_id', ophys_session_id)
        print(e)
        pc_activations = []
    return pc_activations


def get_extended_stimulus_presentations(session):
    '''
    Calculates additional information for each stimulus presentation
    '''
    import visual_behavior.ophys.dataset.stimulus_processing as sp
    stimulus_presentations_pre = session.stimulus_presentations
    change_times = session.trials['change_time'].values
    change_times = change_times[~np.isnan(change_times)]
    extended_stimulus_presentations = sp.get_extended_stimulus_presentations(
        stimulus_presentations_df=stimulus_presentations_pre,
        licks=session.licks,
        rewards=session.rewards,
        change_times=change_times,
        running_speed_df=session.running_data_df,
        pupil_area=session.pupil_area
    )
    return extended_stimulus_presentations


def get_model_output_file(behavior_session_id):
    model_output_dir = get_behavior_model_outputs_dir()
    model_output_file = [file for file in os.listdir(model_output_dir) if
                         (str(behavior_session_id) in file) and ('training' not in file)]
    return model_output_file


def check_if_model_output_available(behavior_session_id):
    model_output_file = get_model_output_file(behavior_session_id)
    if len(model_output_file) > 0:
        return True
    else:
        return False


def add_model_outputs_to_stimulus_presentations(stimulus_presentations, behavior_session_id):
    '''
       Adds additional columns to stimulus table for model weights and related metrics
    '''

    if check_if_model_output_available(behavior_session_id):
        model_outputs = pd.read_csv(
            os.path.join(get_behavior_model_outputs_dir(), get_model_output_file(behavior_session_id)[0]))
        model_outputs.drop(columns=['image_index', 'image_name', 'omitted', 'change',
                                    'licked', 'lick_rate', 'rewarded', 'reward_rate'], inplace=True)
        stimulus_presentations = stimulus_presentations.merge(model_outputs, right_on='stimulus_presentations_id',
                                                              left_on='stimulus_presentations_id').set_index(
            'stimulus_presentations_id')
        stimulus_presentations['engagement_state'] = [
            'engaged' if flash_metrics_label != 'low-lick,low-reward' else 'disengaged' for flash_metrics_label in
            stimulus_presentations.flash_metrics_labels.values]
        stimulus_presentations = stimulus_presentations.drop(
            columns=['hit_rate', 'miss_rate', 'false_alarm_rate', 'correct_reject_rate', 'd_prime', 'criterion'])
        return stimulus_presentations
    else:
        print('no model outputs saved for behavior_session_id:', behavior_session_id)
    return stimulus_presentations






def get_behavior_model_summary_table():
    data_dir = get_behavior_model_outputs_dir()
    data = pd.read_csv(os.path.join(data_dir, '_summary_table.csv'))
    data2 = pd.read_csv(os.path.join(data_dir, '_meso_summary_table.csv'))
    data = data.append(data2)
    return data


def check_for_events_file(ophys_experiment_id):
    # events_folder = os.path.join(get_analysis_cache_dir(), 'events')
    events_folder = os.path.join(get_events_dir())
    if os.path.exists(events_folder):
        events_file = [file for file in os.listdir(events_folder) if
                       str(ophys_experiment_id) in file]
        if len(events_file) > 0:
            return True
        else:
            return False


def get_behavior_movie_predictions_for_session(ophys_session_id):
    """
    Loads model predictions from behavior movie classifier and returns a dictionary with keys =
    ['groom_reach_with_contact', 'groom_reach_without_contact', 'lick_with_contact', 'lick_without_contact', 'no_contact', 'paw_contact']
    :param ophys_session_id: ophys_session_id
    :return: dictionary of behavior prediction values
    """
    model_output_dir = '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/lick_detection_validation/model_predictions'
    predictions_path = glob.glob(os.path.join(model_output_dir, 'predictions*osid={}*'.format(ophys_session_id)))[0]
    try:
        movie_predictions = pd.read_csv(predictions_path)
    except Exception as e:
        print('could not behavior movie model predictions for ophys_session_id', ophys_session_id)
        print(e)
        movie_predictions = []
    return movie_predictions


def get_sdk_max_projection(ophys_experiment_id):
    """ uses SDK to return 2d max projection image of the microscope field of view


    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        image -- can be visualized via plt.imshow(max_projection)
    """
    session = get_ophys_dataset(ophys_experiment_id)
    max_projection = session.max_projection
    return max_projection


def get_sdk_ave_projection(ophys_experiment_id):
    """uses SDK to return 2d image of the 2-photon microscope filed of view, averaged
        across the experiment.

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        image -- can be visualized via plt.imshow(ave_projection)
    """
    session = get_ophys_dataset(ophys_experiment_id)
    ave_projection = session.average_projection
    return ave_projection


def get_sdk_segmentation_mask_image(ophys_experiment_id):
    """uses SDK to return an array containing the masks of all cell ROIS

    Arguments:
       ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
       array -- a 2D boolean array
                visualized via plt.imshow(seg_mask_image)
    """
    session = get_ophys_dataset(ophys_experiment_id)
    seg_mask_image = session.segmentation_mask_image.data
    return seg_mask_image


def get_sdk_roi_masks(cell_specimen_table):
    """uses sdk to return a dictionary with individual ROI
        masks for each cell specimen ID.

    Arguments:
        cell_specimen_table {DataFrame} -- cell_specimen_table from SDK session object

    Returns:
        dictonary -- keys are cell specimen ids(ints)
                    values are 2d numpy arrays(binary array
                    the size of the motion corrected 2photon
                    FOV where 1's are the ROI/Cell mask).
                    specific cell masks can be visualized via
                    plt.imshow(roi_masks[cell_specimen_id])
    """

    roi_masks = {}
    for cell_specimen_id in cell_specimen_table.index:
        mask = cell_specimen_table.at[cell_specimen_id, 'roi_mask']
        binary_mask = np.zeros(mask.shape)
        binary_mask[mask == True] = 1
        roi_masks[cell_specimen_id] = binary_mask
    return roi_masks


def get_valid_segmentation_mask(ophys_experiment_id):
    session = get_ophys_dataset(ophys_experiment_id)
    ct = session.cell_specimen_table
    valid_cell_specimen_ids = ct[ct.valid_roi == True].index.values
    roi_masks = session.get_roi_masks()
    valid_roi_masks = roi_masks[roi_masks.cell_specimen_id.isin(valid_cell_specimen_ids)].data
    valid_segmentation_mask = np.sum(valid_roi_masks, axis=0)
    valid_segmentation_mask[valid_segmentation_mask > 0] = 1
    return valid_segmentation_mask


def get_sdk_cell_specimen_table(ophys_experiment_id):
    """[summary]

    Arguments:
        ophys_experiment_id {[type]} -- [description]

    Returns:
        Dataframe -- dataframe with the following columns:
                    "cell_specimen_id": index
                    "cell_roi_id"
                    "height"
                    "image_mask"
                    "mask_image_plane"
                    "max_correction_down"
                    "max_correction_left"
                    "max_correction_right"
                    "max_correction_up"
                    "valid_roi"
                    "width"
                    "x"
                    "y"
    """
    session = get_ophys_dataset(ophys_experiment_id)
    cell_specimen_table = session.cell_specimen_table
    return cell_specimen_table


def get_sdk_dff_traces(ophys_experiment_id):
    session = get_ophys_dataset(ophys_experiment_id)
    dff_traces = session.dff_traces
    return dff_traces


def get_sdk_dff_traces_array(ophys_experiment_id):
    dff_traces = get_sdk_dff_traces(ophys_experiment_id)
    dff_traces_array = np.vstack(dff_traces.dff.values)
    return dff_traces_array


def get_sdk_running_speed(ophys_session_id):
    session = get_ophys_dataset(get_ophys_experiment_id_for_ophys_session_id(ophys_session_id))
    running_speed = session.running_data_df['speed']
    return running_speed


def get_sdk_trials(ophys_session_id):
    session = get_ophys_dataset(get_ophys_experiment_id_for_ophys_session_id(ophys_session_id))
    trials = session.trials.reset_index()
    return trials


def get_stim_metrics_summary(behavior_session_id, load_location='from_file'):
    '''
    gets flashwise stimulus presentation summary including behavior model weights

    inputs:
        behavior_session_id (int): LIMS behavior_session_id
        load_location (int): location from which to load data
            'from_file' (default) loads from a CSV on disk
            'from_database' loads from a Mongo database

    returns:
        a pandas dataframe containing columns describing stimulus information for each stimulus presentation
    '''
    if load_location == 'from_file':
        stim_metrics_summary_path = "/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/flashwise_metric_summary_2020.04.14.csv"
        stim_metrics_summary = pd.read_csv(stim_metrics_summary_path)
        return stim_metrics_summary.query('behavior_session_id == @behavior_session_id').copy()
    elif load_location == 'from_database':
        conn = db.Database('visual_behavior_data')
        collection = conn['behavior_analysis']['annotated_stimulus_presentations']
        df = pd.DataFrame(list(collection.find({'behavior_session_id': int(behavior_session_id)})))
        conn.close()
        return df.sort_values(by=['behavior_session_id', 'flash_index'])


# FROM LIMS DATABASE


# EXPERIMENT LEVEL


def get_lims_experiment_info(ophys_experiment_id):
    """uses an sqlite query to retrieve ophys experiment information
        from the lims2 database

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        table -- table with the following columns:
                    "ophys_experiment_id":
                    "experiment_workflow_state":
                    "ophys_session_id":
                    "ophys_container_id":
                    "date_of_acquisition":
                    "stage_name_lims":
                    "foraging_id":
                    "mouse_info":
                    "mouse_donor_id":
                    "targeted_structure":
                    "depth":
                    "rig":

    """
    ophys_experiment_id = int(ophys_experiment_id)
    mixin = lims_engine
    # build query
    query = '''
    select

    oe.id as ophys_experiment_id,
    oe.workflow_state,
    oe.ophys_session_id,

    container.visual_behavior_experiment_container_id as ophys_container_id,

    os.date_of_acquisition,
    os.stimulus_name as stage_name_lims,
    os.foraging_id,
    oe.workflow_state as experiment_workflow_state,

    specimens.name as mouse_info,
    specimens.donor_id as mouse_donor_id,
    structures.acronym as targeted_structure,
    imaging_depths.depth,
    equipment.name as rig

    from
    ophys_experiments_visual_behavior_experiment_containers container
    join ophys_experiments oe on oe.id = container.ophys_experiment_id
    join ophys_sessions os on os.id = oe.ophys_session_id
    join specimens on specimens.id = os.specimen_id
    join structures on structures.id = oe.targeted_structure_id
    join imaging_depths on imaging_depths.id = oe.imaging_depth_id
    join equipment on equipment.id = os.equipment_id

    where oe.id = {}'''.format(ophys_experiment_id)

    lims_experiment_info = mixin.select(query)

    return lims_experiment_info


def get_current_segmentation_run_id(ophys_experiment_id):
    """gets the id for the current cell segmentation run for a given experiment.
        Queries LIMS via AllenSDK PostgresQuery function.

    Arguments:
       ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        int -- current cell segmentation run id
    """

    segmentation_run_table = get_lims_cell_segmentation_run_info(ophys_experiment_id)
    current_segmentation_run_id = segmentation_run_table.loc[segmentation_run_table["current"] == True, ["id"][0]][0]
    return current_segmentation_run_id


def get_lims_cell_segmentation_run_info(ophys_experiment_id):
    """Queries LIMS via AllenSDK PostgresQuery function to retrieve
        information on all segmentations run in the
        ophys_cell_segmenatation_runs table for a given experiment

    Arguments:
         ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        dataframe --  dataframe with the following columns:
                        id {int}:  9 digit segmentation run id
                        run_number {int}: segmentation run number
                        ophys_experiment_id{int}: 9 digit ophys experiment id
                        current{boolean}: True/False
                                    True: most current segmentation run
                                    False: not the most current segmentation run
                        created_at{timestamp}:
                        updated_at{timestamp}:
    """

    mixin = lims_engine
    query = '''
    select *
    FROM ophys_cell_segmentation_runs
    WHERE ophys_experiment_id = {} '''.format(ophys_experiment_id)
    return mixin.select(query)


def get_lims_cell_rois_table(ophys_experiment_id):
    """Queries LIMS via AllenSDK PostgresQuery function to retrieve
        everything in the cell_rois table for a given experiment

    Arguments:
        experiment_id {int} -- 9 digit unique identifier for an ophys experiment

    Returns:
        dataframe -- returns dataframe with the following columns:
            id: a temporary id assigned before cell matching has occured. Same as cell_roi_id in
                the objectlist.txt file

            cell_specimen_id: a permanent id that is assigned after cell matching has occured.
                            this id can be found in multiple experiments in a container if a
                            cell is matched across experiments.
                            experiments that fail qc are not assigned cell_specimen_id s
            ophys_experiment_id:
            x: roi bounding box min x or "bbox_min_x" in objectlist.txt file
            y: roi bounding box min y or "bbox_min_y" in objectlist.txt file
            width:
            height:
            valid_roi: boolean(true/false), whether the roi passes or fails roi filtering
            mask_matrix: boolean mask of just roi
            max_correction_up:
            max_correction_down:
            max_correction_right:
            max_correction_left:
            mask_image_plane:
            ophys_cell_segmentation_run_id:

    """
    # query from AllenSDK

    mixin = lims_engine
    query = '''select cell_rois.*

    from

    ophys_experiments oe
    join cell_rois on oe.id = cell_rois.ophys_experiment_id

    where oe.id = {}'''.format(ophys_experiment_id)
    lims_cell_rois_table = mixin.select(query)
    return lims_cell_rois_table


# CONTAINER  LEVEL


def get_lims_container_info(ophys_container_id):
    """"uses an sqlite query to retrieve container level information
        from the lims2 database. Each row is an experiment within the container.

    Arguments:
        ophys_container_id {[type]} -- [description]

    Returns:
       table -- table with the following columns:
                    "ophys_container_id":
                    "container_workflow_state":
                    "ophys_experiment_id":
                    "ophys_session_id":
                    "stage_name_lims":
                    "foraging_id":
                    "experiment_workflow_state":
                    "mouse_info":
                    "mouse_donor_id":
                    "targeted_structure":
                    "depth":
                    "rig":
                    "date_of_acquisition":
    """
    ophys_container_id = int(ophys_container_id)

    mixin = lims_engine
    # build query
    query = '''
    SELECT
    container.visual_behavior_experiment_container_id as ophys_container_id,
    vbec.workflow_state as container_workflow_state,
    oe.id as ophys_experiment_id,
    oe.ophys_session_id,
    os.stimulus_name as stage_name_lims,
    os.foraging_id,
    oe.workflow_state as experiment_workflow_state,
    specimens.name as mouse_info,
    specimens.donor_id as mouse_donor_id,
    structures.acronym as targeted_structure,
    imaging_depths.depth,
    equipment.name as rig,
    os.date_of_acquisition

    FROM
    ophys_experiments_visual_behavior_experiment_containers container
    join visual_behavior_experiment_containers vbec on vbec.id = container.visual_behavior_experiment_container_id
    join ophys_experiments oe on oe.id = container.ophys_experiment_id
    join ophys_sessions os on os.id = oe.ophys_session_id
    join structures on structures.id = oe.targeted_structure_id
    join imaging_depths on imaging_depths.id = oe.imaging_depth_id
    join specimens on specimens.id = os.specimen_id
    join equipment on equipment.id = os.equipment_id

    where
    container.visual_behavior_experiment_container_id ={}'''.format(ophys_container_id)

    lims_container_info = mixin.select(query)
    return lims_container_info


# FROM LIMS WELL KNOWN FILES


def get_timeseries_ini_wkf_info(ophys_session_id):
    """use SQL and the LIMS well known file system to get the timeseries_XYT.ini file
        for a given ophys session *from a Scientifica rig*

    Arguments:
        ophys_session_id {int} -- 9 digit ophys session id

    Returns:

    """

    QUERY = '''
    SELECT wkf.storage_directory || wkf.filename
    FROM well_known_files wkf
    JOIN well_known_file_types wkft ON wkft.id=wkf.well_known_file_type_id
    JOIN specimens sp ON sp.id=wkf.attachable_id
    JOIN ophys_sessions os ON os.specimen_id=sp.id
    WHERE wkft.name = 'SciVivoMetadata'
    AND wkf.storage_directory LIKE '%ophys_session_{0}%'
    AND os.id = {0}

    '''.format(ophys_session_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    timeseries_ini_wkf_info = (lims_cursor.fetchall())
    return timeseries_ini_wkf_info


def get_timeseries_ini_location(ophys_session_id):
    """use SQL and the LIMS well known file system to
        get info for the timeseries_XYT.ini file for a
        given ophys session, and then parses that information
        to get the filepath

    Arguments:
        ophys_session_id {int} -- 9 digit ophys session id

    Returns:
        filepath -- [description]
    """
    timeseries_ini_wkf_info = get_timeseries_ini_wkf_info(ophys_session_id)
    timeseries_ini_path = timeseries_ini_wkf_info[0]['?column?']  # idk why it's ?column? but it is :(
    timeseries_ini_path = timeseries_ini_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return timeseries_ini_path


def pmt_gain_from_timeseries_ini(timeseries_ini_path):
    """parses the timeseries ini file (scientifica experiments only)
        and extracts the pmt gain setting

    Arguments:
        timeseries_ini_path {[type]} -- [description]

    Returns:
        int -- int of the pmt gain
    """
    config.read(timeseries_ini_path)
    pmt_gain = int(float(config['_']['PMT.2']))
    return pmt_gain


def get_pmt_gain_for_session(ophys_session_id):
    """finds the timeseries ini file for a given ophys session
        on a Scientifica rig, parses the file and returns the
        pmt gain setting for that session

    Arguments:
        ophys_session_id {int} -- [description]

    Returns:
        int -- pmt gain setting
    """
    try:
        timeseries_ini_path = get_timeseries_ini_location(ophys_session_id)
        pmt_gain = pmt_gain_from_timeseries_ini(timeseries_ini_path)
    except IndexError:
        ophys_experiment_id = get_ophys_experiment_id_for_ophys_session_id(ophys_session_id)
        print("lims query did not return timeseries_XYT.ini location for session_id: " + str(
            ophys_session_id) + ", experiment_id: " + str(ophys_experiment_id))
        pmt_gain = np.nan
    return pmt_gain


def get_pmt_gain_for_experiment(ophys_experiment_id):
    """finds the timeseries ini file for  the ophys_session_id
        associated with an ophys_experiment_id  from a Scientifica
        rig, parses the file and returns the
        pmt gain setting for that session

    Arguments:
        ophys_experiment_id {[type]} -- [description]

    Returns:
        int -- pmt gain setting
    """
    ophys_session_id = get_ophys_session_id_for_ophys_experiment_id(ophys_experiment_id)
    pmt_gain = get_pmt_gain_for_session(ophys_session_id)
    return pmt_gain


def get_wkf_dff_h5_location(ophys_experiment_id):
    """uses well known file system to query lims
        and get the directory and filename for the
        dff traces h5 for a given ophys experiment

    Arguments:
        ophys_experiment_id {int} -- 9 digit unique identifier for
                                    an ophys experiment

    Returns:
        string -- filepath (directory and filename) for the dff.h5 file
                    for the given ophys_experiment_id
    """
    QUERY = '''
    SELECT storage_directory || filename
    FROM well_known_files
    WHERE well_known_file_type_id = 514173073 AND
    attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    dff_h5_location_info = (lims_cursor.fetchall())

    dff_h5_path = dff_h5_location_info[0]['?column?']  # idk why it's ?column? but it is :(
    dff_h5_path = dff_h5_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return dff_h5_path


def get_wkf_roi_trace_h5_location(ophys_experiment_id):
    """uses well known file system to query lims
        and get the directory and filename for the
        roi_traces.h5 for a given ophys experiment

    Arguments:
        ophys_experiment_id {int} -- 9 digit unique identifier for
                                    an ophys experiment

    Returns:
        string -- filepath (directory and filename) for the roi_traces.h5 file
                    for the given ophys_experiment_id
    """
    QUERY = '''
    SELECT storage_directory || filename
    FROM well_known_files
    WHERE well_known_file_type_id = 514173076 AND
    attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    trace_h5_location_info = (lims_cursor.fetchall())

    trace_h5_path = trace_h5_location_info[0]['?column?']  # idk why it's ?column? but it is :(
    trace_h5_path = trace_h5_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return trace_h5_path


def get_roi_traces_array(ophys_experiment_id):
    """use SQL and the LIMS well known file system to find and load
            "roi_traces.h5" then return the traces as an array

        Arguments:
            ophys_experiment_id {int} -- 9 digit ophys experiment ID

        Returns:
            raw_traces_array -- mxn array where m = rois and n = time
        """
    filepath = get_wkf_roi_trace_h5_location(ophys_experiment_id)
    f = h5py.File(filepath, 'r')
    roi_traces_array = np.asarray(f['data'])
    f.close()
    return roi_traces_array


def get_wkf_neuropil_trace_h5_location(ophys_experiment_id):
    """uses well known file system to query lims
        and get the directory and filename for the
        neuropil_traces.h5 for a given ophys experiment

    Arguments:
        ophys_experiment_id {int} -- 9 digit unique identifier for
                                    an ophys experiment

    Returns:
        string -- filepath (directory and filename) for the neuropil_traces.h5 file
                    for the given ophys_experiment_id
    """
    QUERY = '''
    SELECT storage_directory || filename
    FROM well_known_files
    WHERE well_known_file_type_id = 514173078 AND
    attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    trace_h5_location_info = (lims_cursor.fetchall())

    trace_h5_path = trace_h5_location_info[0]['?column?']  # idk why it's ?column? but it is :(
    trace_h5_path = trace_h5_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return trace_h5_path


def get_neuropil_traces_array(ophys_experiment_id):
    """use SQL and the LIMS well known file system to find and load
            "neuropil_traces.h5" then return the traces as an array

        Arguments:
            ophys_experiment_id {int} -- 9 digit ophys experiment ID

        Returns:
            neuropil_traces_array -- mxn array where m = rois and n = time
        """
    filepath = get_wkf_neuropil_trace_h5_location(ophys_experiment_id)
    f = h5py.File(filepath, 'r')
    neuropil_traces_array = np.asarray(f['data'])
    f.close()
    return neuropil_traces_array


def get_wkf_extracted_trace_h5_location(ophys_experiment_id):
    """uses well known file system to query lims
        and get the directory and filename for the
        neuropil_traces.h5 for a given ophys experiment

    Arguments:
        ophys_experiment_id {int} -- 9 digit unique identifier for
                                    an ophys experiment

    Returns:
        string -- filepath (directory and filename) for the neuropil_traces.h5 file
                    for the given ophys_experiment_id
    """
    QUERY = '''
    SELECT storage_directory || filename
    FROM well_known_files
    WHERE well_known_file_type_id = 486797213 AND
    attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    trace_h5_location_info = (lims_cursor.fetchall())

    trace_h5_path = trace_h5_location_info[0]['?column?']  # idk why it's ?column? but it is :(
    trace_h5_path = trace_h5_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return trace_h5_path


def get_wkf_demixed_traces_h5_location(ophys_experiment_id):
    """uses well known file system to query lims
        and get the directory and filename for the
        roi_traces.h5 for a given ophys experiment

    Arguments:
        ophys_experiment_id {int} -- 9 digit unique identifier for
                                    an ophys experiment

    Returns:
        string -- filepath (directory and filename) for the roi_traces.h5 file
                    for the given ophys_experiment_id
    """
    QUERY = '''
    SELECT storage_directory || filename
    FROM well_known_files
    WHERE well_known_file_type_id = 820011707 AND
    attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    trace_h5_location_info = (lims_cursor.fetchall())

    trace_h5_path = trace_h5_location_info[0]['?column?']  # idk why it's ?column? but it is :(
    trace_h5_path = trace_h5_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return trace_h5_path


def get_demixed_traces_array(ophys_experiment_id):
    """use SQL and the LIMS well known file system to find and load
            "demixed_traces.h5" then return the traces as an array

        Arguments:
            ophys_experiment_id {int} -- 9 digit ophys experiment ID

        Returns:
            demixed_traces_array -- mxn array where m = rois and n = time
        """
    filepath = get_wkf_demixed_traces_h5_location(ophys_experiment_id)
    f = h5py.File(filepath, 'r')
    demixed_traces_array = np.asarray(f['data'])
    f.close()
    return demixed_traces_array


def get_motion_corrected_movie_h5_wkf_info(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get the
        "motion_corrected_movie.h5" information for a given
        ophys_experiment_id

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        [type] -- [description]
    """

    QUERY = '''
     SELECT storage_directory || filename
     FROM well_known_files
     WHERE well_known_file_type_id = 886523092 AND
     attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    motion_corrected_movie_h5_wkf_info = (lims_cursor.fetchall())
    return motion_corrected_movie_h5_wkf_info


def get_motion_corrected_movie_h5_location(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get info for the
        "motion_corrected_movie.h5" file for a ophys_experiment_id,
        and then parses that information to get the filepath

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        filepath -- [description]
    """
    motion_corrected_movie_h5_wkf_info = get_motion_corrected_movie_h5_wkf_info(ophys_experiment_id)
    motion_corrected_movie_h5_path = motion_corrected_movie_h5_wkf_info[0][
        '?column?']  # idk why it's ?column? but it is :(
    motion_corrected_movie_h5_path = motion_corrected_movie_h5_path.replace('/allen',
                                                                            '//allen')  # works with windows and linux filepaths
    return motion_corrected_movie_h5_path


def load_motion_corrected_movie(ophys_experiment_id):
    """uses well known file system to get motion_corrected_movie.h5
        filepath and then loads the h5 file with h5py function.
        Gets the motion corrected movie array in the h5 from the only
        datastream/key 'data' and returns it.

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        HDF5 dataset -- 3d array-like  (z, y, x) dimensions
                        z: timeseries/frame number
                        y: single frame y axis
                        x: single frame x axis
    """
    motion_corrected_movie_h5_path = get_motion_corrected_movie_h5_location(ophys_experiment_id)
    motion_corrected_movie_h5 = h5py.File(motion_corrected_movie_h5_path, 'r')
    motion_corrected_movie = motion_corrected_movie_h5['data']

    return motion_corrected_movie


def get_rigid_motion_transform_csv_wkf_info(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get the
        "rigid_motion_transform.csv" information for a given
        ophys_experiment_id

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        [type] -- [description]
    """
    QUERY = '''
     SELECT storage_directory || filename
     FROM well_known_files
     WHERE well_known_file_type_id = 514167000 AND
     attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = db.get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    rigid_motion_transform_csv_wkf_info = (lims_cursor.fetchall())
    return rigid_motion_transform_csv_wkf_info


def get_rigid_motion_transform_csv_location(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get info for the
        rigid_motion_transform.csv" file for a ophys_experiment_id,
        and then parses that information to get the filepath

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        filepath -- [description]
    """
    rigid_motion_transform_csv_wkf_info = get_rigid_motion_transform_csv_wkf_info(ophys_experiment_id)
    rigid_motion_transform_csv_path = rigid_motion_transform_csv_wkf_info[0][
        '?column?']  # idk why it's ?column? but it is :(
    rigid_motion_transform_csv_path = rigid_motion_transform_csv_path.replace('/allen',
                                                                              '//allen')  # works with windows and linux filepaths
    return rigid_motion_transform_csv_path


def load_rigid_motion_transform_csv(ophys_experiment_id):
    """use SQL and the LIMS well known file system to locate
        and load the rigid_motion_transform.csv file for
        a given ophys_experiment_id

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        dataframe -- dataframe with the following columns:
                        "framenumber":
                                  "x":
                                  "y":
                        "correlation":
                           "kalman_x":
                           "kalman_y":
    """
    rigid_motion_transform_csv_path = get_rigid_motion_transform_csv_location(ophys_experiment_id)
    rigid_motion_transform_df = pd.read_csv(rigid_motion_transform_csv_path)
    return rigid_motion_transform_df


# FROM MTRAIN DATABASE


def get_mtrain_stage_name(dataframe):
    foraging_ids = dataframe['foraging_id'][~pd.isnull(dataframe['foraging_id'])]
    query = """
            SELECT
            stages.name as stage_name,
            bs.id as foraging_id
            FROM behavior_sessions bs
            LEFT JOIN states ON states.id = bs.state_id
            LEFT JOIN stages ON stages.id = states.stage_id
            WHERE bs.id IN ({})
        """.format(",".join(["'{}'".format(x) for x in foraging_ids]))
    mtrain_response = pd.read_sql(query, mtrain_engine.get_connection())
    dataframe = dataframe.merge(mtrain_response, on='foraging_id', how='left')
    dataframe = dataframe.rename(columns={"stage_name": "stage_name_mtrain"})
    return dataframe


def build_container_df():
    '''
    build dataframe with one row per container
    '''

    table = get_filtered_ophys_experiment_table().sort_values(by='date_of_acquisition', ascending=False).reset_index()
    container_ids = table['container_id'].unique()
    list_of_dicts = []
    for container_id in container_ids:
        subset = table.query('container_id == @container_id').sort_values(by='date_of_acquisition',
                                                                          ascending=True).drop_duplicates(
            'ophys_session_id').reset_index()
        temp_dict = {
            'container_id': container_id,
            'container_workflow_state':
                table.query('container_id == @container_id')['container_workflow_state'].unique()[0],
            'first_acquistion_date': subset['date_of_acquisition'].min().split(' ')[0],
            'project_code': subset['project_code'].unique()[0],
            'driver_line': subset['driver_line'][0],
            'cre_line': subset['cre_line'][0],
            'targeted_structure': subset['targeted_structure'].unique()[0],
            'imaging_depth': subset['imaging_depth'].unique()[0],
            'exposure_number': subset['exposure_number'][0],
            'equipment_name': subset['equipment_name'].unique(),
            'specimen_id': subset['specimen_id'].unique()[0],
            'sex': subset['sex'].unique()[0],
            'age_in_days': subset['age_in_days'].min(),
        }
        for idx, row in subset.iterrows():
            temp_dict.update(
                {'session_{}'.format(idx): '{} {}'.format(row['session_type'], row['ophys_experiment_id'])})

        list_of_dicts.append(temp_dict)

    return pd.DataFrame(list_of_dicts).sort_values(by='container_id', ascending=False)


# multi session summary data #########

def get_annotated_experiments_table():
    project_codes = ['VisualBehavior', 'VisualBehaviorTask1B',
                     'VisualBehaviorMultiscope', 'VisualBehaviorMultiscope4areasx2d']

    experiments_table = get_filtered_ophys_experiment_table()
    experiments_table = experiments_table[experiments_table.project_code.isin(project_codes)]
    # add columns
    experiments_table['depth'] = ['superficial' if experiments_table.loc[expt].imaging_depth <= 250 else 'deep' for expt
                                  in experiments_table.index]  # 355
    experiments_table['location'] = [experiments_table.loc[expt].cre_line.split('-')[0] + '_' +
                                     experiments_table.loc[expt].depth for expt in experiments_table.index]

    # experiments_table['location2'] = [experiments_table.loc[expt].cre_line.split('-')[0] + '_' +
    #                                   experiments_table.loc[expt].depth for expt in experiments_table.index]

    experiments_table['layer'] = None
    indices = experiments_table[(experiments_table.imaging_depth < 100)].index.values
    experiments_table.at[indices, 'layer'] = 'L1'
    indices = experiments_table[(experiments_table.imaging_depth < 270) &
                                (experiments_table.imaging_depth >= 100)].index.values
    experiments_table.at[indices, 'layer'] = 'L2/3'
    # indices = experiments_table[
    #     (experiments_table.imaging_depth >= 125) & (experiments_table.imaging_depth < 200)].index.values
    # experiments_table.at[indices, 'layer'] = 'L3'
    indices = experiments_table[
        (experiments_table.imaging_depth >= 270) & (experiments_table.imaging_depth < 350)].index.values
    experiments_table.at[indices, 'layer'] = 'L4'
    indices = experiments_table[
        (experiments_table.imaging_depth >= 350) & (experiments_table.imaging_depth < 550)].index.values
    experiments_table.at[indices, 'layer'] = 'L5'
    # indices = experiments_table[
    #     (experiments_table.imaging_depth >= 345) & (experiments_table.imaging_depth < 500)].index.values
    # experiments_table.at[indices, 'layer'] = 'L5b'
    experiments_table['location_layer'] = [experiments_table.loc[expt].cre_line.split('-')[0] + '_' +
                                           experiments_table.loc[expt].targeted_structure + '_' +
                                           experiments_table.loc[expt].layer for expt in experiments_table.index]

    indices = experiments_table[experiments_table.location == 'Slc17a7_superficial'].index.values
    experiments_table.at[indices, 'location'] = 'Excitatory superficial'
    indices = experiments_table[experiments_table.location == 'Slc17a7_deep'].index.values
    experiments_table.at[indices, 'location'] = 'Excitatory deep'
    indices = experiments_table[experiments_table.location == 'Vip_superficial'].index.values
    experiments_table.at[indices, 'location'] = 'Vip'
    indices = experiments_table[experiments_table.location == 'Sst_superficial'].index.values
    experiments_table.at[indices, 'location'] = 'Sst'
    indices = experiments_table[experiments_table.location == 'Vip_deep'].index.values
    experiments_table.at[indices, 'location'] = 'Vip'
    indices = experiments_table[experiments_table.location == 'Sst_deep'].index.values
    experiments_table.at[indices, 'location'] = 'Sst'

    experiments_table['session_number'] = [int(session_type[6]) for session_type in
                                           experiments_table.session_type.values]
    experiments_table['cre'] = [cre.split('-')[0] for cre in experiments_table.cre_line.values]

    return experiments_table


def get_file_name_for_multi_session_df_no_session_type(df_name, project_code, conditions, use_events):
    if use_events:
        suffix = '_events'
    else:
        suffix = ''

    if len(conditions) == 5:
        filename = 'mean_' + df_name + '_' + project_code + '_' + conditions[1] + '_' + conditions[
            2] + '_' + conditions[3] + '_' + conditions[4] + suffix + '.h5'
    elif len(conditions) == 4:
        filename = 'mean_' + df_name + '_' + project_code + '_' + conditions[1] + '_' + conditions[
            2] + '_' + conditions[3] + suffix + '.h5'
    elif len(conditions) == 3:
        filename = 'mean_' + df_name + '_' + project_code + '_' + conditions[1] + '_' + conditions[
            2] + suffix + '.h5'
    elif len(conditions) == 2:
        filename = 'mean_' + df_name + '_' + project_code + '_' + conditions[1] + suffix + '.h5'
    elif len(conditions) == 1:
        filename = 'mean_' + df_name + '_' + project_code + '_' + conditions[0] + suffix + '.h5'

    return filename


def get_file_name_for_multi_session_df(df_name, project_code, session_type, conditions, use_events):
    if use_events:
        suffix = '_events'
    else:
        suffix = ''
    if len(conditions) == 6:
        filename = 'mean_' + df_name + '_' + project_code + '_' + session_type + '_' + conditions[1] + '_' + conditions[2] + '_' + conditions[3] + '_' + conditions[4] + '_' + conditions[5] + suffix + '.h5'
    elif len(conditions) == 5:
        filename = 'mean_' + df_name + '_' + project_code + '_' + session_type + '_' + conditions[1] + '_' + conditions[2] + '_' + conditions[3] + '_' + conditions[4] + suffix + '.h5'
    elif len(conditions) == 4:
        filename = 'mean_' + df_name + '_' + project_code + '_' + session_type + '_' + conditions[1] + '_' + conditions[2] + '_' + conditions[
            3] + suffix + '.h5'
    elif len(conditions) == 3:
        filename = 'mean_' + df_name + '_' + project_code + '_' + session_type + '_' + conditions[1] + '_' + conditions[2] + suffix + '.h5'
    elif len(conditions) == 2:
        filename = 'mean_' + df_name + '_' + project_code + '_' + session_type + '_' + conditions[1] + suffix + '.h5'
    elif len(conditions) == 1:
        filename = 'mean_' + df_name + '_' + project_code + '_' + session_type + '_' + conditions[0] + suffix + '.h5'

    return filename


def get_multi_session_df(cache_dir, df_name, conditions, experiments_table, use_session_type=True, use_events=False):
    experiments_table = get_annotated_experiments_table()
    project_codes = experiments_table.project_code.unique()
    multi_session_df = pd.DataFrame()
    for project_code in project_codes:
        experiments = experiments_table[(experiments_table.project_code == project_code)]
        if project_code == 'VisualBehaviorMultiscope':
            experiments = experiments[experiments.session_type != 'OPHYS_2_images_B_passive']
        expts = experiments_table.reset_index()
        if use_session_type:
            for session_type in np.sort(experiments.session_type.unique()):
                filename = get_file_name_for_multi_session_df(df_name, project_code, session_type, conditions,
                                                              use_events)
                filepath = os.path.join(cache_dir, 'multi_session_summary_dfs', filename)
                df = pd.read_hdf(filepath, key='df')
                df = df.merge(expts, on='ophys_experiment_id')
                outlier_cells = df[df.mean_response > 5].cell_specimen_id.unique()
                df = df[df.cell_specimen_id.isin(outlier_cells) == False]
                multi_session_df = pd.concat([multi_session_df, df])
        else:
            filename = get_file_name_for_multi_session_df_no_session_type(df_name, project_code, conditions, use_events)
            filepath = os.path.join(cache_dir, 'multi_session_summary_dfs', filename)
            df = pd.read_hdf(filepath, key='df')
            df = df.merge(expts[['ophys_experiment_id', 'cre_line', 'location', 'location_layer',
                                 'layer', 'ophys_session_id', 'project_code', 'session_type',
                                 'specimen_id', 'depth', 'exposure_number', 'container_id']], on='ophys_experiment_id')
            outlier_cells = df[df.mean_response > 5].cell_specimen_id.unique()
            df = df[df.cell_specimen_id.isin(outlier_cells) == False]
    return multi_session_df


def remove_outlier_traces_from_multi_session_df(multi_session_df):
    indices = [row for row in multi_session_df.index.values if (multi_session_df.mean_trace.values[row].max() > 5)]

    multi_session_df = multi_session_df[multi_session_df.index.isin(indices) == False]
    multi_session_df = multi_session_df.reset_index()
    multi_session_df = multi_session_df.drop(columns=['index'])
    return multi_session_df


def remove_first_novel_session_retakes_from_multi_session_df(multi_session_df):
    multi_session_df = multi_session_df.reset_index()
    multi_session_df = multi_session_df.drop(columns=['index'])

    indices = multi_session_df[(multi_session_df.session_number == 4) & (multi_session_df.exposure_number != 0)].index
    multi_session_df = multi_session_df.drop(index=indices)

    multi_session_df = multi_session_df.reset_index()
    multi_session_df = multi_session_df.drop(columns=['index'])

    indices = multi_session_df[(multi_session_df.session_number == 1) & (multi_session_df.exposure_number != 0)].index
    multi_session_df = multi_session_df.drop(index=indices)

    multi_session_df = multi_session_df.reset_index()
    multi_session_df = multi_session_df.drop(columns=['index'])

    return multi_session_df


def remove_problematic_data_from_multi_session_df(multi_session_df):
    # notes on containers, experiments & mice #####
    # experiments to exclude
    # another Slc mouse with large familiar passive 840542948, also ramping in some familiar sessions, generally noisy
    # all mouse 920877188 remove & investiate later - weirdness
    # slc superficial very high novel 2 container 1018027834
    # Slc container 1018027644 has inconsistent familiar sessions
    # another Slc mouse with large passive familiar responses 837581585, only one container
    # slc deep with abnormally large familiar passive 1018028067, 1018028055

    # havent exlcuded these yet
    # 904363938, 905955240 #weird
    # 903485718, 986518889, 903485718 # omission in Slc?!
    # 971813765 # potentially bad

    # experiments of interest
    # Sst mouse with omission ramping 813702151, containers 1018028135, 1019028153
    # sst large novelty response N1 mouse 850862430 container 1018028339, 1018028351
    # SST omission ramping for familiar 904922342

    # slc containers with omission responses for familiar sessions, superficial - 1018028046, 1018028061 same mouse
    # another Slc with omission ramping 840390377 but only container 1018027878
    # Slc with omission ramping in all session types 843122504 container 1018027663 VISl superficial at 275 but not at 75 in VIsl or at 275 in V1

    # Vip mouse with really large familiar 1 activity 810573072, noisy familiar 2
    # VIp mouse with abnormally high familiar 3 791871803
    # Vip with abormally high novel 1 837628436
    # Vip mouse with novelty like responses to familiar 3 807248992, container 1018028367 especially but also others

    bad_specimen_ids = [810573072]  # 840542948, 920877188, 837581585
    bad_experiment_ids = [989610992, 904352692, 905955211, 974362760, 904363938, 905955240,
                          957759566, 957759574, 916220452, 934550023,
                          986518876, 986518891, 989610991, 989213058, 989213062, 990400778, 990681008, 991852002,
                          # specimen 920877188
                          915229064, 934550019, 919419011,  # specimen 840542948
                          847267618, 847267620, 848039121, 848039125, 848039123, 848760990,  # specimen 810573072
                          886585138, 886565136,  # specimen 837581585
                          ]
    multi_session_df = multi_session_df[multi_session_df.specimen_id.isin(bad_specimen_ids) == False]
    multi_session_df = multi_session_df[multi_session_df.ophys_experiment_id.isin(bad_experiment_ids) == False]

    return multi_session_df


def annotate_and_clean_multi_session_df(multi_session_df):
    def get_session_labels():
        return ['F1', 'F2', 'F3', 'N1', 'N2', 'N3']

    multi_session_df.session_number = [int(number) for number in multi_session_df.session_number.values]
    multi_session_df['session_name'] = [get_session_labels()[session_number - 1] for session_number in
                                        multi_session_df.session_number.values]

    multi_session_df = remove_first_novel_session_retakes_from_multi_session_df(multi_session_df)
    multi_session_df = remove_outlier_traces_from_multi_session_df(multi_session_df)
    # multi_session_df = remove_problematic_data_from_multi_session_df(multi_session_df)

    return multi_session_df


def get_concatenated_stimulus_presentations(project_codes=None, session_numbers=None):
    """
    loads stimulus presentation table data for multiple sessions from cached files.
    dataframe contains stimulus information including image_name, change, licked, omitted, etc for every stimulus presentation.
    can be merged with stimulus_response_dfs to get cell responses for all stimulus presentations.

    if desired project codes and session numbers are not specified, all data will be loaded.
    project_codes and session_numbers should be provided as lists,
    ex: project_codes = ['VisualBehaviorTask1B', 'VisualBehaviorMultiscope], session_numbers = [3, 4]
    """

    save_dir = os.path.join(get_decoding_analysis_dir(), 'data')
    experiments_table = get_filtered_ophys_experiment_table()
    if project_codes is None:
        project_codes = experiments_table.project_code.unique()
    if session_numbers is None:
        session_numbers = experiments_table.session_number.unique()

    concatenated_stimulus_presentations = pd.DataFrame()
    for project_code in project_codes:
        for session_number in session_numbers:
            try:
                df = pd.read_hdf(os.path.join(save_dir, 'stimulus_presentations_' + project_code + '_session_' + str(
                    session_number) + '.h5'), key='df')
                concatenated_stimulus_presentations = pd.concat([concatenated_stimulus_presentations, df])
            except Exception as e:
                print('problem for', project_code, session_number)
                print(e)
    return concatenated_stimulus_presentations


def get_concatenated_stimulus_response_dfs(project_codes=None, session_numbers=None):
    """
    loads stimulus response dataframes for multiple sessions from cached files.
    dataframe contains the response of each cell for each stimulus presentation across sessions,
    including the trace in a [0, 0.75] second window, the mean response in that window, etc.
    can be merged with stimulus presentations to get the stimulus conditions for each cell response.

    if desired project codes and session numbers are not specified, all data will be loaded.
    project_codes and session_numbers should be provided as lists,
    ex: project_codes = ['VisualBehaviorTask1B', 'VisualBehaviorMultiscope], session_numbers = [3, 4]
    """

    save_dir = os.path.join(get_decoding_analysis_dir(), 'data')
    experiments_table = get_filtered_ophys_experiment_table()
    if project_codes is None:
        project_codes = experiments_table.project_code.unique()
    if session_numbers is None:
        session_numbers = experiments_table.session_number.unique()
    cre_lines = experiments_table.cre_line.unique()

    concatenated_stimulus_response_dfs = pd.DataFrame()
    for project_code in project_codes:
        for session_number in session_numbers:
            for cre_line in cre_lines:
                try:
                    df = pd.read_hdf(os.path.join(save_dir,
                                                  'stimulus_response_dfs_' + project_code + '_' + cre_line + '_session_' + str(
                                                      session_number) + '.h5'), key='df')
                    concatenated_stimulus_response_dfs = pd.concat([concatenated_stimulus_response_dfs, df])
                except Exception as e:
                    print('problem for', project_code, cre_line, session_number)
                    print(e)
    return concatenated_stimulus_response_dfs


def get_stimulus_response_data_across_sessions(project_codes=None, session_numbers=None):
    """
    loads and merges stimulus_response_dfs, stimulus_presentations data, and experiments_table metadata
    across sessions for a given set of project_codes and session_numbers.
    returns all cell responses for all image flashes for that set of sessions.

    if desired project codes and session numbers are not specified, all data will be loaded (slow).
    project_codes and session_numbers should be provided as lists,
    ex: project_codes = ['VisualBehaviorTask1B', 'VisualBehaviorMultiscope], session_numbers = [3, 4]
    """

    experiments_table = get_filtered_ophys_experiment_table()
    if project_codes is None:
        project_codes = experiments_table.project_code.unique()
    if session_numbers is None:
        session_numbers = experiments_table.session_number.unique()

    stim_presentations = get_concatenated_stimulus_presentations(project_codes, session_numbers)
    stim_response_dfs = get_concatenated_stimulus_response_dfs(project_codes, session_numbers)
    stimulus_response_data = stim_response_dfs.merge(stim_presentations, on='ophys_session_id')
    stimulus_response_data = stimulus_response_data.merge(experiments_table,
                                                          on=['ophys_experiment_id', 'ophys_session_id'])
    return stimulus_response_data


def get_container_response_df(container_id, df_name='omission_response_df', use_events=False):
    """
    get concatenated dataframe of response_df type specificied by df_name, across all experiments from a container
    """
    from visual_behavior.ophys.response_analysis.response_analysis import ResponseAnalysis
    experiments_table = get_filtered_ophys_experiment_table()
    container_expts = experiments_table[experiments_table.container_id==container_id]
    container_df = pd.DataFrame()
    for ophys_experiment_id in container_expts.index.values:
        dataset = get_ophys_dataset(ophys_experiment_id)
        analysis = ResponseAnalysis(dataset, use_events)
        odf = analysis.get_response_df(df_name=df_name)
        odf['ophys_experiment_id'] = ophys_experiment_id
        odf['session_number'] = experiments_table.loc[ophys_experiment_id].session_number
        container_df = pd.concat([container_df, odf])
    return container_df