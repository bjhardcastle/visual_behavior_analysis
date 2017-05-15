import pandas as pd

from functools import wraps
def data_or_pkl(func):
    """ Decorator that allows a function to accept a pickled experiment object
    or a path to the object.

    >>> @data_or_pkl
    >>> def print_keys(data):
    >>>     print data.keys()

    """

    @wraps(func)
    def pkl_wrapper(first_arg,*args,**kwargs):

        if isinstance(first_arg, basestring):
            return func(pd.read_pickle(first_arg))
        else:
            return func(first_arg)


    return pkl_wrapper

@data_or_pkl
def load_params(data):
    """ Returns the parameters passed in to an experiment.

    Parameters
    ----------
    data : dict, unpickled experiment (or path to pickled object)

    Returns
    -------
    params : dict

    """
    return data['params']

@data_or_pkl
def load_trials(data):
    """ Returns the trials generated in an experiment.

    Parameters
    ----------
    data : dict, unpickled experiment (or path to pickled object)

    Returns
    -------
    trials : pandas DataFrame

    """
    trials = pd.DataFrame(data['triallog'])

    return trials

@data_or_pkl
def load_time(data):
    """ Returns the times of each stimulus frame in an experiment.

    Parameters
    ----------
    data : dict, unpickled experiment (or path to pickled object)

    Returns
    -------
    time : numpy array

    """
    return data['vsyncintervals'].cumsum()

@data_or_pkl
def load_licks(data):
    """ Returns each lick in an experiment.

    Parameters
    ----------
    data : dict, unpickled experiment (or path to pickled object)

    Returns
    -------
    licks : numpy array

    """
    lick_frames = data['lickData'][0]-1
    time = load_time(data)

    licks = pd.DataFrame(dict(
            frame = lick_frames,
            time = time[lick_frames],
    ))




@data_or_pkl
def load_flashes(data):
    """ Returns the stimulus flashes in an experiment.

    NOTE: Currently only works for images & gratings.

    Parameters
    ----------
    data : dict, unpickled experiment (or path to pickled object)

    Returns
    -------
    flashes : pandas DataFrame

    See Also
    --------
    load_trials : loads trials

    """

    stimdf = pd.DataFrame(data['stimuluslog'])

    # first we find the flashes
    try:
        assert pd.isnull(stimdf['image_category']).any()==False
        flashes = stimdf[stimdf['state'].astype(int).diff()>0].reset_index()[['image_category','image_name','frame']]
#         flashes['change'] = (flashes['image_category'].diff()!=0)
        flashes['prior_image_category'] = flashes['image_category'].shift()
        flashes['image_category_change'] = flashes['image_category'].ne(flashes['prior_image_category']).astype(int)

        flashes['prior_image_name'] = flashes['image_name'].shift()
        flashes['image_name_change'] = flashes['image_name'].ne(flashes['prior_image_name']).astype(int)

        flashes['change'] = flashes['image_category_change']
    except (AssertionError,KeyError) as e:
        print "error in {}: {}".format(pkl,e)
        flashes = stimdf[stimdf['state'].astype(int).diff()>0].reset_index()[['ori','frame']]
        flashes['prior_ori'] = flashes['ori'].shift()
        flashes['ori_change'] = flashes['ori'].ne(flashes['prior_ori']).astype(int)

        flashes['change'] = flashes['ori_change']

    time = load_time(data)

    flashes['time'] = time[flashes['frame']]


    # then we find the licks
    licks = load_licks(data)
    licks['flash'] = np.searchsorted(flashes['frame'].values,licks['frame'].values) - 1,

    licks = licks[licks['frame'].diff()!=1] # filter out redundant licks
    licks = licks[licks['flash'].diff()>0] # get first lick from each flash

    # then we merge in the licks
    flashes = flashes.merge(
        licks,
        left_index=True,
        right_on='flash',
        suffixes=('','_lick'),
        how='left'
    ).set_index('flash')


    flashes['lick'] = ~pd.isnull(flashes['time_lick'])
    class Counter():
        def __init__(self):
            self.count = np.nan
        def count_it(self,val):
            count = self.count
            if val>0:
                self.count = 1
            else:
                self.count += 1
            return count

    flashes['last_lick'] = flashes['lick'].map(Counter().count_it)

    #then we find the rewards
    reward_frames = data['rewards'][:,1].astype(int) - 1

    rewards = pd.DataFrame(dict(
            frame = reward_frames,
            time = data['vsyncintervals'].cumsum()[reward_frames],
            flash = np.searchsorted(flashes['frame'].values,reward_frames) - 1,
    ))

    # then we merge in the rewards
    flashes = flashes.merge(
        rewards,
        left_index=True,
        right_on='flash',
        suffixes=('','_reward'),
        how='left',
    ).set_index('flash')

    # finally, we assign the trials
    try:
        trial_bounds = [dict(index=tr['index'],startframe=tr['startframe']) for tr in data['triallog']]
    except KeyError:
        trial_bounds = [dict(index=tr_index,startframe=tr['startframe']) for tr_index,tr in enumerate(data['triallog'])]

    trial_bounds = pd.DataFrame(trial_bounds)
    flashes['trial'] = np.searchsorted(trial_bounds['startframe'].values,flashes['frame'].values) - 1

    flashes['flashed'] = data['blank_duration_range'][1]>0

    flashes['mouse_id'] = data['mouseid']
    flashes['datetime'] = data['startdatetime']
    flashes['task'] = data['task']
    flashes['stage'] = data['stage']

    session_params = [
        'initial_blank',
        'delta_minimum',
        'delta_mean',
        'stimulus_distribution',
        'trial_duration',
        'stimulus',
        ]

    for param in session_params:
        try:
            flashes[param] = data[param]
        except KeyError:
            pass

    return flashes
