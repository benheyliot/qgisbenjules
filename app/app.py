import dash
from dash import dcc, html, Input, Output, State
import dash_leaflet as dl
import pandas as pd
import dash_uploader as du
from pathlib import Path
from components.layout import layout

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
UPLOAD_FOLDER_ROOT = r"app/data"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)

app.layout = layout

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
    options = [{'label': i, 'value': i} for i in df['network_name'].unique()]
    options.insert(0, {'label': 'All Networks', 'value': 'all'})
    return options


@app.callback(
    Output('markers', 'children'),
    [Input('dataframe-store', 'data'),
     Input('network-filter', 'value')]
)
def update_map(data, network_filter):
    if data is None:
        return []

    df = pd.DataFrame(data)
    if network_filter and network_filter != 'all':
        df = df[df['network_name'] == network_filter]

    markers = []
    for index, row in df.iterrows():
        markers.append(dl.CircleMarker(center=[row['latitude'], row['longitude']], radius=5,
                                        children=[
                                            dl.Tooltip(f"Network: {row['network_name']}\\nLocation: {row['latitude']}, {row['longitude']}")
                                        ]))

    return markers

@app.callback(
    Output('stats-section', 'children'),
    Input('dataframe-store', 'data')
)
def update_stats(data):
    if data is None:
        return []

    df = pd.DataFrame(data)
    num_nodes = len(df)
    nodes_per_network = df['network_name'].value_counts().to_dict()

    stats = [
        html.H4("Statistics"),
        html.P(f"Total Nodes: {num_nodes}"),
        html.H5("Nodes per Network:")
    ]
    for network, count in nodes_per_network.items():
        stats.append(html.P(f"{network}: {count}"))

    return stats


if __name__ == '__main__':
    app.run_server(debug=True)
