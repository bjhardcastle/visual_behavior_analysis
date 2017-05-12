import numpy as np
import pandas as pd
import os
import glob
import sys
import time
from fnmatch import fnmatch
import socket
import warnings

from braintv_behav.io import load_trials

from braintv_behav.data import annotate_parameters, explode_startdatetime, annotate_n_rewards
from braintv_behav.data import annotate_rig_id, annotate_startdatetime, annotate_cumulative_reward
from braintv_behav.data import annotate_filename, fix_autorearded

# -> io.py
def create_doc_dataframe(filename):
    data = pd.read_pickle(filename)

    df = load_trials(data)
    df = df[~pd.isnull(df['reward_times'])].reset_index()

    #add some columns to the dataframe
    keydict = {
        'mouse_id': 'mouseid',
        'response_window': 'response_window',
        'task': 'task',
        'session_duration': 'stoptime',
        'user_id': 'userid',
        'LDT_mode': 'lick_detect_training_mode',
        'blank_screen_timeout': 'blankscreen_on_timeout',
        'stim_duration': 'stim_duration',
        'blank_duration_range': 'blank_duration_range',
        'prechange_minimum': 'delta_minimum',
        'stimulus_distribution': 'stimulus_distribution',
        'stimulus': 'stimulus',
        'distribution_mean': 'delta_mean',
        'trial_duration': 'trial_duration',
        'computer_name': 'computer_name',
        }
    
    
    annotate_parameters(df,data,keydict=keydict,inplace=True)
    annotate_startdatetime(df,data,inplace=True)
    explode_startdatetime(df,inplace=True)
    annotate_n_rewards(df,inplace=True)
    annotate_rig_id(df,data,inplace=True)
    fix_autorearded(df,inplace=True)
    annotate_cumulative_reward(df,data,inplace=True)
    annotate_filename(df,filename,inplace=True)


    for col in ('auto_rewarded','change_time'):
        if col not in df.columns:
            df[col] = None

    #add some columns that require calculation
    calculate_latency(df)
    calculate_reward_rate(df)

    df['trial_type'] = categorize_trials(df)
    df['response'] = check_responses(df)
    df['trial_length'] = calculate_trial_length(df)
    df['endframe'] = get_end_frame(df,last_frame = len(data['vsyncintervals']))
    df['color'] = assign_color(df)
    df['response_type'] = get_response_type(df)
    df['lick_frames'] = get_lick_frames(df,data)
    # df['last_lick'] = get_last_licktimes(df,data)

    try:
        remove_repeated_licks(df)
    except Exception as e:
        print 'FAILED TO REMOVE REPEATED LICKS'
        print e


    return df


# -> DEPRECATE
def get_mouse_info(mouse_id):
    '''
    Gets data from the info.txt file in each mouse's folder on aibsdata
    '''
    import warnings
    warnings.warn(
        "this function is deprecated. please use the `mouse_info` package",
        DeprecationWarning
    )
    from braintv_behav.cohorts import mouse_info
    return mouse_info(mouse_id)

# -> analyze.py
def get_lick_frames(df_in,data):
    """
    returns a list of arrays of lick frames, with one entry per trial
    """
    lick_frames = data['lickData'][0]
    local_licks = []
    for idx,row in df_in.iterrows():
        local_licks.append(lick_frames[np.logical_and(lick_frames>=int(row['startframe']),
                                                      lick_frames<=int(row['endframe']))])

    return local_licks

# -> analyze.py
def get_last_licktimes(df_in,data):
    '''
    get time of most recent lick before every change
    '''
    time_arr = np.hstack((0,np.cumsum(data['vsyncintervals'])/1000.))

    licks = time_arr[data['lickData'][0]]
    
    #get times of all changes in this dataset
    change_frames = df_in.change_frame.values
    
    change_times = np.zeros(len(change_frames))*np.nan
    last_lick = np.zeros(len(change_frames))*np.nan
    for ii,frame in enumerate(change_frames):
        if np.isnan(frame) == False:
            change_times[ii] = time_arr[frame.astype(int)]
            #when was the last lick?
            a = licks-change_times[ii]
            try:
                last_lick[ii] = np.max(a[a<0])
            except:
                pass

    return last_lick



# -> analyze.py
def remove_repeated_licks(df_in):
    """
    the stimulus code records one lick for each frame in which the tongue was in contact with the spout
    if a single lick spans multiple frames, it'll be recorded as multiple licks
    this method will throw out the lick times and lick frames after the initial contact
    """
    lt = []
    lf = []
    for idx,row in df_in.iterrows():
        
        #get licks for this frame
        lick_frames_on_this_trial = row.lick_frames
        lick_times_on_this_trial = row.lick_times
        if len(lick_frames_on_this_trial) > 0:
            #use the number of frames between each lick to determine which to keep
            if len(lick_frames_on_this_trial)>1:
                    lick_intervals = np.hstack((np.inf,np.diff(lick_frames_on_this_trial)))
            else:
                lick_intervals = np.array([np.inf])

            #only keep licks that are preceded by at least one frame without a lick
            lf.append(list(np.array(lick_frames_on_this_trial)[lick_intervals>1]))
            lt.append(list(np.array(lick_times_on_this_trial)[lick_intervals[:len(lick_times_on_this_trial)]>1]))
        else:
            lt.append([])
            lf.append([])
            
    #replace the appropriate rows of the dataframe
    df_in['lick_times'] = lt
    df_in['lick_frames'] = lf

# -> io.py
def load_from_folder(foldername,load_existing_dataframe=True,save_dataframe=True,filename_contains='*'):
    '''
    Loads all PKL files in a given directory
    if load_existing_dataframe is True, will attempt to load previously saved dataframe in same folder to save time
    if save_dataframe is True, will save dataframe in folder to save loading time on next run
    '''

    if load_existing_dataframe==True:
        try:
            df = pd.read_pickle(os.path.join(foldername,'summary_df.pkl'))
            previously_loaded_filenames = df.filename.unique()
        except Exception as e:
            df = pd.DataFrame()
            previously_loaded_filenames = []
    else:
        df = pd.DataFrame()
        previously_loaded_filenames = []

    unloaded = []
    for ii,filename in enumerate(os.listdir(foldername)):
        if filename not in previously_loaded_filenames and ".pkl" in filename and 'summary' not in filename and fnmatch(filename, '*'+filename_contains+'*'):
            try:
                dft = create_doc_dataframe(os.path.join(foldername,filename))
                unloaded.append(dft)
            except Exception as e:
                print "error loading file {}: {}".format(filename,e)
                continue
    df = pd.concat([df,]+unloaded,ignore_index=True)
    #count unique days of training for each session
    try:
        df['training_day'] = get_training_day(df)
    except Exception as e:
        warnings.warn("Couldn't calculate training day")

    if save_dataframe == True:
        df.to_pickle(os.path.join(foldername,'summary_df.pkl'))

    return df

from braintv_behav.devices import get_rig_id

# -> devices.py
def return_reward_volumes(cluster_id):
    '''
    Prints a report to the console window telling the user how much water the animals
    in cluster_id have:
        a) received so far, if the session is still running
        b) received in the last session, if no session is currently running
    '''
    from zro import Proxy
    for rig in range(1,7):
        computer_name = get_rig_id('{}{}'.format(cluster_id,rig),input_type='rig_id')
        print 'Rig {}{}'.format(cluster_id,rig)
        try:
            agent = Proxy('{}:5000'.format(computer_name),timeout=2)
    #         print agent.status
            if agent.status['running'] == True:
                print "mouse {} is currently running in this rig".format(agent.status['mouse_id'])
                session =Proxy('{}:12000'.format(computer_name),timeout=2)
                N,V = len(np.array(session.rewards)[:,0]),np.sum(np.array(session.rewards)[:,3])
            elif agent.status['running'] == False:
                print "getting data for last session from mouse: {}".format(agent.status['mouse_id'])
                N,V = get_reward_volume_last_session(agent.status['mouse_id'])
            print "number of rewards = {}".format(N)
            print "total volume = {} mL".format(V)
        except Exception as e:
            print "failed to get data"
            print e
        print ""
        

def get_reward_volume_last_session(mouse_id):
    '''
    returns number of rewards and total volume for last session for a given mouse
    '''
    fn = get_datafile(mouse_id)
    data = pd.read_pickle(fn)
    return len(data['rewards'][:,0]),np.sum(data['rewards'][:,3])

def get_datafile(mouse_id,year=None,month=None,day=None,return_longest=True,location=None):
    '''
    returns path to filenames for a given mouse and date
    year should be four digits

    if return_longest is True (default):
        returns only the longest file for the given day (to avoid short sessions that were aborted early)
    if return_longest is False:
        returns a list of all filenames for the given day
    '''
    if location is None and sys.platform == 'darwin':
        location = os.path.join('/Volumes/neuralcoding/behavior/data',mouse_id,'output')
    elif location is None and sys.platform != 'darwin':
        location = os.path.join('//aibsdata/neuralcoding/behavior/data',mouse_id,'output')

    if year == None or day == None or month == None:
        # if any of the date arguments are none, return the newest
        fnames = glob.glob('{}/*.pkl'.format(location)) 
        fnames_lim = [fn for fn in fnames if not os.path.basename(fn).endswith('df.pkl')]
        newest = max(fnames_lim, key=os.path.getctime)
        return newest
    else:
        matches = []
        filesizes = []
        for filename in os.listdir(location):
            try:
                timestamp = pd.to_datetime(filename.split('-')[0],format='%y%m%d%H%M%S')
                if timestamp.year ==int(year) and timestamp.month ==int(month) and timestamp.day == int(day):
                    #check to see if mouseID is in filename:
                    if 'mouse='+mouse_id in filename or 'mouse=' not in filename:
                        matches.append(filename)
                        filesizes.append(os.path.getsize(location))

            except:
                pass

        if len(matches)>1 and return_longest==False:
            return [os.path.join(location,fn) for fn in matches]
        elif len(matches)>1 and return_longest==True:
            longest_file_index = filesizes.index(max(filesizes))
            return os.path.join(location,matches[longest_file_index])
        elif len(matches)==1:
            return os.path.join(location,matches[0])
        else:
            return None

# -> plotting.py
def save_figure(fig, fname, formats = ['.png'],transparent=False,dpi=300,**kwargs):
    import matplotlib as mpl
    mpl.rcParams['pdf.fonttype'] = 42
    if 'size' in kwargs.keys():
        fig.set_size_inches(kwargs['size'])
    else:
        fig.set_size_inches(11,8.5)
    for f in formats:
        fig.savefig(fname + f, transparent = transparent, orientation = 'landscape',dpi=dpi)

# -> analyze
def calculate_reward_rate(df,window=1.0,trial_window=25,remove_aborted=False):
    #written by Dan Denman (stolen from http://stash.corp.alleninstitute.org/users/danield/repos/djd/browse/calculate_reward_rate.py)
    #add a column called reward_rate to the input dataframe
    #the reward_rate column contains a rolling average of rewards/min
    #window sets the window in which a response is considered correct, so a window of 1.0 means licks before 1.0 second are considered correct
    #remove_aborted flag needs work, don't use it for now
    reward_rate = np.zeros(np.shape(df.change_time))
    c=0
    for startdatetime in df.startdatetime.unique():                      # go through the dataframe by each behavior session
                          # get a dataframe for just this session
        if remove_aborted == True:
            warnings.warn("Don't use remove_aborted yet. Code needs work")
            df_temp = df[(df.startdatetime==startdatetime)&(df.trial_type != 'aborted')].reset_index()
        else:
            df_temp = df[df.startdatetime==startdatetime]  
        trial_number = 0
        for trial in range(len(df_temp)):
            if trial_number <10 :                                        # if in first 10 trials of experiment
                reward_rate_on_this_lap = np.inf                         # make the reward rate infinite, so that you include the first trials automatically.
            else:                     
                #ensure that we don't run off the ends of our dataframe                                   # get the correct response rate around the trial
                min_index = np.max((0,trial-trial_window))
                max_index = np.min((trial+trial_window,len(df_temp)))
                df_roll = df_temp.iloc[min_index:max_index]


                correct = len(df_roll[df_roll.response_latency<window])    # get a rolling number of correct trials
                time_elapsed = df_roll.starttime.iloc[-1] - df_roll.starttime.iloc[0]  # get the time elapsed over the trials 
                reward_rate_on_this_lap= correct / time_elapsed          # calculate the reward rate

            reward_rate[c]=reward_rate_on_this_lap                       # store the rolling average
            c+=1;trial_number+=1                                         # increment some dumb counters
    df['reward_rate'] = reward_rate * 60.                                # convert to rewards/min



def flatten_array(in_array):
    out_array = np.array([])
    for entry in in_array:
        if len(entry)>0:
            out_array = np.hstack((out_array,entry))
    return out_array

def flatten_list(in_list):
    out_list = []
    for i in range(len(in_list)):
        #check to see if each entry is a list or array
        if isinstance(in_list[i],list) or isinstance(in_list[i],np.ndarray):
            # if so, iterate over each value and append to out_list
            for entry in in_list[i]:
                out_list.append(entry)
        else:
            #otherwise, append the value itself
            out_list.append(in_list[i])

    return out_list


# -> analyze
def calculate_latency(df_in):
    # For each trial, calculate the difference between each stimulus change and the next lick (response lick)
    for idx in df_in.index:
        if pd.isnull(df_in['change_time'][idx])==False and len(df_in['lick_times'][idx])>0:
            licks = np.array(df_in['lick_times'][idx])

            post_stimulus_licks= licks-df_in['change_time'][idx]

            post_window_licks = post_stimulus_licks[post_stimulus_licks>df_in.loc[idx]['response_window'][0]]

            if len(post_window_licks)>0:
                df_in.loc[idx,'response_latency'] = post_window_licks[0]


    return df_in

# -> analyze
def calculate_trial_length(df_in):
    trial_length = np.zeros(len(df_in))
    for ii,idx in enumerate(df_in.index):
        try:
            tl = df_in.loc[idx+1].starttime - df_in.loc[idx].starttime
            if tl < 0 or tl > 1000:
                tl = np.nan
            trial_length[ii]= tl
        except:
            pass

    return trial_length

# -> analyze
def get_end_frame(df_in,last_frame=None):


    end_frames = np.zeros_like(df_in.index)*np.nan

    for ii,index in enumerate(df_in.index[:-1]):
        end_frames[ii] = int(df_in.loc[index+1].startframe-1)
    if last_frame is not None:
        end_frames[-1] = int(last_frame)

    return end_frames.astype(np.int32)
    

# -> analyze
def categorize_one_trial(row):

    if pd.isnull(row['change_time']):
        if (len(row['lick_times'])>0):
            trial_type = 'aborted'
        else:
            trial_type = 'other'
    else:
        if (row['rewarded'] == True):
            return 'go'

        elif (row['rewarded'] == 0):
            return 'catch'

        elif (row['auto_rewarded'] == True):
            return 'autorewarded'

        else:
            return 'other'

    return trial_type

def categorize_trials(df_in):
    '''trial types:
         'aborted' = lick before stimulus
         'autorewarded' = reward autodelivered at time of stimulus
         'go' = stimulus delivered, rewarded if lick emitted within 1 second
         'catch' = no stimulus delivered
         'other' = uncategorized (shouldn't be any of these, but this allows me to find trials that don't meet this conditions)

         adds a column called 'trial_type' to the input dataframe
         '''
    return df_in.apply(categorize_one_trial,axis=1)


# -> analyze
def get_training_day(df_in):
    '''adds a column to the dataframe with the number of unique training days up to that point
         '''

    training_day_lookup = {}
    for key, group in df_in.groupby(['mouse_id',]):
        dates = np.sort(group['date'].unique())
        training_day_lookup[key] = {date:training_day for training_day,date in enumerate(dates)}
    return df_in.apply(lambda row: training_day_lookup[row['mouse_id']][row['date']],axis=1)


# -> analyze
def get_response_type(df_in):

    response_type = []
    for idx in df_in.index:
        if (df_in.loc[idx].rewarded == True) & (df_in.loc[idx].response == 1):
            response_type.append('HIT')
        elif (df_in.loc[idx].rewarded == True) & (df_in.loc[idx].response != 1):
            response_type.append('MISS')
        elif (df_in.loc[idx].rewarded == False) & (df_in.loc[idx].response == 1):
            response_type.append('FA')
        elif (df_in.loc[idx].rewarded == False) & (df_in.loc[idx].response != 1):
            response_type.append('CR')
        else:
            response_type.append('other')

    return response_type

# -> analyze
def assign_color(df_in):

    color = [None]*len(df_in)
    for idx in df_in.index:

        if df_in.loc[idx]['trial_type'] == 'aborted':
            # color[idx] = 'lightgray'
            color[idx] = 'red'

        elif df_in.loc[idx]['auto_rewarded'] == True:
            # color[idx]='darkblue'
            color[idx]='blue'

        elif df_in.loc[idx]['trial_type'] == 'go':
            if df_in.loc[idx]['response'] == 1:
                # color[idx]='#55a868'
                color[idx] = 'darkgreen'

            elif df_in.loc[idx]['response'] != 1:
                # color[idx]='#ccb974'
                color[idx] = 'lightgreen'

        elif df_in.loc[idx]['trial_type'] == 'catch':
            if df_in.loc[idx]['response'] == 1:
                # color[idx]='#c44e52'
                color[idx] = 'darkorange'

            elif df_in.loc[idx]['response'] != 1:
                # color[idx]='#4c72b0'
                color[idx] = 'yellow'

    return color


# -> analyze
def check_responses(df_in,reward_window=None):
    '''trial types:
         'aborted' = lick before stimulus
         'autorewarded' = reward autodelivered at time of stimulus
         'go' = stimulus delivered, rewarded if lick emitted within 1 second
         'catch' = no stimulus delivered
         'other' = uncategorized (shouldn't be any of these, but this allows me to find trials that don't meet this conditions)

         adds a column called 'response' to the input dataframe
         '''

    if reward_window is not None:
        rw_low = reward_window[0]
        rw_high = reward_window[1]

    did_respond = np.zeros(len(df_in))
    for ii,idx in enumerate(df_in.index):
        if reward_window == None:
            rw_low = df_in.iloc[idx]['response_window'][0]
            rw_high = df_in.iloc[idx]['response_window'][1]
        if pd.isnull(df_in.loc[idx]['change_time']) == False and \
        pd.isnull(df_in.loc[idx]['response_latency']) == False and \
        df_in.loc[idx]['response_latency'] >= rw_low and \
        df_in.loc[idx]['response_latency'] <= rw_high:

                did_respond[ii] = True

    return did_respond

# -> analyze
def get_reward_window(df_in):
    try:
        reward_window = df_in.iloc[0].response_window
    except:
        reward_window = [0.15,1]
    return reward_window


# -> analyze
def get_licktimes(df,reference="change"):
    if reference == 'start':
        licktimes = []
        for idx in df.index:
            licktimes.append(df.loc[idx].lick_times - df.loc[idx].starttime)
    elif reference == 'change':
        licktimes = []
        for idx in df.index:
            licktimes.append(df.loc[idx].lick_times - df.loc[idx].change_time)

    return licktimes


def dprime(hit_rate,fa_rate,limits = (0.01,0.99)):
    from scipy.stats import norm
    Z = norm.ppf

    # Limit values in order to avoid d' infinity
    hit_rate = np.clip(hit_rate,limits[0],limits[1])
    fa_rate = np.clip(fa_rate,limits[0],limits[1])

    return Z(hit_rate) - Z(fa_rate)



# -> analyze
def get_response_rates(df_in2,sliding_window=100,reward_window=None):

    df_in = df_in2.copy()
    df_in.reset_index(inplace=True)

    go_responses = pd.Series([np.nan]*len(df_in))
    go_responses[df_in[(df_in.trial_type=='go')&(df_in.response==1)].index] = 1
    go_responses[df_in[(df_in.trial_type=='go')&((df_in.response==0)|np.isnan(df_in.response))].index] = 0
    hit_rate = go_responses.rolling(window=100,min_periods=0).mean()

    catch_responses = pd.Series([np.nan]*len(df_in))
    catch_responses[df_in[(df_in.trial_type=='catch')&(df_in.response==1)].index] = 1
    catch_responses[df_in[(df_in.trial_type=='catch')&((df_in.response==0)|np.isnan(df_in.response))].index] = 0
    catch_rate = catch_responses.rolling(window=100,min_periods=0).mean()

    d_prime = dprime(hit_rate,catch_rate)

    return hit_rate.values,catch_rate.values,d_prime



def make_response_df(df_in,parameter='delta_ori',additional_columns=None,response_window=None,pool_opposite_signs=True):
    '''
    Pools all values in the input dataframe sharing the value specified in 'parameter'
    Returns a dataframe summarizing performance across the desired parameter

    "additional columns" can be dictionary containing key/value pairs for additional columns desired in the output dictionary
    '''
    from statsmodels.stats.proportion import proportion_confint

    if response_window is None:
        response_window = df_in.iloc[0].response_window
    if pool_opposite_signs==True:
        xvals = np.abs(df_in[parameter]).unique()
    else:
        xvals = df_in[parameter].unique()

    response_dict_list = []
    for X in np.sort(xvals):
        response_dict = {}
        response_dict[parameter] = X

        if pool_opposite_signs==True:
            response_dict['attempts'] = len(df_in[(np.abs(df_in[parameter])==X)])
#         successes = df_in[(df_in[parameter]==X)].response.sum()
            response_dict['successes'] = len(df_in[(np.abs(df_in[parameter])==X)&
                                                   (df_in['response_latency']<response_window[1])&
                                                   (df_in['response_latency']>response_window[0])])
        else:
            response_dict['attempts'] = len(df_in[(df_in[parameter]==X)])
#         successes = df_in[(df_in[parameter]==X)].response.sum()
            response_dict['successes'] = len(df_in[(df_in[parameter]==X)&
                                                   (df_in['response_latency']<response_window[1])&
                                                   (df_in['response_latency']>response_window[0])])

        response_dict['CI'] = proportion_confint(response_dict['successes'],response_dict['attempts'],alpha=0.05,method='beta')
        response_dict['response_probability'] = float(response_dict['successes'])/float(response_dict['attempts'])

        # add a column containing d_prime
        # treat the FAs different than the HITS
        if X == 0:
            response_dict['dprime'] = np.nan
            FA_rate = response_dict['response_probability']
        else:
            response_dict['dprime'] = dprime(response_dict['response_probability'],FA_rate)

        if additional_columns is not None:
            response_dict = dict(response_dict.items() + additional_columns.items())

        response_dict_list.append(response_dict)

    return pd.DataFrame(response_dict_list)


def gsheet_to_dataframe(input_url):
    """
    Modifies the URL of a google spreadsheet to make it into a downloadable CSV that is readable by Pandas
    Requires the full URL, starting with https://

    IMPORTANT: The URL must be retrieved by clicking on 'Share', the 'Get shareable link'
               Simply copying the URL directly from the browser will result in error
    """

    modified_url = input_url.split('edit')[0] + 'export?gid=0&format=csv'
    return pd.read_csv(modified_url)


def ProgressBar_Test(iterations):
    pbar = Progress_Bar_Text(iterations)
    for i in range(iterations):
        pbar.update()

def pbar(iterations,display_count=False,message=''):
    '''
    tries to return html widet based progress bar, returns text-based progress bar on failure
    '''
    try:
        return Progress_Bar_Widget(iterations,display_count=False,message='')
    except:
        return Progress_Bar_Text(iterations,display_count=False,message='')

def progress(iterations,display_count=False,message=''):
    return Progress_Bar_Widget(iterations,display_count=False,message='')

def ProgressBar(iterations,display_count=False,message=''):
    return Progress_Bar_Text(iterations,display_count=False,message='')


class Progress_Bar_Widget(object):
    '''
    Progress bar for jupyter notebook
    DRO - 6/13/16
    mashup of code from: https://github.com/ipython/ipywidgets/issues/624 
                                    &
                         https://github.com/alexanderkuk/log-progress/blob/master/test.ipynb
    '''
    def __init__(self,iterations,display_count=False,message=''):
        from ipywidgets import IntProgress,HTML, VBox
        from IPython.display import display

        self.display = display
        self.display_count = display_count
        self.message = message
        # self.iterations = iterations
        self.progress = IntProgress(min=0, max=iterations, description=self.message)
        # self.progress.bar_style = 'info'



        self.label = HTML()
        self.box = VBox(children=[self.label, self.progress])

        self.initialize(iterations=iterations)

        self.display(self.box)
        # self.count = 0

    def change_message(self,message):
        self.message = message
        self.progress.description = self.message

    def update(self,message=None,step=1,force_count=None):
        if message is not None:
            self.message = message
        if force_count is None:
            self.count += step
        else:
            self.count = int(force_count)
        self.progress.value = self.count
        self.progress.description = self.message + " "+ str(round(100.0*self.count/self.iterations))+"%"
        if self.display_count:
            self.label.value = u'{index} / {total}'.format(index=self.count,total=self.iterations)

        if self.count >= self.iterations:
            self.progress.bar_style = 'success'

    def initialize(self,iterations=None):
        if iterations is not None:
            self.iterations = iterations
        self.count = 0
        self.progress.max = iterations
        self.progress.value = self.count
        self.progress.bar_style = 'info'
        self.progress.description = self.message + " "+"0%"
        

class Progress_Bar_Text(object):
    """
    Shamelessly stolen, with slight modification, from: https://gist.github.com/minrk/2211026
    """
    
    def __init__(self, iterations,display_count=False,message=""):



        self.iterations = iterations
        self.message = message
        self.prog_bar = '[]'
        self.fill_char = '*'
        self.width = 40
        self.__update_amount(0)
        # if self.have_ipython:
        self.animate = self.animate_ipython
        self.count = 0
        self.animate(self.count)
        self.endstop = False
        # else:
        #     self.animate = self.animate_noipython

    def update(self,message=None):
        self.count += 1
        self.animate(self.count)
        if message is not None:
            self.message = message
        # if self.count >= self.iterations and self.endstop is False:
        #     print ""
        #     self.endstop = True #prevent this progress bar from being overwritting by the next print statement


    def animate_ipython(self, iter):
        try:
            clear_output()
        except Exception:
            # terminal IPython has no clear_output
            pass
        print '\r', self,
        sys.stdout.flush()
        self.update_iteration(iter + 1)

    def update_iteration(self, elapsed_iter):
        self.__update_amount((elapsed_iter / float(self.iterations)) * 100.0)
        self.prog_bar += '  %d of %s complete' % (elapsed_iter, self.iterations)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = self.message+' [' + self.fill_char * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) / 2) - len(str(percent_done)) + (len(self.message)+2)/2
        pct_string = '%d%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def __str__(self):
        return str(self.prog_bar)


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
    def check(self,arr):
        if arr.all():
            self.firstall = True
        return self.firstall