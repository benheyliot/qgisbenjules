import dash
from dash import Output, Input, State
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
import base64
import io
import os
import tempfile
import requests

from app.components.layout import layout
from app.utils.kml_to_geojson import kml_or_kmz_to_gdf
from app.utils.raster_to_tile import tiff_to_image_overlay

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = layout
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
