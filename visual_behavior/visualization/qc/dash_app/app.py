#!/usr/bin/env python

import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import argparse
import numpy as np
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from visual_behavior.data_access import loading

import time
import datetime
import functions
import components
import base64

# APP SETUP
# app = dash.Dash(__name__,)
app = dash.Dash(external_stylesheets=[dbc.themes.SPACELAB])
app.title = 'Visual Behavior Data QC'
# app.config['suppress_callback_exceptions'] = True

# FUNCTION CALLS
print('setting up table')
t0 = time.time()
container_table = functions.load_data().sort_values('first_acquistion_date')
container_plot_options = functions.load_container_plot_options()
container_overview_plot_options = functions.load_container_overview_plot_options()
plot_inventory = functions.generate_plot_inventory()
plot_inventory_fig = functions.make_plot_inventory_heatmap(plot_inventory)
experiment_table = loading.get_filtered_ophys_experiment_table().reset_index()
print('done setting up table, it took {} seconds'.format(time.time()- t0))

QC_ATTRIBUTES = functions.load_container_qc_definitions()

# COMPONENT SETUP
print('setting up components')
t0 = time.time()
components.plot_selection_dropdown.options = container_plot_options
components.container_overview_dropdown.options = container_overview_plot_options
components.container_overview_iframe.src = app.get_asset_url('qc_plots/overview_plots/d_prime_container_overview.html')
components.plot_inventory_iframe.src = 'https://dougollerenshaw.github.io/figures_to_share/container_plot_inventory.html'  # app.get_asset_url('qc_plots/container_plot_inventory.html')
components.container_data_table.columns = [{"name": i.replace('_', ' '), "id": i} for i in container_table.columns]
components.container_data_table.data = container_table.to_dict('records')
print('done setting up components, it took {} seconds'.format(time.time()- t0))

app.layout = html.Video(src='/static/my-video.webm')

server = app.server

@server.route('/static/<path:path>')
def serve_static(path):
    root_dir = os.getcwd()
    return flask.send_from_directory(os.path.join(root_dir, 'static'), path)


# APP LAYOUT
app.layout = html.Div(
    [
        html.H3('Visual Behavior Data QC Viewer'),
        # checklist for components to show
        components.show_overview_checklist,
        components.plot_inventory_graph_div,
        # container level dropdown
        components.container_overview_dropdown,
        # frame with container level plots
        components.container_overview_iframe,
        components.plot_inventory_iframe,
        html.H4('Find container from experiment ID:'),
        html.Label('Enter experiment ID:'),
        dcc.Input(id='experiment_id_entry', placeholder=''),
        html.Label('|  Corresponding Container ID:  '),
        html.Output(id='container_id_output', children=''),
        html.H4('Container Summary Data Table:'),
        html.I('Adjust number of rows to display in the data table:'),
        components.table_row_selection,
        # data table
        components.container_data_table,
        # dropdown for plot selection
        components.previous_button,
        components.next_button,
        html.Div(id='stored_feedback', style={'display': 'none'}),
        html.H4('Links to motion corrected movies for this container'),
        dcc.Link(id='link_0',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_1',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_2',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_3',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_4',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_5',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_6',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_7',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_8',children='', href='', style={'display': True}, target="_blank"),
        html.H4(''),
        dcc.Link(id='link_9',children='', href='', style={'display': True}, target="_blank"),
        components.feedback_button,
        html.H4('Select plots to generate from the dropdown (max 10)'),
        components.plot_selection_dropdown,
        components.plot_titles[0],
        components.plot_frames[0],
        components.plot_titles[1],
        components.plot_frames[1],
        components.plot_titles[2],
        components.plot_frames[2],
        components.plot_titles[3],
        components.plot_frames[3],
        components.plot_titles[4],
        components.plot_frames[4],
        components.plot_titles[5],
        components.plot_frames[5],
        components.plot_titles[6],
        components.plot_frames[6],
        components.plot_titles[7],
        components.plot_frames[7],
        components.plot_titles[8],
        components.plot_frames[8],
        components.plot_titles[9],
        components.plot_frames[9],
        components.plot_titles[10],
        components.plot_frames[10],
        components.plot_titles[11],
        components.plot_frames[11],
        components.plot_titles[12],
        components.plot_frames[12],
        components.plot_titles[13],
        components.plot_frames[13],
        components.plot_titles[14],
        components.plot_frames[14],
        components.plot_titles[15],
        components.plot_frames[15],
        components.plot_titles[16],
        components.plot_frames[16],
        components.plot_titles[17],
        components.plot_frames[17],
        components.plot_titles[18],
        components.plot_frames[18],
        components.plot_titles[19],
        components.plot_frames[19],
    ],
    className='container',
    style={
        # 'padding': '10px',
        'margin-left': '10px',
        'margin-right': '10px',
        'margin-top': '10px',
        'margin-bottom': '10px',
    },
)

# ensure that the table page is set to show the current selection
@app.callback(
    Output("data_table", "page_current"),
    [Input('data_table', 'selected_rows')],
    [
        State('data_table', 'derived_virtual_indices'),
        State('data_table', 'page_current'),
        State('data_table', 'page_size'),
    ]
)
def get_on_correct_page(selected_rows, derived_virtual_indices, page_current, page_size):
    current_selection = selected_rows[0]
    current_index = derived_virtual_indices.index(current_selection)
    current_page = int(current_index/page_size)
    return current_page


@app.callback(
    Output("container_id_output", "children"),
    [Input("experiment_id_entry", "value")],
)
def look_up_container(oeid):
    try:
        res = experiment_table.query('ophys_experiment_id == @oeid')
        if len(res) == 0:
            return 'Not Found'
        else:
            return res.iloc[0]['container_id']
    except ValueError:
        return ''


# go to previous selection in table
@app.callback(
    Output("data_table", "selected_rows"),
    [
        Input("next_button", "n_clicks"),
        Input("previous_button", "n_clicks")
    ],
    [
        State("data_table", "selected_rows"), 
        State('data_table', 'derived_virtual_indices'),
    ]
)
def select_next(next_button_n_clicks, prev_button_n_clicks, selected_rows, derived_virtual_indices):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'previous_button' in changed_id:
        print('previous_button was clicked')
        advance_index = -1
    elif 'next_button' in changed_id:
        print('next_button was clicked')
        advance_index = 1
    else:
        advance_index = 0
    if derived_virtual_indices is not None:
        current_selection = selected_rows[0]
        current_index = derived_virtual_indices.index(current_selection)
        next_index = current_index + advance_index
        if next_index >= 0:
            next_selection = derived_virtual_indices[next_index]
        else:
            next_selection = derived_virtual_indices[current_index]
        return [int(next_selection)]
    else:
        return [0]


# feedback qc data log
@app.callback(
    Output("stored_feedback", "children"),
    [
        Input("feedback_popup_ok", "n_clicks"),
    ],
    [
        State("feedback_popup_datetime", "value"),
        State("feedback_popup_username", "value"),
        State("feedback_popup_container_id", "value"),
        State("feedback_popup_experiments", "value"),
        State("feedback_popup_qc_dropdown", "value"),
        State("feedback_popup_qc_labels", "value"),
        State("feedback_popup_text", "value")
    ]
)
def log_feedback(n1, timestamp, username, container_id, experiment_ids, qc_attribute, qc_labels, input_text):
    print('LOGGING FEEDBACK')
    feedback = {
        'timestamp': timestamp,
        'username': username,
        'container_id': container_id,
        'experiment_ids': experiment_ids,
        'qc_attribute': qc_attribute,
        'qc_labels': qc_labels,
        'input_text': input_text,
    }
    print(feedback)
    functions.log_feedback(feedback)
    functions.set_qc_complete_flags(feedback)
    print('logging feedback at {}'.format(time.time()))
    return 'TEMP'

# toggle popup open/close state
@app.callback(
    Output("plot_qc_popup", "is_open"),
    [
        Input("open_feedback_popup", "n_clicks"), 
        Input("feedback_popup_cancel", "n_clicks"),
        Input("feedback_popup_ok", "n_clicks"),
    ],
    [State("plot_qc_popup", "is_open")],
)
def toggle_modal(n1, n2, n3, is_open):
    print('modal is open? {}'.format(is_open))
    if n1 or n2:
        return not is_open
    return is_open

# fill popup with currently selected container ID
@app.callback(
    Output("feedback_popup_container_id", "value"),
    [
        Input('data_table', 'selected_rows'), 
    ],
)
def fill_container_id(selected_rows):
    idx = selected_rows[0]
    return container_table.iloc[idx]['container_id']

# label radio buttons in popup with currently selected experiment_ids
@app.callback(
    Output('feedback_popup_experiments', 'options'),
    [
        Input('data_table', 'selected_rows'), 
    ],
    [State('feedback_popup_experiments', 'options')]
)
def experiment_id_checklist(row_index, options):
    container_id = container_table.iloc[row_index[0]]['container_id']
    subset = experiment_table.query('container_id == @container_id').sort_values(by='date_of_acquisition')[['session_type','ophys_experiment_id']].reset_index(drop=True)
    options = [{'label': '{} {}'.format(subset.loc[i]['session_type'], subset.loc[i]['ophys_experiment_id']), 'value': subset.loc[i]['ophys_experiment_id']} for i in range(len(subset))]
    return options

# populate feedback popup qc options
@app.callback(
    Output('feedback_popup_qc_labels', 'options'),
    [
        Input('feedback_popup_qc_dropdown', 'value'), 
    ],
)
def populate_qc_options(attribute_to_qc):
    try:
        return [{'label':v, 'value':v} for v in QC_ATTRIBUTES[attribute_to_qc]['qc_attributes']]
    except KeyError:
        return []

# clear popup text
@app.callback(
    Output("feedback_popup_text", "value"),
    [
        Input("open_feedback_popup", "n_clicks"), 
    ],
    [State("plot_qc_popup", "is_open")],
)
def clear_popup_text(n1, is_open):
    return ''


# clear experiment selections
@app.callback(
    Output("feedback_popup_experiments", "value"),
    [
        Input("open_feedback_popup", "n_clicks"), 
    ],
    [State("plot_qc_popup", "is_open")],
)
def clear_experiment_labels(n1, is_open):
    return []


# clear qc label selections
@app.callback(
    Output("feedback_popup_qc_labels", "value"),
    [
        Input("open_feedback_popup", "n_clicks"), 
    ],
    [State("plot_qc_popup", "is_open")],
)
def clear_qc_labels(n1, is_open):
    return []


#populate datetime in feedback popup
@app.callback(
    Output("feedback_popup_datetime", "value"),
    [
        Input("open_feedback_popup", "n_clicks"), 
    ],
)
def populate_popup_datetime(n_clicks):
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.callback(Output('data_table', 'page_size'), [Input('entries_per_page_input', 'value')])
def change_entries_per_page(entries_per_page):
    return entries_per_page


@app.callback(Output('container_overview_iframe', 'src'), [Input('container_overview_dropdown', 'value')])
def embed_iframe(value):
    print('getting a new iframe')
    print('value: {}'.format(value))
    if value == 'motion_corrected_movies':
        print("going to show URLs!!!!")
        return None
    else:
        return app.get_asset_url('qc_plots/overview_plots/{}'.format(value))


# update container overview options when container checklist state is changed
@app.callback(Output('container_overview_dropdown', 'options'), [Input('container_checklist', 'value')])
def update_container_overview_options(checkbox_values):
    global container_overview_plot_options
    container_overview_plot_options = functions.load_container_overview_plot_options()
    return container_overview_plot_options


# update container plot options when container checklist state is changed
@app.callback(Output('container_plot_dropdown', 'options'), [Input('container_checklist', 'value')])
def update_container_plot_options(checkbox_values):
    global container_plot_options
    container_plot_options = functions.load_container_plot_options()
    return container_plot_options


# show/hide container view frame based on 'container_checklist'
@app.callback(Output('container_overview_iframe', 'hidden'), [Input('container_checklist', 'value')])
def show_container_view(checkbox_values):
    if 'show_container_plots' in checkbox_values:
        # retun hidden = False
        return False
    else:
        # return hidden = True
        return True


# repopulate plot inventory frame based on 'container_checklist'
@app.callback(Output('plot_inventory_graph', 'figure'), [Input('container_checklist', 'value')])
def regenerate_plot_inventory(checkbox_values):
    if 'show_plot_inventory' in checkbox_values:

        plot_inventory = functions.generate_plot_inventory()
        plot_inventory_fig = functions.make_plot_inventory_heatmap(plot_inventory)
        temp_fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[1, 8 * np.random.rand(), 2])])
        return plot_inventory_fig
    else:
        # return hidden = True
        temp_fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[0, 0, 0])])
        return temp_fig


# show/hide plot inventory frame based on 'container_checklist'
@app.callback(Output('plot_inventory_container', 'style'), [Input('container_checklist', 'value')])
def show_plot_inventory(checkbox_values):
    if 'show_plot_inventory' in checkbox_values:
        # retun hidden = False
        print('making plot visible!!')
        return {'display': 'block'}
    else:
        # return hidden = True
        return {'display': 'none'}


# show/hide container dropdown based on 'container_checklist'
@app.callback(Output('container_overview_dropdown', 'style'), [Input('container_checklist', 'value')])
def show_container_dropdown(checkbox_values):
    if 'show_container_plots' in checkbox_values:
        # return hidden = False
        return {'display': 'block'}
    else:
        # return hidden = True
        return {'display': 'none'}


# highlight row in data table
@app.callback(Output('data_table', 'data'),
              [
                  Input('data_table', 'selected_rows'),
                  Input('feedback_popup_ok', 'n_clicks'),
                  Input("stored_feedback", "children")
               ]
)
def update_data(selected_rows, n_clicks, stored_feedback):
    print('updating data table at {}'.format(time.time()))
    container_table = functions.load_data().sort_values('first_acquistion_date')
    data = container_table.to_dict('records')
    return data

# highlight row in data table
@app.callback(Output('data_table', 'style_data_conditional'),
              [Input('data_table', 'selected_rows'),
               Input('data_table', 'page_current'),
               Input('data_table', 'derived_viewport_indices')
               ])
def highlight_row(row_index, page_current, derived_viewport_indices):
    # row index is None on the very first call. This avoids an error:
    if row_index is None or derived_viewport_indices is None:
        index_to_highlight = 0
    elif row_index[0] in derived_viewport_indices:
        index_to_highlight = derived_viewport_indices.index(row_index[0])
    else:
        index_to_highlight = 1e6

    style_data_conditional = [{
        "if": {"row_index": index_to_highlight},
        "backgroundColor": "#3D9970",
        'color': 'white'
    }]
    return style_data_conditional

# set plot titles
# this is just text above the actual plot frame
# Use this loop to determine the correct title to update
def update_plot_title(plot_types, input_id):
    '''a function to update plot titles'''
    idx = int(input_id.split('plot_title_')[1])
    try:
        return plot_types[idx]
    except IndexError:
        return ''
for i in range(10):
    app.callback(
        Output(f"plot_title_{i}", "children"), 
        [Input(f"container_plot_dropdown", "value"), Input(f"plot_title_{i}", "id")]
    )(update_plot_title)

# image frames callbacks
# generated in a loop
def update_frame_N(row_index, plot_types, input_id):
    '''
    a function to fill the image frames
    '''
    idx = int(input_id.split('image_frame_')[1])
    try:
        plot_type = plot_types[idx]
        container_id = container_table.iloc[row_index[0]]['container_id']
        encoded_image = functions.get_container_plot(container_id, plot_type=plot_type)
        return 'data:image/png;base64,{}'.format(encoded_image.decode())
    except IndexError:
        return None
for i in range(10):
    app.callback(
        Output(f"image_frame_{i}", "src"), 
        [
            Input('data_table', 'selected_rows'), 
            Input('container_plot_dropdown', 'value'), 
            Input(f"image_frame_{i}", "id")
        ]
    )(update_frame_N)

# update_links

def update_link_text_N(row_index, input_id):
    '''a function to update plot titles'''
    idx = int(input_id.split('link_')[1])
    container_id = container_table.iloc[row_index[0]]['container_id']
    link_list = functions.get_motion_corrected_movie_paths(container_id)
    try:
        return link_list[idx].replace('/','\\')
    except IndexError:
        return 'INVALID LINK'
for i in range(10):
    app.callback(
        Output(f"link_{i}", "children"), 
        [Input('data_table', 'selected_rows'), Input(f"link_{i}", "id")]
    )(update_link_text_N)

def update_link_destination_N(row_index, input_id):
    '''a function to update plot titles'''
    idx = int(input_id.split('link_')[1])
    container_id = container_table.iloc[row_index[0]]['container_id']
    link_list = functions.get_motion_corrected_movie_paths(container_id)
    try:
        return 'file:{}'.format(link_list[idx])
    except IndexError:
        return 'https://www.google.com/'
for i in range(10):
    app.callback(
        Output(f"link_{i}", "href"), 
        [Input('data_table', 'selected_rows'), Input(f"link_{i}", "id")]
    )(update_link_destination_N)

def update_link_visibility_N(row_index, input_id):
    '''a function to update plot titles'''
    idx = int(input_id.split('link_')[1])
    container_id = container_table.iloc[row_index[0]]['container_id']
    link_list = functions.get_motion_corrected_movie_paths(container_id)
    try:
        link = link_list[idx]
        print("Returning True, idx = {}".format(idx))
        return {'display': True}
    except IndexError:
        print("Returning None, idx = {}".format(idx))
        return {'display': 'none'}
for i in range(10):
    app.callback(
        Output(f"link_{i}", "style"), 
        [Input('data_table', 'selected_rows'), Input(f"link_{i}", "id")]
    )(update_link_visibility_N)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Run dash visualization app for VB production data')
    parser.add_argument(
        '--port',
        type=int,
        default='3389',
        metavar='port on which to host. 3389 (Remote desktop port) by default, since it is open over VPN)'
    )
    parser.add_argument(
        '--debug',
        help='boolean, not followed by an argument. Enables debug mode. False by default.',
        action='store_true'
    )
    args = parser.parse_args()
    print("PORT = {}".format(args.port))
    print("DEBUG MODE = {}".format(args.debug))
    app.run_server(debug=args.debug, port=args.port, host='0.0.0.0')


@app.callback(Output('link_0', 'children'),
              [Input('data_table', 'selected_rows'),
               Input('container_plot_dropdown', 'value'),
               ])
def print_movie_paths(row_index, plot_types):
    plot_type = plot_types[0]
    container_id = container_table.iloc[row_index[0]]['container_id']
    output_text = functions.print_motion_corrected_movie_paths(container_id)
    print(output_text)
    return output_text