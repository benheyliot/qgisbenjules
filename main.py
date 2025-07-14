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
app.layout = serve_layout

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
        elif ext in ['.geojson', '.json', '.shp']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                gdf = gpd.read_file(tmp.name)
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    vector_layers.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                elif row.geometry.geom_type == "Point":
                    vector_layers.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
        elif ext in ['.tif', '.tiff']:
            bounds = tiff_to_image_overlay(file_bytes, filename)
            # For MVP, use a placeholder image (you can generate a PNG from the TIFF for real use)
            # Here, we just show the bounds as a transparent overlay
            raster_layers.append(
                dl.ImageOverlay(
                    url="https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png",
                    bounds=bounds,
                    opacity=0.5
                )
            )
    return vector_layers, raster_layers

# --- QGIS Server Integration Example ---
# This is a simple example for a spatial join using QGIS Server's WFS endpoint.
# Replace URL and params with your QGIS Server details.

def qgis_spatial_join(point_lat, point_lon, wfs_url, layer_name):
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": layer_name,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "CQL_FILTER": f"INTERSECTS(geometry, POINT({point_lon} {point_lat}))"
    }
    r = requests.get(wfs_url, params=params)
    if r.status_code == 200:
        features = r.json().get("features", [])
        if features:
            return features[0]["properties"]
    return {}

# Example usage in a callback (not wired in above for brevity):
# props = qgis_spatial_join(48.85, 2.35, "http://your-qgis-server-url/ows", "your_layer_name")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
