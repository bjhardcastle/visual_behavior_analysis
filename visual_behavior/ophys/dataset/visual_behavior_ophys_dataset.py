"""
Created on Sunday July 15 2018

@author: marinag
"""
import os
import h5py
import platform
import numpy as np
import pandas as pd


class VisualBehaviorOphysDataset(object):
    def __init__(self, experiment_id, cache_dir=None):
        """initialize visual behavior ophys experiment dataset.
            loads processed experiment data from cache_dir

        Parameters
        ----------
        experiment_id : ophys experiment ID (not session ID)
        cache_dir : directory to save or load analysis files to/from
        """
        self.experiment_id = experiment_id
        self.cache_dir = cache_dir
        self.cache_dir = self.get_cache_dir()
        self.get_analysis_dir()
        self.get_metadata()
        self.get_timestamps()
        self.get_timestamps_ophys()
        self.get_timestamps_stimulus()
        self.get_visual_stimuli()
        self.get_running()
        self.get_licks()
        self.get_rewards()
        self.get_trials()
        self.get_dff_traces()
        self.get_roi_masks()
        self.get_roi_metrics()
        self.get_max_projection()
        self.get_motion_correction()
        # self.get_pupil_diameter()
        # self.get_corrected_fluorescence_traces()
        # self.get_events()

    def get_cache_dir(self):
        if self.cache_dir is None:
            if platform.system() == 'Linux':
                cache_dir = r'/allen/aibs/informatics/swdb2018/visual_behavior'
            else:
                cache_dir = r'\\allen\aibs\informatics\swdb2018\visual_behavior'
            print 'using default cache_dir:', cache_dir # flake8: noqa: E999
        else:
            cache_dir = self.cache_dir
        self.cache_dir = cache_dir
        return self.cache_dir

    def get_analysis_dir(self):
        analysis_folder = [file for file in os.listdir(self.cache_dir) if str(self.experiment_id) in file]
        if len(analysis_folder) > 0:
            self.analysis_folder = analysis_folder[0]
            self.analysis_dir = os.path.join(self.cache_dir, self.analysis_folder)
        else:
            self.analysis_dir = None
            print 'no analysis folder  found for ', self.experiment_id
        return self.analysis_dir

    def get_metadata(self):
        self.metadata = pd.read_hdf(os.path.join(self.analysis_dir, 'metadata.h5'), key='df', format='fixed')
        return self.metadata

    def get_timestamps(self):
        self.timestamps = pd.read_hdf(os.path.join(self.analysis_dir, 'timestamps.h5'), key='df', format='fixed')

    def get_timestamps_stimulus(self):
        self.timestamps_stimulus = self.timestamps['stimulus_frames']['timestamps']
        return self.timestamps_stimulus

    def get_timestamps_ophys(self):
        self.timestamps_ophys = self.timestamps['ophys_frames']['timestamps']
        return self.timestamps_ophys

    def get_visual_stimuli(self):
        self.visual_stimuli = pd.read_hdf(os.path.join(self.analysis_dir, 'visual_stimuli.h5'), key='df', format='fixed')
        return self.visual_stimuli

    def get_running(self):
        self.running = pd.read_hdf(os.path.join(self.analysis_dir, 'running.h5'), key='df', format='fixed')
        return self.running

    def get_licks(self):
        self.licks = pd.read_hdf(os.path.join(self.analysis_dir, 'licks.h5'), key='df', format='fixed')
        return self.licks

    def get_rewards(self):
        self.rewards = pd.read_hdf(os.path.join(self.analysis_dir, 'rewards.h5'), key='df', format='fixed')
        return self.rewards

    def get_trials(self):
        self.all_trials = pd.read_hdf(os.path.join(self.analysis_dir, 'trials.h5'), key='df', format='fixed')
        all_trials = self.all_trials.copy()
        trials = all_trials[(all_trials.auto_rewarded != True) & (all_trials.trial_type != 'aborted')].reset_index()
        trials = trials.rename(columns={'level_0': 'index'})
        trials.insert(loc=0, column='trial', value=trials.index.values)
        self.trials = trials
        return self.trials

    def get_dff_traces(self):
        f = h5py.File(os.path.join(self.analysis_dir, 'dff_traces.h5'), 'r')
        dff_traces = []
        for key in f.keys():
            dff_traces.append(np.asarray(f[key]))
        f.close()
        self.dff_traces = np.asarray(dff_traces)
        return self.dff_traces

    def get_roi_masks(self):
        f = h5py.File(os.path.join(self.analysis_dir, 'roi_masks.h5'), 'r')
        roi_masks = {}
        for key in f.keys():
            roi_masks[key] = np.asarray(f[key])
        f.close()
        self.roi_masks = roi_masks
        return self.roi_masks

    def get_roi_metrics(self):
        self.roi_metrics = pd.read_hdf(os.path.join(self.analysis_dir, 'roi_metrics.h5'), key='df', format='fixed')
        return self.roi_metrics

    def get_max_projection(self):
        f = h5py.File(os.path.join(self.analysis_dir, 'max_projection.h5'), 'r')
        self.max_projection = np.asarray(f['data'])
        f.close()
        return self.max_projection

    def get_motion_correction(self):
        self.motion_correction = pd.read_hdf(os.path.join(self.analysis_dir, 'motion_correction.h5'), key='df',
                                             format='fixed')
        return self.motion_correction
