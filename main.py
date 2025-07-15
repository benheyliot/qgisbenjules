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
    id='upload-csv',
)
def callback_on_csv_completion(filenames):
    if not filenames:
        return None

    filepath = Path(UPLOAD_FOLDER_ROOT) / filenames[0]
    df = pd.read_csv(filepath)
    return df.to_dict('records')


@app.callback(
    output=Output('coverage-store', 'data'),
    id='upload-coverage',
)
def callback_on_coverage_completion(filenames):
    if not filenames:
        return None

    filepath = Path(UPLOAD_FOLDER_ROOT) / filenames[0]
    # For now, assume it's a geojson file
    gdf = gpd.read_file(filepath)
    return gdf.to_json()


import os

@app.callback(
    Output('layer-checklist', 'options'),
    Output('layer-checklist', 'value'),
    Input('dataframe-store', 'data')  # Just to trigger on app load
)
def update_layer_checklist(_):
    vector_layers = [f for f in os.listdir('app/data/vector') if f.endswith('.geojson')]
    raster_layers = [f for f in os.listdir('app/data/raster') if f.endswith('.tif')]

    options = [{'label': layer, 'value': layer} for layer in vector_layers + raster_layers]
    return options, []


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
     Input('coverage-store', 'data'),
     Input('network-filter', 'value'),
     Input('layer-checklist', 'value')]
)
def update_map(data, coverage_data, network_filter, selected_layers):
    children = [
        dl.TileLayer(),
        dl.WMSLayer(url="https://qgiscloud.com/ttechnicienheyliot/QGIS_CD38_final__1_/wms", layers="QGIS_CD38_final", format="image/png", transparent=True)
    ]

    for layer in selected_layers:
        if layer.endswith('.geojson'):
            path = os.path.join('app/data/vector', layer)
            gdf = gpd.read_file(path)
            children.append(dl.GeoJSON(data=gdf.to_json(), style={'color': 'red', 'opacity': 0.5, 'fillOpacity': 0.2}))

    if coverage_data is not None:
        children.append(dl.GeoJSON(data=coverage_data, style={'color': 'blue', 'opacity': 0.5, 'fillOpacity': 0.2}))

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
