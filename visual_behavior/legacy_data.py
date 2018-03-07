import os
import pandas as pd
import numpy as np
from six import iteritems
from functools import wraps
from .processing import get_licks, get_time


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


@inplace
def annotate_parameters(trials, data, keydict=None):
    """ annotates a dataframe with session parameters

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials (or flashes)
    data : unpickled session
    keydict : dict
        {'column': 'parameter'}
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    io.load_flashes
    """
    if keydict is None:
        return
    else:
        for key, value in iteritems(keydict):
            try:
                trials[key] = [data[value]] * len(trials)
            except KeyError:
                trials[key] = None


@inplace
def explode_startdatetime(df):
    """ explodes the 'startdatetime' column into date/year/month/day/hour/dayofweek

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials (or flashes)
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    df['date'] = df['startdatetime'].dt.date.astype(str)
    df['year'] = df['startdatetime'].dt.year
    df['month'] = df['startdatetime'].dt.month
    df['day'] = df['startdatetime'].dt.day
    df['hour'] = df['startdatetime'].dt.hour
    df['dayofweek'] = df['startdatetime'].dt.weekday


@inplace
def annotate_n_rewards(df):
    """ computes the number of rewards from the 'reward_times' column

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    try:
        df['number_of_rewards'] = df['reward_times'].map(len)
    except KeyError:
        df['number_of_rewards'] = None


@inplace
def annotate_rig_id(df, data):
    """ adds a column with rig id

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    try:
        df['rig_id'] = data['rig_id']
    except KeyError:
        from visual_behavior.devices import get_rig_id
        df['rig_id'] = get_rig_id(df['computer_name'][0])


@inplace
def annotate_startdatetime(df, data):
    """ adds a column with the session's `startdatetime`

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    data : pickled session
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    df['startdatetime'] = pd.to_datetime(data['startdatetime'])


@inplace
def assign_session_id(df_in):
    """ adds a column with a unique ID for the session defined as
            a combination of the mouse ID and startdatetime

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    df_in['session_id'] = df_in['mouse_id'] + '_' + df_in['startdatetime'].map(lambda x: x.isoformat())


@inplace
def annotate_cumulative_reward(trials, data):
    """ adds a column with the session's cumulative volume

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    data : pickled session
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    try:
        trials['cumulative_volume'] = trials['reward_volume'].cumsum()
    except Exception:
        trials['reward_volume'] = data['rewardvol'] * trials['number_of_rewards']
        trials['cumulative_volume'] = trials['reward_volume'].cumsum()


@inplace
def annotate_filename(df, filename):
    """ adds `filename` and `filepath` columns to dataframe

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    filename : full filename & path of session's pickle file
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    df['filepath'] = os.path.split(filename)[0]
    df['filename'] = os.path.split(filename)[-1]


@inplace
def fix_autorearded(df):
    """ renames `auto_rearded` columns to `auto_rewarded`

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    df.rename(columns={'auto_rearded': 'auto_rewarded'}, inplace=True)


@inplace
def annotate_change_detect(trials):
    """ adds `change` and `detect` columns to dataframe

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """

    trials['change'] = trials['trial_type'] == 'go'
    trials['detect'] = trials['response'] == 1.0


@inplace
def fix_change_time(trials):
    """ forces `None` values in the `change_time` column to numpy NaN

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    trials['change_time'] = trials['change_time'].map(lambda x: np.nan if x is None else x)


@inplace
def explode_response_window(trials):
    """ explodes the `response_window` column in lower & upper columns

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    trials['response_window_lower'] = trials['response_window'].map(lambda x: x[0])
    trials['response_window_upper'] = trials['response_window'].map(lambda x: x[1])


@inplace
def annotate_epochs(trials, epoch_length=5.0):
    """ annotates the dataframe with an additional column which designates
    the "epoch" from session start

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    epoch_length : float
        length of epochs in seconds
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """

    trials['epoch'] = (
        trials['change_time']
        .map(lambda x: x / (60 * epoch_length))
        .round()
        .map(lambda x: x * epoch_length)
        # .map(lambda x: "{:0.1f} min".format(x))
    )


@inplace
def annotate_lick_vigor(trials, data, window=3.5):
    """ annotates the dataframe with two columns that indicate the number of
    licks and lick rate in 1/s

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    window : window relative to reward time for licks to include
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """

    licks = get_licks(data)

    def find_licks(reward_times):
        try:
            reward_time = reward_times[0]
        except IndexError:
            return None

        reward_lick_mask = (
            (licks['time'] > reward_time)
            & (licks['time'] < (reward_time + window))
        )

        tr_licks = licks[reward_lick_mask].copy()
        tr_licks['time'] -= reward_time
        return tr_licks['time'].values

    def number_of_licks(licks):
        return len(licks)

    trials['reward_licks'] = trials['reward_times'].map(find_licks)
    trials['reward_lick_count'] = trials['reward_licks'].map(lambda lks: len(lks) if lks is not None else None)
    # trials['reward_lick_rate'] = trials['reward_lick_number'].map(lambda n: n / window)

    def min_licks(lks):
        if lks is None:
            return None
        elif len(lks) == 0:
            return None
        else:
            return np.min(lks)

    trials['reward_lick_latency'] = trials['reward_licks'].map(min_licks)


@inplace
def annotate_trials(trials):
    """ performs multiple annotatations:

    - annotate_change_detect
    - fix_change_time
    - explode_response_window

    Parameters
    ----------
    trials : pandas DataFrame
        dataframe of trials
    inplace : bool, optional
        modify `trials` in place. if False, returns a copy. default: True

    See Also
    --------
    io.load_trials
    """
    # build arrays for change detection
    annotate_change_detect(trials, inplace=True)

    # assign a session ID to each row
    assign_session_id(trials, inplace=True)

    # calculate reaction times
    fix_change_time(trials, inplace=True)

    # unwrap the response window
    explode_response_window(trials, inplace=True)


@inplace
def update_times(trials, data, time=None):

    if time is None:
        time = get_time(data)

    time_frame_map = {
        'change_time': 'change_frame',
        'starttime': 'startframe',
        'endtime': 'endframe',
        'lick_times': 'lick_frames',
        'reward_times': 'reward_frames',
    }

    def update(fr):
        try:
            if pd.isnull(fr) == True:  # this should catch np.nans
                return None
            else:  # this should be for floats
                return time[int(fr)]
        except (TypeError, ValueError):  # this should catch lists
            return time[[int(f) for f in fr]]

    for time_col, frame_col in iteritems(time_frame_map):
        try:
            trials[time_col] = trials[frame_col].map(update)
        except KeyError:
            print('oops! {} does not exist'.format(frame_col))
            pass

    def make_array(val):
        try:
            len(val)
        except TypeError as e:
            val = [val, ]
        return val

    must_be_arrays = ('lick_times', 'reward_times')
    for col in must_be_arrays:
        trials[col] = trials[col].map(make_array)
