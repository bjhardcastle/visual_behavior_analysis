import numpy as np
import pandas as pd
from six import iteritems
import logging


logger = logging.getLogger(__name__)


def get_visual_stimuli(stimuli, time):
    n_frames = len(time)

    data = []
    for stimuli_group_name, stim_dict in iteritems(stimuli):

        for idx, (attr_name, attr_value, _time, frame, ) in \
                enumerate(stim_dict["set_log"]):
            orientation = attr_value if attr_name.lower() == "ori" else np.nan
            image_name = attr_value if attr_name.lower() == "image" else np.nan

            if attr_name.lower() == "image" and stim_dict["change_log"]:
                image_category = _resolve_image_category(
                    stim_dict["change_log"],
                    frame
                )
            else:
                image_category = np.nan

            stimulus_epoch = _get_stimulus_epoch(
                stim_dict["set_log"],
                idx,
                frame,
                n_frames,
            )
            draw_epochs = _get_draw_epochs(
                stim_dict["draw_log"],
                *stimulus_epoch
            )

            for idx, (epoch_start, epoch_end, ) in enumerate(draw_epochs):

                # visual stimulus doesn't actually change until start of
                # following frame, so we need to bump the epoch_start & epoch_end
                # to get the timing right
                epoch_start += 1
                epoch_end += 1

                data.append({
                    "orientation": orientation,
                    "image_name": image_name,
                    "image_category": image_category,
                    "frame": epoch_start,
                    "end_frame": epoch_end,
                    "time": time[epoch_start],
                    "duration": time[epoch_end] - time[epoch_start],  # this will always work because an epoch will never occur near the end of time
                })

    return data


def check_for_omitted_flashes(stimulus_df, time, omitted_flash_frame_log=None, periodic_flash=None, threshold=2):
    '''
    fills in stimulus_df with rows for omitted flashes
    if omitted_flash_frame_log is None, looks for blank_durations exceeding threshold*(expected blank duration)
    '''
    if periodic_flash is None:
        # there cannot be omitted flashes if the stimulus isn't flashing
        return pd.DataFrame(columns=['frame','time'])
    else:
        flash_duration,blank_duration = periodic_flash

        omitted_flash_list = []
        if omitted_flash_frame_log is None:
            #if there was no omitted flash frame log, infer omitted flashes
            #iterate over all rows with a preceding blank duration greater than threshold

            stimulus_df['preceding_blank_duration'] = stimulus_df['time'].diff() - stimulus_df['duration']

            for idx,row in stimulus_df[stimulus_df['preceding_blank_duration'] > threshold * blank_duration].iterrows():

                consecutive_previous_omitted_flashes = int((row['preceding_blank_duration'] - blank_duration) / (flash_duration + blank_duration))

                for inferred_omitted_flash_number in range(consecutive_previous_omitted_flashes):
                    inferred_blank_time = (1 + inferred_omitted_flash_number) * (flash_duration + blank_duration)
                    inferred_omitted_flash_time = row['time'] - inferred_blank_time
                    inferred_omitted_flash_frame = np.argmin(abs(inferred_omitted_flash_time - time))

                    omitted_flash_list.append({
                        'frame':inferred_omitted_flash_frame,
                        'time':inferred_omitted_flash_time,
                    })
                    
        elif omitted_flash_frame_log is not None:
            for stimuli_group_name, omitted_flash_frames in iteritems(omitted_flash_frame_log):
                omitted_flash_times = [time[frame] for frame in omitted_flash_frames]
                for omitted_flash_frame,omitted_flash_time in zip(omitted_flash_frames,omitted_flash_times):

                    omitted_flash_list.append({
                        'frame':omitted_flash_frame,
                        'time':omitted_flash_time,
                    })

    return pd.DataFrame(omitted_flash_list)


def unpack_change_log(change):

    (from_category, from_name), (to_category, to_name, ), time, frame = change

    return dict(
        frame=frame,
        time=time,
        from_category=from_category,
        to_category=to_category,
        from_name=from_name,
        to_name=to_name,
    )


def _resolve_image_category(change_log, frame):

    for change in (unpack_change_log(c) for c in change_log):
        if frame < change['frame']:
            return change['from_category']

    return change['to_category']


def _get_stimulus_epoch(set_log, current_set_index, start_frame, n_frames):
    try:
        next_set_event = set_log[current_set_index + 1]  # attr_name, attr_value, time, frame
    except IndexError:  # assume this is the last set event
        next_set_event = (None, None, None, n_frames, )

    return (start_frame, next_set_event[3])  # end frame isnt inclusive


def _get_draw_epochs(draw_log, start_frame, stop_frame):
    """start_frame inclusive, stop_frame non-inclusive
    """
    draw_epochs = []
    current_frame = start_frame

    while current_frame <= stop_frame:
        epoch_length = 0
        while current_frame < stop_frame and draw_log[current_frame] == 1:
            epoch_length += 1
            current_frame += 1
        else:
            current_frame += 1

        if epoch_length:
            draw_epochs.append(
                (current_frame - epoch_length - 1, current_frame - 1, )
            )

    return draw_epochs
