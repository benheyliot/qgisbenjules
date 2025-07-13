import dash
from dash import dcc, html, Input, Output, State
import dash_leaflet as dl
import pandas as pd
import dash_uploader as du
from pathlib import Path

# Create the Dash app
app = dash.Dash(__name__)
UPLOAD_FOLDER_ROOT = r"app/data"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)

# App layout
app.layout = html.Div([
    dcc.Store(id='dataframe-store'),
    html.H1("LoRa Network Visualizer"),
    html.Div(du.Upload(), className='upload'),
    dcc.Dropdown(id='network-filter', placeholder="Filter by network"),
    dl.Map(id='map', center=[46.603354, 1.888334], zoom=6,
            children=[dl.TileLayer()], style={'width': '100%', 'height': '80vh'})
], style={'padding': '10px'})


@du.callback(
    output=Output('dataframe-store', 'data'),
    id='upload',
)
def callback_on_completion(filenames):
    if not filenames:
        return None

    filepath = Path(UPLOAD_FOLDER_ROOT) / filenames[0]
    df = pd.read_csv(filepath)
    return df.to_dict('records')


@app.callback(
    Output('network-filter', 'options'),
    Input('dataframe-store', 'data')
)
def update_dropdown(data):
    if data is None:
        return []
    df = pd.DataFrame(data)
    return [{'label': i, 'value': i} for i in df['network_name'].unique()]


@app.callback(
    Output('map', 'children'),
    [Input('dataframe-store', 'data'),
     Input('network-filter', 'value')]
)
def update_map(data, network_filter):
    if data is None:
        return [dl.TileLayer()]

    df = pd.DataFrame(data)
    if network_filter:
        df = df[df['network_name'] == network_filter]

    markers = []
    for index, row in df.iterrows():
        markers.append(dl.Marker(position=[row['latitude'], row['longitude']]))

    return [dl.TileLayer()] + markers


if __name__ == '__main__':
    app.run_server(debug=True)
