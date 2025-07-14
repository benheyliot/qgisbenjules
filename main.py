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

from app.components.layout import serve_layout
from app.utils.kml_to_geojson import kml_or_kmz_to_gdf
from app.utils.raster_to_tile import tiff_to_image_overlay

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

static_overlays = []
for file in os.listdir('app/data'):
    if file.endswith(('.kml', '.kmz', '.geojson', '.json', '.shp', '.tif', '.tiff')):
        with open(os.path.join('app/data', file), 'rb') as f:
            file_bytes = f.read()
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.kml', '.kmz']:
                gdf = kml_or_kmz_to_gdf(file_bytes, file)
                for _, row in gdf.iterrows():
                    if row.geometry.geom_type == "Polygon":
                        static_overlays.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                    elif row.geometry.geom_type == "Point":
                        static_overlays.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
            elif ext in ['.geojson', '.json']:
                gdf = gpd.read_file(io.BytesIO(file_bytes))
                for _, row in gdf.iterrows():
                    if row.geometry.geom_type == "Polygon":
                        static_overlays.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                    elif row.geometry.geom_type == "Point":
                        static_overlays.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
            elif ext == '.shp':
                with tempfile.TemporaryDirectory() as tmpdir:
                    with open(os.path.join(tmpdir, file), 'wb') as f:
                        f.write(file_bytes)
                    gdf = gpd.read_file(os.path.join(tmpdir, file))
                for _, row in gdf.iterrows():
                    if row.geometry.geom_type == "Polygon":
                        static_overlays.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                    elif row.geometry.geom_type == "Point":
                        static_overlays.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
            elif ext in ['.tif', '.tiff']:
                bounds = tiff_to_image_overlay(file_bytes, file)
                static_overlays.append(
                    dl.ImageOverlay(
                        url="https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png",
                        bounds=bounds,
                        opacity=0.5
                    )
                )

app.layout = serve_layout(static_overlays)

@app.callback(
    Output('network-filter', 'options'),
    Output('network-filter', 'value'),
    Output('markers', 'children'),
    Output('stats', 'children'),
    Input('upload-csv', 'contents'),
    Input('network-filter', 'value'),
    State('upload-csv', 'filename'),
)
def update_map(csv_contents, selected_network, csv_filename):
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
        return [], None, [], ""

    options = [{'label': n, 'value': n} for n in sorted(df['network_name'].unique())]
    if selected_network:
        df = df[df['network_name'] == selected_network]
    markers = [
        dl.Marker(
            position=[row['latitude'], row['longitude']],
            children=dl.Tooltip(str(row['network_name'])),
        ) for _, row in df.iterrows()
    ]
    stats = f"Total nodes: {len(df)}"
    return options, selected_network, markers, stats

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

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
