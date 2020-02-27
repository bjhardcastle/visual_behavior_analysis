import os
import seaborn as sns
import matplotlib.pyplot as plt
import visual_behavior.database as db
import visual_behavior.plotting as vbp

from visual_behavior.visualization import utils as ut
from visual_behavior.visualization.qc import data_loading as dl
from visual_behavior.visualization.qc import data_processing as dp
from visual_behavior.visualization.qc import experiment_plots as ep
from visual_behavior.visualization.qc import session_plots as sp


################  OPHYS  ################ # NOQA: E402

def plot_max_projection_images_for_container(ophys_container_id, save_figure=True):
    ophys_experiment_ids = dl.get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 5)
    fig, ax = plt.subplots(1, 6, figsize=figsize)
    for i, ophys_experiment_id in enumerate(ophys_experiment_ids):
        ax[i] = ep.plot_max_intensity_projection_for_experiment(ophys_experiment_id, ax=ax[i])
        session_type = dl.get_session_type_for_ophys_experiment_id(ophys_experiment_id)
        ax[i].set_title(str(ophys_experiment_id) + '\n' + session_type)

    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'max_intensity_projection',
                       'container_' + str(ophys_container_id))


def plot_eye_tracking_sample_frames(ophys_container_id, save_figure=True):
    table = dl.get_filtered_ophys_experiment_table()
    ophys_experiment_ids = table.query('container_id == {}'.format(ophys_container_id)).sort_values(by='date_of_acquisition')['ophys_experiment_id']

    fig = plt.figure(figsize=(16, 5 * len(ophys_experiment_ids)))
    axes = []
    nplots = len(ophys_experiment_ids)
    buffer = 0.05
    for ii, ophys_experiment_id in enumerate(ophys_experiment_ids):
        print('on ophys_experiment_id {}, #{} of {}'.format(ophys_experiment_id, ii + 1, nplots))
        axes.append(vbp.placeAxesOnGrid(fig, dim=(3, 10), xspan=(0, 1), yspan=(ii / nplots + buffer, (ii + 1) / nplots)))
        axes[-1] = ep.make_eye_matrix_plot(ophys_experiment_id, axes[-1])

    savepath = os.path.join(dl.get_container_plots_dir(), 'eyetracking_sample_frames', 'container_{}.png'.format(ophys_container_id))
    fig.savefig(savepath, dpi=300, pad_inches=0.0, bbox_inches='tight')

    return fig, axes


def plot_average_images_for_container(ophys_container_id, save_figure=True):
    ophys_experiment_ids = dl.get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 5)
    fig, ax = plt.subplots(1, 6, figsize=figsize)
    for i, ophys_experiment_id in enumerate(ophys_experiment_ids):
        ax[i] = ep.plot_average_image_for_experiment(ophys_experiment_id, ax=ax[i])
        session_type = dl.get_session_type_for_ophys_experiment_id(ophys_experiment_id)
        ax[i].set_title(str(ophys_experiment_id) + '\n' + session_type)

    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'average_images',
                       'container_' + str(ophys_container_id))


def plot_segmentation_masks_for_container(ophys_container_id, save_figure=True):
    ophys_experiment_ids = dl.get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 5)
    fig, ax = plt.subplots(1, 6, figsize=figsize)
    for i, ophys_experiment_id in enumerate(ophys_experiment_ids):
        ax[i] = ep.plot_segmentation_mask_for_experiment(ophys_experiment_id, ax=ax[i])
        session_type = dl.get_session_type_for_ophys_experiment_id(ophys_experiment_id)
        ax[i].set_title(str(ophys_experiment_id) + '\n' + session_type)

    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'segmentation_masks',
                       'container_' + str(ophys_container_id))


def plot_segmentation_mask_overlays_for_container(ophys_container_id, save_figure=True):
    ophys_experiment_ids = dl.get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 5)
    fig, ax = plt.subplots(1, 6, figsize=figsize)
    for i, ophys_experiment_id in enumerate(ophys_experiment_ids):
        ax[i] = ep.plot_segmentation_mask_overlay_for_experiment(ophys_experiment_id, ax=ax[i])
        session_type = dl.get_session_type_for_ophys_experiment_id(ophys_experiment_id)
        ax[i].set_title(str(ophys_experiment_id) + '\n' + session_type)

    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'segmentation_mask_overlays',
                       'container_' + str(ophys_container_id))


def plot_dff_traces_heatmaps_for_container(ophys_container_id, save_figure=True):
    ophys_experiment_ids = dl.get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 20)
    fig, ax = plt.subplots(6, 1, figsize=figsize)
    for i, ophys_experiment_id in enumerate(ophys_experiment_ids):
        ax[i] = ep.plot_traces_heatmap_for_experiment(ophys_experiment_id, ax=ax[i])
        session_type = dl.get_session_type_for_ophys_experiment_id(ophys_experiment_id)
        ax[i].set_title(str(ophys_experiment_id) + ' - ' + session_type)

    fig.tight_layout()
    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'dff_traces_heatmaps',
                       'container_' + str(ophys_container_id))

# def plot_average_intensity_timeseries_for_container(ophys_container_id, save_figure=True):
#     container_df = (dp.ophys_container_passed_experiments(ophys_container_id)).sort_values('stage_name_lims').reset_index(drop=True)
#     colors = sns.color_palette()
#     figsize = (7, 5)
#     fig, ax = plt.subplots(figsize=figsize)
#     for i, ophys_experiment_id in enumerate(container_df["ophys_experiment_id"].unique()):
#         ax = ep.plot_average_intensity_timeseries_for_experiment(ophys_experiment_id, ax=ax, color=colors[i])
#     ax.legend(fontsize='xx-small', title='experiment_id', title_fontsize='xx-small', loc='upper left')
#     ax.set_title('full field average fluorescence intensity over time')
#     fig.tight_layout()
#     if save_figure:
#         ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'average_intensity_timeseries',
#                        'container_' + str(ophys_container_id))


def plot_average_intensity_timeseries_for_container(ophys_container_id, save_figure=True):
    container_df = (dp.ophys_container_passed_experiments(ophys_container_id)).sort_values('stage_name_lims').reset_index(drop=True)
    figsize = (9, 5)
    fig, ax = plt.subplots(figsize=figsize)
    for i, ophys_experiment_id in enumerate(container_df["ophys_experiment_id"].unique()):
        ax = ep.plot_average_intensity_timeseries_for_experiment(ophys_experiment_id, ax=ax)
    ax.legend(fontsize='xx-small', title='stage name', title_fontsize='xx-small',
              bbox_to_anchor=(1.01, 1), loc=2)
    ax.set_title('full field average fluorescence intensity over time')
    fig.tight_layout()
    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'average_intensity_timeseries',
                       'container_' + str(ophys_container_id))


def plot_number_matched_cells_for_container(ophys_container_id, save_figure=True):
    df = dp.container_cell_matching_count_heatmap_df(ophys_container_id)

    matrix = df.values
    labels = df.index

    figsize = (10, 10)
    fig, ax = plt.subplots(figsize=figsize)
    ax = sns.heatmap(matrix, square=True, cmap='magma', ax=ax, cbar_kws={'shrink': 0.7, 'label': '# matched cells'},
                     annot=True, fmt='.3g')
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom + 0.5, top - 0.5)
    ax.set_xticklabels(labels, rotation=90)
    ax.set_yticklabels(labels, rotation=0)
    ax.set_title('number of matched cells across sessions')
    fig.tight_layout()
    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'number_matched_cells',
                       'container_' + str(ophys_container_id))


def plot_fraction_matched_cells_for_container(ophys_container_id, save_figure=True):
    df = dp.container_cell_matching_percent_heatmap_df(ophys_container_id)

    matrix = df.values
    labels = df.index

    figsize = (10, 10)
    fig, ax = plt.subplots(figsize=figsize)
    ax = sns.heatmap(matrix, square=True, cmap='magma', ax=ax, cbar_kws={'shrink': 0.7, 'label': '% matched cells'},
                     annot=True, vmin=0, vmax=1, fmt='.3g')
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom + 0.5, top - 0.5)
    ax.set_xticklabels(labels, rotation=90)
    ax.set_yticklabels(labels, rotation=0)
    ax.set_title('fraction matched cells across sessions')
    fig.tight_layout()
    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'fraction_matched_cells',
                       'container_' + str(ophys_container_id))


def plot_motion_correction_xy_shift_for_container(ophys_container_id, save_figure=True):
    ophys_experiment_ids = dl.get_ophys_experiment_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 20)
    fig, ax = plt.subplots(6, 1, figsize=figsize)
    for i, ophys_experiment_id in enumerate(ophys_experiment_ids):
        ax[i] = ep.plot_motion_correction_xy_shift_for_experiment(ophys_experiment_id, ax=ax[i])

        session_type = dl.get_session_type_for_ophys_experiment_id(ophys_experiment_id)
        ax[i].set_title(str(ophys_experiment_id) + '\n' + session_type)
    fig.tight_layout()
    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'motion_correction_xy_shift',
                       'container_' + str(ophys_container_id))


def plot_PMT_gain_for_container(ophys_container_id, save_figure=True):
    import numpy as np
    ophys_session_ids = dl.get_ophys_session_ids_for_ophys_container_id(ophys_container_id)
    figsize = (6, 5)
    fig, ax = plt.subplots(figsize=figsize)
    for i, ophys_session_id in enumerate(ophys_session_ids):
        pmt_value = dl.get_pmt_gain_for_session(ophys_session_id)
        ax.plot(i, pmt_value, 'o', color=sns.color_palette()[0])
    ax.set_xticks(np.arange(0, len(ophys_session_ids)))
    ax.set_xticklabels(ophys_session_ids, rotation=90)
    ax.set_ylabel('PMT setting')
    ax.set_xlabel('ophys_session_id')
    ax.set_title('PMT gain setting across sessions')
    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'PMT_gain',
                       'container_' + str(ophys_container_id))


################  BEHAVIOR  ################ # NOQA: E402

def plot_running_speed_for_container(ophys_container_id, save_figure=True):
    ophys_session_ids = dl.get_ophys_session_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 15)
    fig, ax = plt.subplots(6, 1, figsize=figsize)
    for i, ophys_session_id in enumerate(ophys_session_ids):
        ax[i] = sp.plot_running_speed(ophys_session_id, ax=ax[i])
        session_type = dl.get_session_type_for_ophys_session_id(ophys_session_id)
        ax[i].set_title(str(ophys_session_id) + '\n' + session_type)
    fig.tight_layout()
    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'running_speed',
                       'container_' + str(ophys_container_id))


def plot_lick_rasters_for_container(ophys_container_id, save_figure=True):
    ophys_session_ids = dl.get_ophys_session_ids_for_ophys_container_id(ophys_container_id)

    figsize = (25, 7)
    fig, ax = plt.subplots(1, 6, figsize=figsize)
    for i, ophys_session_id in enumerate(ophys_session_ids):
        ax[i] = sp.plot_lick_raster(ophys_session_id, ax=ax[i])
        ax[i].invert_yaxis()
        session_type = dl.get_session_type_for_ophys_session_id(ophys_session_id)
        ax[i].set_title(str(ophys_session_id) + '\n' + session_type)
    # plt.gca().invert_yaxis()

    if save_figure:
        ut.save_figure(fig, figsize, dl.get_container_plots_dir(), 'lick_rasters',
                       'container_' + str(ophys_container_id))
