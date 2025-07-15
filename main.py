import dash
from dash import dcc, html, Input, Output, State
import dash_leaflet as dl
import pandas as pd
import dash_uploader as du
from pathlib import Path
from app.components.layout import layout
import dash_bootstrap_components as dbc

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
UPLOAD_FOLDER_ROOT = r"app/data"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)

app.layout = layout
server = app.server

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


import geopandas as gpd
from owslib.wms import WebMapService

try:
    wms = WebMapService('https://qgiscloud.com/ttechnicienheyliot/QGIS_CD38_final__1_/wms', version='1.3.0')
    print("WMS capabilities loaded successfully.")
    print(list(wms.contents))
except Exception as e:
    print(f"Error loading WMS capabilities: {e}")


coverage = gpd.read_file("coverage.geojson")

@app.callback(
    Output('markers', 'children'),
    [Input('dataframe-store', 'data'),
     Input('network-filter', 'value')]
)
def update_map(data, network_filter):
    children = [
        dl.TileLayer(),
        dl.GeoJSON(data=coverage.__geo_interface__, style={'color': 'blue', 'opacity': 0.5, 'fillOpacity': 0.2}),
        dl.WMSLayer(url="https://qgiscloud.com/ttechnicienheyliot/QGIS_CD38_final__1_/wms", layers="QGIS_CD38_final", format="image/png", transparent=True)
    ]
    if data is not None:
        df = pd.DataFrame(data)
        if network_filter and network_filter != 'all':
            df = df[df['network_name'] == network_filter]

        markers = []
        for index, row in df.iterrows():
            markers.append(dl.Marker(position=[row['latitude'], row['longitude']]))
        children.append(dl.LayerGroup(markers))

    return children


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


@app.callback(
    Output('table-container', 'children'),
    Input('dataframe-store', 'data')
)
def update_table(data):
    if data is None:
        return []

    df = pd.DataFrame(data)
    return html.Div([
        dash.dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        )
    ])


@app.callback(
    Output('download-button', 'disabled'),
    Input('dataframe-store', 'data')
)
def enable_download_button(data):
    return data is None


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State('dataframe-store', 'data'),
    prevent_initial_call=True,
)
def download_csv(n_clicks, data):
    if data is None:
        return None

    df = pd.DataFrame(data)
    points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    joined = gpd.sjoin(points, coverage, how="left", op='within')

    return dcc.send_data_frame(joined.to_csv, "coverage_results.csv")


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State('dataframe-store', 'data'),
    prevent_initial_call=True,
)
def download_csv(n_clicks, data):
    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_csv, "coverage_results.csv")


if __name__ == '__main__':
    app.run_server(debug=True)
