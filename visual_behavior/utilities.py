from __future__ import print_function
from dateutil import parser, tz
from functools import wraps
import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
import datetime
import os
import h5py
import cv2
import warnings

from sync import Dataset

from . import database as db


def flatten_list(in_list):
    out_list = []
    for i in range(len(in_list)):
        # check to see if each entry is a list or array
        if isinstance(in_list[i], list) or isinstance(in_list[i], np.ndarray):
            # if so, iterate over each value and append to out_list
            for entry in in_list[i]:
                out_list.append(entry)
        else:
            # otherwise, append the value itself
            out_list.append(in_list[i])

    return out_list


def get_response_rates(df_in, sliding_window=100, apply_trial_number_limit=False):
    """
    calculates the rolling hit rate, false alarm rate, and dprime value
    Note that the pandas rolling metric deals with NaN values by propogating the previous non-NaN value

    Parameters
    ----------
    sliding_window : int
        Number of trials over which to calculate metrics

    Returns
    -------
    tuple containing hit rate, false alarm rate, d_prime

    """

    from visual_behavior.translator.core.annotate import is_catch, is_hit

    go_responses = df_in.apply(is_hit, axis=1)

    hit_rate = go_responses.rolling(
        window=sliding_window,
        min_periods=0,
    ).mean().values

    catch_responses = df_in.apply(is_catch, axis=1)

    catch_rate = catch_responses.rolling(
        window=sliding_window,
        min_periods=0,
    ).mean().values

    if apply_trial_number_limit:
        # avoid values close to 0 and 1
        go_count = go_responses.rolling(
            window=sliding_window,
            min_periods=0,
        ).count()

        catch_count = catch_responses.rolling(
            window=sliding_window,
            min_periods=0,
        ).count()

        hit_rate = np.vectorize(trial_number_limit)(hit_rate, go_count)
        catch_rate = np.vectorize(trial_number_limit)(catch_rate, catch_count)

    d_prime = dprime(hit_rate, catch_rate)

    return hit_rate, catch_rate, d_prime


class RisingEdge():
    """
    This object implements a "rising edge" detector on a boolean array.

    It takes advantage of how pandas applies functions in order.

    For example, if the "criteria" column in the `df` dataframe consists of booleans indicating
    whether the row meets a criterion, we can detect the first run of three rows above criterion
    with the following

        first_run_of_three = (
            df['criteria']
            .rolling(center=False,window=3)
            .apply(func=RisingEdge().check)
            )

    ```

    """

    def __init__(self):
        self.firstall = False

    def check(self, arr):
        if arr.all():
            self.firstall = True
        return self.firstall


# -> metrics
def trial_number_limit(p, N):
    if N == 0:
        return np.nan
    if not pd.isnull(p):
        p = np.max((p, 1. / (2 * N)))
        p = np.min((p, 1 - 1. / (2 * N)))
    return p


def dprime(hit_rate, fa_rate, limits=(0.01, 0.99)):
    """ calculates the d-prime for a given hit rate and false alarm rate

    https://en.wikipedia.org/wiki/Sensitivity_index

    Parameters
    ----------
    hit_rate : float
        rate of hits in the True class
    fa_rate : float
        rate of false alarms in the False class
    limits : tuple, optional
        limits on extreme values, which distort. default: (0.01,0.99)

    Returns
    -------
    d_prime

    """
    assert limits[0] > 0.0, 'limits[0] must be greater than 0.0'
    assert limits[1] < 1.0, 'limits[1] must be less than 1.0'
    Z = norm.ppf

    # Limit values in order to avoid d' infinity
    hit_rate = np.clip(hit_rate, limits[0], limits[1])
    fa_rate = np.clip(fa_rate, limits[0], limits[1])

    # fill nans with 0.5 to avoid warning about nans
    d_prime = Z(pd.Series(hit_rate)) - Z(pd.Series(fa_rate))

    if len(d_prime) == 1:
        # if the result is a 1-length vector, return as a scalar
        return d_prime[0]
    else:
        return d_prime


def calc_deriv(x, time):
    dx = np.diff(x)
    dt = np.diff(time)
    dxdt_rt = np.hstack((np.nan, dx / dt))
    dxdt_lt = np.hstack((dx / dt, np.nan))

    dxdt = np.vstack((dxdt_rt, dxdt_lt))

    dxdt = np.nanmean(dxdt, axis=0)

    return dxdt


def deg_to_dist(speed_deg_per_s):
    '''
    takes speed in degrees per second
    converts to radians
    multiplies by radius (in cm) to get linear speed in cm/s
    '''
    wheel_diameter = 6.5 * 2.54  # 6.5" wheel diameter
    running_radius = 0.5 * (
        2.0 * wheel_diameter / 3.0)  # assume the animal runs at 2/3 the distance from the wheel center
    running_speed_cm_per_sec = np.pi * speed_deg_per_s * running_radius / 180.
    return running_speed_cm_per_sec


def local_time(iso_timestamp, timezone=None):
    if isinstance(iso_timestamp, datetime.datetime):
        dt = iso_timestamp
    else:
        dt = parser.parse(iso_timestamp)

    if not dt.tzinfo:
        dt = dt.replace(tzinfo=tz.gettz('America/Los_Angeles'))
    return dt.isoformat()


class ListHandler(logging.Handler):
    """docstring for ListHandler."""

    def __init__(self, log_list):
        super(ListHandler, self).__init__()
        self.log_list = log_list

    def emit(self, record):
        entry = self.format(record)
        self.log_list.append(entry)


DoubleColonFormatter = logging.Formatter(
    "%(levelname)s::%(name)s::%(message)s",
)


def inplace(func):
    """ decorator which allows functions that modify a dataframe inplace
    to use a copy instead
    """

    @wraps(func)
    def df_wrapper(df, *args, **kwargs):

        try:
            inplace = kwargs.pop('inplace')
        except KeyError:
            inplace = False

        if inplace is False:
            df = df.copy()

        func(df, *args, **kwargs)

        if inplace is False:
            return df
        else:
            return None

    return df_wrapper


def find_nearest_index(val, time_array):
    '''
    Takes an input (can be a scalar, list, or array) and a time_array
    Returns the index or indices of the time points in time_array that are closest to val
    '''
    if hasattr(val, "__len__"):
        idx = np.zeros(len(val), dtype=int)
        for i, v in enumerate(val):
            idx[i] = np.argmin(np.abs(v - np.array(time_array)))
    else:
        idx = np.argmin(np.abs(val - np.array(time_array)))
    return idx


class Movie(object):
    '''
    a class for loading movies captured with videomon

    Args
    ----------
    filepath (string):
        path to the movie file
    sync_timestamps (array), optional:
        array of timestamps acquired by sync. None by default
    h5_filename (string), optional:
        path to h5 file. assumes by default that filename matches movie filename, but with .h5 extension
    lazy_load (boolean), defaults True:
        when True, each frame is loaded from disk when requested. When False, the entire movie is loaded into memory on intialization (can be very slow)

    Attributes:
    ------------
    frame_count (int):
        number of frames in movie
    width (int):
        width of each frame
    height (int):
        height of each frame

    Todo:
    --------------
    - non-lazy-load a defined interval (would this be useful?)
    '''

    def __init__(self, filepath, sync_timestamps=None, h5_filename=None, lazy_load=True):

        self.cap = cv2.VideoCapture(filepath)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.filepath = filepath

        if sync_timestamps is not None:
            self.sync_timestamps = sync_timestamps
        else:
            self.sync_timestamps = None

        if not h5_filename:
            h5_filename = filepath.replace('.avi', '.h5')
        if os.path.exists(h5_filename):
            timestamp_file = h5py.File(filepath.replace('.avi', '.h5'))

            # videomon saves an h5 file with frame intervals. Take cumulative sum to get timestamps
            self.timestamps_from_file = np.hstack((0, np.cumsum(timestamp_file['frame_intervals'])))
            if self.sync_timestamps is not None and len(self.sync_timestamps) != len(self.timestamps_from_file):
                warnings.warn('NONMATCHING timestamp counts\nThere are {} timestamps in sync and {} timestamps in the associated camera file\nthese should match'.format(
                    len(self.sync_timestamps), len(self.timestamps_from_file)))
        else:
            warnings.warn('Movies often have a companion h5 file with a corresponding name. None found for this movie. Expected {}'.format(h5_filename))
            self.timestamps_from_file = None

        self._lazy_load = lazy_load
        if self._lazy_load == False:
            self._get_array()
        else:
            self.array = None

    def get_frame(self, frame=None, time=None, timestamps='sync'):
        if time and timestamps == 'sync':
            assert self.sync_timestamps is not None, 'sync timestamps do not exist'
            timestamps = self.sync_timestamps
        elif time and timestamps == 'file':
            assert self.timestamps_from_file is not None, 'timestamps from file do not exist'
            timestamps = self.timestamps_from_file
        else:
            timestamps = None

        if time is not None and frame is None:
            assert timestamps is not None, 'must pass a timestamp array if referencing by time'
            frame = find_nearest_index(time, timestamps)

        # use open CV to get the frame from disk if lazy mode is True
        if self._lazy_load:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
            found_frame, frame_array = self.cap.read()
            if found_frame == True:
                return frame_array
            else:
                warnings.warn("Couldn't find frame {}, returning None".format(frame))
                return None
        # or get the frame the preloaded array
        else:
            return self.array[frame, :, :]

    def _get_array(self, dtype='uint8'):
        '''iterate over movie, load frames into an in-memory numpy array one at a time (slow and memory intensive)'''
        self.array = np.empty((self.frame_count, self.height, self.width), np.dtype(dtype))

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        for N in range(self.frame_count):
            found_frame, frame = self.cap.read()
            if not found_frame:
                print('something went wrong on frame {}, stopping'.format(frame))
                break
            self.array[N, :, :] = frame[:, :, 0]


def get_sync_data(sync_path):
    sync_data = Dataset(sync_path)

    sample_freq = sync_data.meta_data['ni_daq']['counter_output_freq']
    line_labels = [label for label in sync_data.meta_data['line_labels'] if label != '']
    sd = {}
    for line_label in line_labels:
        sd.update({line_label + '_rising': sync_data.get_rising_edges(line_label) / sample_freq})
        sd.update({line_label + '_falling': sync_data.get_falling_edges(line_label) / sample_freq})

    return sd


class EyeTrackingData(object):
    def __init__(self, ophys_session_id, data_source='mongodb', pupil_color=[0, 0, 255], eye_color=[255, 0, 0], cr_color=[0, 255, 0]):
        well_known_files = db.get_well_known_files(ophys_session_id)

        # colors of ellipses:
        self.pupil_color = pupil_color
        self.eye_color = eye_color
        self.cr_color = cr_color

        # get paths of well known files
        self.eye_movie_path = ''.join(well_known_files.query('name=="RawEyeTrackingVideo"')[['storage_directory', 'filename']].iloc[0].tolist())
        self.behavior_movie_path = ''.join(well_known_files.query('name=="RawBehaviorTrackingVideo"')[['storage_directory', 'filename']].iloc[0].tolist())
        self.sync_path = ''.join(well_known_files.query('name=="OphysRigSync"')[['storage_directory', 'filename']].iloc[0].tolist())
        self.ellipse_fit_path = ''.join(well_known_files.query('name=="EyeTracking Ellipses"')[['storage_directory', 'filename']].iloc[0].tolist())

        self.ophys_session_id = ophys_session_id
        self.foraging_id = db.get_value_from_table('id', ophys_session_id, 'ophys_sessions', 'foraging_id')

        self.sync_data = get_sync_data(self.sync_path)

        # open behavior and eye movies
        self.eye_movie = Movie(self.eye_movie_path)
        self.behavior_movie = Movie(self.behavior_movie_path)

        # assign timestamps from sync
        for movie in [self.eye_movie, self.behavior_movie]:
            movie.sync_timestamps = self.sync_data[self.get_matching_sync_line(movie, self.sync_data)]

        self.ellipse_fits = {}
        if data_source == 'filesystem':
            # get ellipse fits from h5 files
            for dataset in ['pupil', 'eye', 'cr']:
                self.ellipse_fits[dataset] = self.get_eye_data_from_file(self.ellipse_fit_path, dataset=dataset, timestamps=self.eye_movie.sync_timestamps)

            # replace the 'cr' key with 'corneal_reflection for clarity
            self.ellipse_fits['corneal_reflection'] = self.ellipse_fits.pop('cr')

        elif data_source == 'mongodb':
            mongo_db = db.Database('visual_behavior_data')

            for dataset in ['pupil', 'eye', 'corneal_reflection']:
                res = list(mongo_db['eyetracking'][dataset].find({'ophys_session_id': self.ophys_session_id}))
                self.ellipse_fits[dataset] = pd.concat([pd.DataFrame(r['data']) for r in res]).reset_index()

            mongo_db.close()

    def get_matching_sync_line(self, movie, sync_data):
        '''determine which sync line matches the frame count of a given movie'''
        nframes = movie.frame_count
        for candidate_line in ['cam1_exposure_rising', 'cam2_exposure_rising', 'behavior_monitoring_rising', 'eye_tracking_rising']:
            if candidate_line in sync_data.keys() and nframes == len(sync_data[candidate_line]):
                return candidate_line
        return None

    def get_eye_data_from_file(self, eye_tracking_path, dataset='pupil', timestamps=None):
        '''open ellipse fit. try to match sync data if possible'''

        df = pd.read_hdf(eye_tracking_path, dataset)

        def area(row):
            # calculate the area as a circle using the max of the height/width as radius
            max_dim = max(row['height'], row['width'])
            return np.pi * max_dim**2

        df['area'] = df[['height', 'width']].apply(area, axis=1)

        if timestamps is not None:
            df['t'] = timestamps

        df['frame'] = np.arange(len(df)).astype(int)

        # imaginary numbers sometimes show up in the ellipse fits. I'm not sure why, but I'm assuming it's an artifact of the fitting process.
        # Convert them to real numbers
        for col in df.columns:
            df[col] = np.real(df[col])

        return df

    def add_ellipse(self, image, ellipse_fit_row, color=[1, 1, 1]):
        '''adds an ellipse fit to an eye tracking video frame'''
        if pd.notnull(ellipse_fit_row['center_x'].item()):
            center_coordinates = (
                int(ellipse_fit_row['center_x'].item()),
                int(ellipse_fit_row['center_y'].item())
            )

            axesLength = (
                int(ellipse_fit_row['width'].item()),
                int(ellipse_fit_row['height'].item())
            )

            angle = ellipse_fit_row['phi']
            startAngle = 0
            endAngle = 360

            # Line thickness of 5 px
            thickness = 3

            # Using cv2.ellipse() method
            # Draw a ellipse with red line borders of thickness of 5 px
            image = cv2.ellipse(image, center_coordinates, axesLength,
                                angle, startAngle, endAngle, color, thickness)

        return image

    def get_annotated_frame(self, frame=None, time=None, pupil=True, eye=True, corneal_reflection=False):
        '''get a particular eye video frame with ellipses drawn'''
        if time is None and frame is None:
            warnings.warn('must specify either a frame or time')
            return None
        elif time is not None and frame is not None:
            warnings.warn('cannot specify both frame and time')
            return None

        if time is not None:
            frame = np.argmin(np.abs(time - self.eye_movie.sync_timestamps))

        image = self.eye_movie.get_frame(frame=frame)

        if pupil:
            image = self.add_ellipse(image, self.ellipse_fits['pupil'].query('frame == @frame'), color=self.pupil_color)

        if eye:
            image = self.add_ellipse(image, self.ellipse_fits['eye'].query('frame == @frame'), color=self.eye_color)

        if corneal_reflection:
            image = self.add_ellipse(image, self.ellipse_fits['corneal_reflection'].query('frame == @frame'), color=self.cr_color)

        return image
