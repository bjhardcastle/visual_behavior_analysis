from allensdk.brain_observatory.behavior.behavior_ophys_session import BehaviorOphysSession
from allensdk.brain_observatory.behavior.behavior_project_cache import BehaviorProjectCache as bpc
from allensdk.internal.api.behavior_ophys_api import BehaviorOphysLimsApi
from visual_behavior.translator.allensdk_sessions import sdk_utils
import visual_behavior.ophys.io.convert_level_1_to_level_2 as convert


from allensdk.internal.api import PostgresQueryMixin
import configparser as configp  # for parsing scientifica ini files

import os
import pandas as pd
import numpy as np

get_psql_dict_cursor = convert.get_psql_dict_cursor #to load well-known files
config = configp.ConfigParser()

####function inputs
# ophys_experiment_id
# ophys_session_id
# behavior_session_id
# ophys_container_id


################  GENERAL STUFF  ################ # NOQA: E402

def get_container_plots_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/qc_plots/container_plots'

def get_session_plots_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/qc_plots/session_plots'

def get_experiment_plots_dir():
    return '//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/qc_plots/experiment_plots'


################  FROM MANIFEST  ################ # NOQA: E402

def get_qc_manifest_path():
    """Get path to default manifest file for QC"""
    manifest_path = "//allen/programs/braintv/workgroups/nc-ophys/visual_behavior/2020_cache/qc_cache/manifest.json"
    return manifest_path

def get_qc_cache():
    """Get cache using default QC manifest path"""
    from allensdk.brain_observatory.behavior.behavior_project_cache import BehaviorProjectCache as bpc
    cache = bpc.from_lims(manifest=get_qc_manifest_path())
    return cache

def get_filtered_ophys_sessions_table():
    """Get ophys sessions that meet the criteria in sdk_utils.get_filtered_sessions_table(), including that the container
    must be 'complete' or 'container_qc', and experiments associated with the session are passing. In addition,
    add container_id and container_workflow_state to table.

        Arguments:
            None

        Returns:
            filtered_sessions -- filtered version of ophys_session_table from QC cache
        """
    cache = get_qc_cache()
    sessions = sdk_utils.get_filtered_sessions_table(cache)
    sessions = sessions.reset_index()
    experiments = cache.get_experiment_table()
    experiments = experiments.reset_index()
    filtered_sessions = sessions.merge(experiments[['ophys_session_id', 'container_id', 'container_workflow_state']],
                              right_on='ophys_session_id', left_on='ophys_session_id')
    return filtered_sessions

def get_filtered_ophys_experiment_table():
    """Get ophys experiments that meet the criteria in sdk_utils.get_filtered_sessions_table(), including that the container
        must be 'complete' or 'container_qc', and experiments are passing

            Arguments:
                None

            Returns:
                filtered_experiments -- filtered version of ophys_experiment_table from QC cache
            """
    cache = get_qc_cache()
    experiments = cache.get_experiment_table()
    experiments = experiments.reset_index()
    sessions = sdk_utils.get_filtered_sessions_table(cache)
    filtered_experiment_ids = [expt_id[0] for expt_id in sessions.ophys_experiment_id.values]
    filtered_experiments = experiments[experiments.ophys_experiment_id.isin(filtered_experiment_ids)]
    return filtered_experiments

def get_filtered_ophys_container_ids():
    """Get container_ids that meet the criteria in sdk_utils.get_filtered_sessions_table(), including that the container
    must be 'complete' or 'container_qc', and experiments associated with the container are passing. """
    sessions = get_filtered_ophys_sessions_table()
    filtered_container_ids = np.sort(sessions.container_id.unique())
    return filtered_container_ids

def get_ophys_session_ids_for_ophys_container_id(ophys_container_id):
    """Get ophys_session_ids belonging to a given ophys_container_id. ophys container must meet the criteria in
    sdk_utils.get_filtered_sessions_table()

            Arguments:
                ophys_container_id -- must be in get_filtered_ophys_container_ids()

            Returns:
                ophys_session_ids -- list of ophys_session_ids that meet filtering criteria
            """
    sessions = get_filtered_ophys_sessions_table()
    ophys_session_ids = np.sort(sessions[(sessions.container_id == ophys_container_id)].ophys_session_id.values)
    return ophys_session_ids

def get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id):
    """Get ophys_experiment_ids belonging to a given ophys_container_id. ophys container must meet the criteria in
        sdk_utils.get_filtered_sessions_table()

                Arguments:
                    ophys_container_id -- must be in get_filtered_ophys_container_ids()

                Returns:
                    ophys_experiment_ids -- list of ophys_experiment_ids that meet filtering criteria
                """
    experiments = get_filtered_ophys_experiment_table()
    ophys_experiment_ids = np.sort(experiments[(experiments.container_id == ophys_container_id)].ophys_experiment_id.values)
    return ophys_experiment_ids


def get_session_type_for_ophys_experiment_id(ophys_experiment_id):
    experiments = get_filtered_ophys_experiment_table()
    session_type = experiments[experiments.ophys_experiment_id==ophys_experiment_id].session_type.values[0]
    return session_type


def get_session_type_for_ophys_session_id(ophys_session_id):
    sessions = get_filtered_ophys_sessions_table()
    session_type = sessions[sessions.ophys_session_id==ophys_session_id].session_type.values[0]
    return session_type


def get_ophys_experiment_id_for_ophys_session_id(ophys_session_id):
    experiments = get_filtered_ophys_experiment_table()
    ophys_experiment_id = experiments[(experiments.ophys_session_id == ophys_session_id)].ophys_experiment_id.values[0]
    return ophys_experiment_id

################  FROM SDK  ################ # NOQA: E402


def get_sdk_session_obj(ophys_experiment_id):
    """Use LIMS API from SDK to return session object

    Arguments:
        experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        session object -- session object from SDK
    """
    api = BehaviorOphysLimsApi(ophys_experiment_id)
    session = BehaviorOphysSession(api)
    return session


def get_sdk_max_projection(ophys_experiment_id):
    """ uses SDK to return 2d max projection image of the microscope field of view


    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        image -- can be visualized via plt.imshow(max_projection)
    """
    session = get_sdk_session_obj(ophys_experiment_id)
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
    session = get_sdk_session_obj(ophys_experiment_id)
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
    session = get_sdk_session_obj(ophys_experiment_id)
    seg_mask_image = session.segmentation_mask_image.data
    return seg_mask_image


def get_sdk_roi_masks(ophys_experiment_id):
    """uses sdk to return a dictionary with individual ROI masks for each cell specimen ID.

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        dictonary -- keys are cell specimen ids(ints)
                    values are 2d numpy arrays(binary array the size of the motion corrected 2photon FOV where 1's are the ROI/Cell mask).
                    specific cell masks can be visualized via plt.imshow(roi_masks[cell_specimen_id])
    """

    session = get_sdk_session_obj(ophys_experiment_id)
    roi_masks = session.get_roi_masks
    return roi_masks


def get_valid_segmentation_mask(ophys_experiment_id):
    session = get_sdk_session_obj(ophys_experiment_id)
    ct = session.cell_specimen_table
    valid_cell_specimen_ids = ct[ct.valid_roi==True].index.values
    roi_masks = session.get_roi_masks()
    valid_roi_masks = roi_masks[roi_masks.cell_specimen_id.isin(valid_cell_specimen_ids)].data
    valid_segmentation_mask = np.sum(valid_roi_masks, axis=0)
    valid_segmentation_mask[valid_segmentation_mask>0] = 1
    return valid_segmentation_mask


def get_sdk_cell_specimen_table(ophys_experiment_id):
    session = get_sdk_session_obj(ophys_experiment_id)
    cell_specimen_table = session.cell_specimen_table
    return cell_specimen_table


def get_sdk_dff_traces_array(ophys_experiment_id):
    session = get_sdk_session_obj(ophys_experiment_id)
    dff_traces = session.dff_traces
    # remove NaN traces - temporary fix, need to change API to return only valid cells
    bad_cell_specimen_ids = []
    for i, trace in enumerate(dff_traces.dff.values):
        if np.isnan(trace).any():
            bad_cell_specimen_ids.append(dff_traces.index[i])
    dff_traces = dff_traces[dff_traces.index.isin(bad_cell_specimen_ids) == False]
    dff_traces_array = np.vstack(dff_traces.dff.values)
    return dff_traces_array

def get_sdk_running_speed(ophys_session_id):
    session = get_sdk_session_obj(get_ophys_experiment_id_for_ophys_session_id(ophys_session_id))
    running_speed = session.running_data_df['speed']
    return running_speed

def get_sdk_trials(ophys_session_id):
    session = get_sdk_session_obj(get_ophys_experiment_id_for_ophys_session_id(ophys_session_id))
    trials = session.trials.reset_index()
    return trials


################  FROM LIMS DATABASE  ################ # NOQA: E402




####### EXPERIMENT LEVEL ####### # NOQA: E402


def get_lims_experiment_info(ophys_experiment_id):
    """uses an sqlite query to retrieve ophys experiment information
        from the lims2 database

    Arguments:
        ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        table -- table with the following columns:
                    "experiment_id":
                    "experiment_workflow_state":
                    "ophys_session_id":
                    "container_id":
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
    mixin = PostgresQueryMixin()
    # build query
    query = '''
    select

    oe.id as experiment_id,
    oe.workflow_state,
    oe.ophys_session_id,

    container.visual_behavior_experiment_container_id as container_id,

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
    """Queries LIMS via AllenSDK PostgresQuery function to retrieve information on all segmentations run in the
        ophys_cell_segmenatation_runs table for a given experiment

    Arguments:
         ophys_experiment_id {int} -- 9 digit ophys experiment ID

    Returns:
        dataframe --  dataframe with the following columns:
                        id {int}:  9 digit segmentation run id
                        run_number {int}: segmentation run number
                        ophys_experiment_id{int}: 9 digit ophys experiment id
                        current{boolean}: True/False True: most current segmentation run; False: not the most current segmentation run
                        created_at{timestamp}:
                        updated_at{timestamp}:
    """

    mixin = PostgresQueryMixin()
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

    mixin = PostgresQueryMixin()
    query = '''select cell_rois.*

    from

    ophys_experiments oe
    join cell_rois on oe.id = cell_rois.ophys_experiment_id

    where oe.id = {}'''.format(ophys_experiment_id)
    lims_cell_rois_table = mixin.select(query)
    return lims_cell_rois_table



####### CONTAINER  LEVEL ####### # NOQA: E402


def get_lims_container_info(ophys_container_id):
    """"uses an sqlite query to retrieve container level information
        from the lims2 database. Each row is an experiment within the container.

    Arguments:
        container_id {[type]} -- [description]

    Returns:
       table -- table with the following columns:
                    "container_id":
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

    mixin = PostgresQueryMixin()
    # build query
    query = '''
    SELECT
    container.visual_behavior_experiment_container_id as container_id,
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




################  FROM LIMS WELL KNOWN FILES  ################ # NOQA: E402


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

    lims_cursor = get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    timeseries_ini_wkf_info = (lims_cursor.fetchall())
    return timeseries_ini_wkf_info


def get_timeseries_ini_location(ophys_session_id):
    """use SQL and the LIMS well known file system to get info for the timeseries_XYT.ini file
        for a given ophys session, and then parses that information to get the filepath

    Arguments:
        ophys_session_id {int} -- 9 digit ophys session id

    Returns:
        filepath -- [description]
    """
    timeseries_ini_wkf_info = get_timeseries_ini_wkf_info(ophys_session_id)
    timeseries_ini_path = timeseries_ini_wkf_info[0]['?column?'] #idk why it's ?column? but it is :(
    timeseries_ini_path = timeseries_ini_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return timeseries_ini_path


def pmt_gain_from_timeseries_ini(timeseries_ini_path):
    """parses the timeseries ini file and extracts the pmt gain setting

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
    timeseries_ini_path = get_timeseries_ini_location(ophys_session_id)
    pmt_gain = pmt_gain_from_timeseries_ini(timeseries_ini_path)
    return pmt_gain


def get_motion_corrected_movie_h5_wkf_info(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get the
        "motion_corrected_movie.h5" information for a given
        ophys_experiment_id

    Arguments:
        ophys_experiment_id {[type]} -- [description]

    Returns:
        [type] -- [description]
    """

    QUERY = '''
     SELECT storage_directory || filename
     FROM well_known_files
     WHERE well_known_file_type_id = 886523092 AND
     attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    motion_corrected_movie_h5_wkf_info = (lims_cursor.fetchall())
    return motion_corrected_movie_h5_wkf_info

def get_motion_corrected_movie_h5_location(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get info for the
        "motion_corrected_movie.h5" file for a ophys_experiment_id,
        and then parses that information to get the filepath

    Arguments:
        ophys_experiment_id {[type]} -- [description]

    Returns:
        filepath -- [description]
    """
    motion_corrected_movie_h5_wkf_info = get_motion_corrected_movie_h5_wkf_info(ophys_experiment_id)
    motion_corrected_movie_h5_path = motion_corrected_movie_h5_wkf_info[0]['?column?'] #idk why it's ?column? but it is :(
    motion_corrected_movie_h5_path = motion_corrected_movie_h5_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return motion_corrected_movie_h5_path


def get_average_intensity(motion_corrected_movie_h5_path):
    import h5py
    f = h5py.File(motion_corrected_movie_h5_path, 'r')
    movie_array = f['data']

    subset = movie_array[::500, 100:400, 50:400]
    average_intensity = np.mean(subset, axis=(1, 2))

    frame_numbers = np.arange(0, movie_array.shape[0])
    frame_numbers = frame_numbers[::500]

    return average_intensity, frame_numbers



def get_rigid_motion_transform_csv_wkf_info(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get the
        "rigid_motion_transform.csv" information for a given
        ophys_experiment_id

    Arguments:
        ophys_experiment_id {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    QUERY = '''
     SELECT storage_directory || filename
     FROM well_known_files
     WHERE well_known_file_type_id = 514167000 AND
     attachable_id = {0}

    '''.format(ophys_experiment_id)

    lims_cursor = get_psql_dict_cursor()
    lims_cursor.execute(QUERY)

    rigid_motion_transform_csv_wkf_info = (lims_cursor.fetchall())
    return rigid_motion_transform_csv_wkf_info


def get_rigid_motion_transform_csv_location(ophys_experiment_id):
    """use SQL and the LIMS well known file system to get info for the
        rigid_motion_transform.csv" file for a ophys_experiment_id,
        and then parses that information to get the filepath

    Arguments:
        ophys_experiment_id {[type]} -- [description]

    Returns:
        filepath -- [description]
    """
    rigid_motion_transform_csv_wkf_info = get_rigid_motion_transform_csv_wkf_info(ophys_experiment_id)
    rigid_motion_transform_csv_path = rigid_motion_transform_csv_wkf_info[0]['?column?'] #idk why it's ?column? but it is :(
    rigid_motion_transform_csv_path = rigid_motion_transform_csv_path.replace('/allen', '//allen')  # works with windows and linux filepaths
    return rigid_motion_transform_csv_path

def load_rigid_motion_transform_csv(ophys_experiment_id):
    """use SQL and the LIMS well known file system to locate
        and load the rigid_motion_transform.csv file for
        a given ophys_experiment_id

    Arguments:
        ophys_experiment_id {[type]} -- [description]

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



################  FROM MTRAIN DATABASE  ################ # NOQA: E402

mtrain_api = PostgresQueryMixin(dbname="mtrain", user="mtrainreader", host="prodmtrain1", password="r0mTr@!n", port=5432)

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
    mtrain_response = pd.read_sql(query, mtrain_api.get_connection())
    dataframe = dataframe.merge(mtrain_response, on='foraging_id', how='left')
    dataframe = dataframe.rename(columns={"stage_name": "stage_name_mtrain"})
    return dataframe












def build_container_df():
    '''
    build dataframe with one row per container
    '''
    manifest_path = "/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/2020_cache/qc_cache/manifest.json"
    cache = bpc.from_lims(manifest=manifest_path)

    table = get_filtered_ophys_experiment_table().sort_values(by='date_of_acquisition', ascending=False).reset_index()
    container_ids = table['container_id'].unique()
    list_of_dicts = []
    for container_id in container_ids:
        subset = table.query('container_id == @container_id').sort_values(by='date_of_acquisition', ascending=True).drop_duplicates('ophys_session_id').reset_index()
        temp_dict = {
            'container_id': container_id,
            'container_workflow_state': table.query('container_id == @container_id')['container_workflow_state'].unique()[0],
            'first_acquistion_date': subset['date_of_acquisition'].min().split(' ')[0],
            'project_code': subset['project_code'].unique()[0],
            'driver_line': subset['driver_line'][0],
            'targeted_structure': subset['targeted_structure'].unique()[0],
            'imaging_depth': subset['imaging_depth'].unique()[0],
            'equipment_name': subset['equipment_name'].unique(),
            'specimen_id': subset['specimen_id'].unique()[0],
            'sex': subset['sex'].unique()[0],
            'age_in_days': subset['age_in_days'].min(),
        }
        for idx,row in subset.iterrows():
            temp_dict.update({'session_{}'.format(idx): '{} {}'.format(row['session_type'], row['ophys_experiment_id'])})
      


        list_of_dicts.append(temp_dict)

    return pd.DataFrame(list_of_dicts).sort_values(by='container_id',ascending=False)
