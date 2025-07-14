import dash
from dash import Output, Input, State, html, dcc
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
import base64
import io
import os
import tempfile
import requests

from app.utils.kml_to_geojson import kml_or_kmz_to_gdf
from app.utils.raster_to_tile import tiff_to_image_overlay

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("LoRa Network Map"),
            dcc.Upload(
                id='upload-csv',
                children=html.Div(['Upload CSV']),
                style={'width': '100%', 'height': '40px', 'lineHeight': '40px',
                       'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                       'textAlign': 'center', 'margin': '10px'},
                multiple=False
            ),
            dcc.Upload(
                id='upload-coverage',
                children=html.Div(['Upload Coverage (KML/KMZ, GeoJSON, SHP, TIFF)']),
                style={'width': '100%', 'height': '40px', 'lineHeight': '40px',
                       'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                       'textAlign': 'center', 'margin': '10px'},
                multiple=True
            ),
            dcc.Dropdown(id='network-filter', placeholder="Filter by network_name"),
            html.Div(id='stats')
        ], width=3),
        dbc.Col([
            dl.Map(center=[46.603354, 1.888334], zoom=6, id='map', style={'height': '80vh'},
                   children=[
                       dl.TileLayer(),
                       dl.LayersControl(
                           [dl.BaseLayer(dl.TileLayer(), name="OpenStreetMap", checked=True)] +
                           [dl.Overlay(dl.LayerGroup(id='markers'), name="Markers", checked=True)] +
                           [dl.Overlay(dl.LayerGroup(id='coverages'), name="Coverages", checked=True)] +
                           [dl.Overlay(dl.LayerGroup(id='rasters'), name="Rasters", checked=True)]
                       )
                   ])
        ], width=9)
    ])
], fluid=True)
server = app.server

@app.callback(
    Output('markers', 'children'),
    Input('network-filter', 'value'),
    State('upload-csv', 'contents'),
    State('upload-csv', 'filename'),
)
def update_map(selected_network, csv_contents, csv_filename):
    if csv_contents:
        content_type, content_string = csv_contents.split(',')
        decoded = io.BytesIO(base64.b64decode(content_string))
        df = pd.read_csv(decoded)
    else:
        df = pd.DataFrame()
        for file in os.listdir('app/data'):
            if file.endswith('.csv'):
                df = pd.concat([df, pd.read_csv(os.path.join('app/data', file))])

    if df.empty:
        return []

    if selected_network:
        df = df[df['network_name'] == selected_network]
    markers = [
        dl.Marker(
            position=[row['latitude'], row['longitude']],
            children=dl.Tooltip(str(row['network_name'])),
        ) for _, row in df.iterrows()
    ]
    return markers

@app.callback(
    Output('coverages', 'children'),
    Output('rasters', 'children'),
    Input('upload-coverage', 'contents'),
    State('upload-coverage', 'filename'),
    prevent_initial_call=True
)
def update_coverages(coverages_contents, coverages_filenames):
    if not coverages_contents:
        return [], []
    vector_layers = []
    raster_layers = []
    for content, filename in zip(coverages_contents, coverages_filenames):
        content_type, content_string = content.split(',')
        file_bytes = base64.b64decode(content_string)
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.kml', '.kmz']:
            gdf = kml_or_kmz_to_gdf(file_bytes, filename)
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    vector_layers.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                elif row.geometry.geom_type == "Point":
                    vector_layers.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
        elif ext in ['.geojson', '.json']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                gdf = gpd.read_file(tmp.name)
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    vector_layers.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                elif row.geometry.geom_type == "Point":
                    vector_layers.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
        elif ext == '.shp':
            with tempfile.TemporaryDirectory() as tmpdir:
                for content, filename in zip(coverages_contents, coverages_filenames):
                     content_type, content_string = content.split(',')
                     file_bytes = base64.b64decode(content_string)
                     with open(os.path.join(tmpdir, filename), 'wb') as f:
                         f.write(file_bytes)
                gdf = gpd.read_file(os.path.join(tmpdir, [f for f in os.listdir(tmpdir) if f.endswith('.shp')][0]))
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    vector_layers.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                elif row.geometry.geom_type == "Point":
                    vector_layers.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
        elif ext in ['.tif', '.tiff']:
            bounds = tiff_to_image_overlay(file_bytes, filename)
            raster_layers.append(
                dl.ImageOverlay(
                    url="https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png",
                    bounds=bounds,
                    opacity=0.5
                )
            )
    return vector_layers, raster_layers

@app.callback(
    Output('network-filter', 'options'),
    Input('upload-csv', 'contents'),
)
def update_dropdown(csv_contents):
    if csv_contents:
        content_type, content_string = csv_contents.split(',')
        decoded = io.BytesIO(base64.b64decode(content_string))
        df = pd.read_csv(decoded)
    else:
        df = pd.DataFrame()
        for file in os.listdir('app/data'):
            if file.endswith('.csv'):
                df = pd.concat([df, pd.read_csv(os.path.join('app/data', file))])

    if df.empty:
        return []

    options = [{'label': n, 'value': n} for n in sorted(df['network_name'].unique())]
    return options

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
