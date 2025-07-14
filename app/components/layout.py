import dash
from dash import dcc, html, Output, Input, State, ctx
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
import base64
import io
import os
import tempfile

from app.utils.kml_to_geojson import kml_or_kmz_to_gdf
from app.utils.raster_to_tile import tiff_to_image_overlay

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# CSV Upload and Marker Display
@app.callback(
    Output('node-markers', 'children'),
    Output('network-filter', 'options'),
    Output('network-filter', 'value'),
    Output('stats-section', 'children'),
    Input('upload-csv', 'contents'),
    Input('network-filter', 'value'),
    State('upload-csv', 'filename'),
    prevent_initial_call=True
)
def update_markers(csv_contents, selected_network, csv_filename):
    if not csv_contents:
        return [], [], None, ""
    # Parse CSV, extract latitude/longitude/network_name, and create markers
    # Example:
    # df = pd.read_csv(...)
    # markers = [dl.Marker(position=[row['latitude'], row['longitude']]) for ...]
    pass  # Implement as above

# Coverage Upload and Display
@app.callback(
    Output('coverage-layers', 'children'),
    Input('upload-coverage', 'contents'),
    State('upload-coverage', 'filename'),
    prevent_initial_call=True
)
def update_coverages(contents, filenames):
    if not contents:
        return []
    layers = []
    for content, filename in zip(contents, filenames):
        # Parse file (KML/KMZ/GeoJSON/SHP) and add polygons/points to layers
        # Use your kml_to_geojson utility, geopandas, etc.
        # Example for KML:
        # gdf = kml_or_kmz_to_gdf(file_bytes, filename)
        # for _, row in gdf.iterrows():
        #     if row.geometry.geom_type == "Polygon":
        #         layers.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
        #     elif row.geometry.geom_type == "Point":
        #         layers.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
        pass  # Implement as above
    return layers

def load_static_coverages(data_dir="app/data"):
    overlays = []
    for fname in os.listdir(data_dir):
        path = os.path.join(data_dir, fname)
        ext = os.path.splitext(fname)[1].lower()
        layer_name = os.path.splitext(fname)[0]
        if ext in [".kml", ".kmz"]:
            with open(path, "rb") as f:
                gdf = kml_or_kmz_to_gdf(f.read(), fname)
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    overlays.append(dl.Overlay(dl.Polygon(positions=[list(row.geometry.exterior.coords)]),
                                              name=layer_name, checked=False))
                elif row.geometry.geom_type == "Point":
                    overlays.append(dl.Overlay(dl.Marker(position=[row.geometry.y, row.geometry.x]),
                                              name=layer_name, checked=False))
        elif ext in [".geojson", ".json", ".shp"]:
            gdf = gpd.read_file(path)
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    overlays.append(dl.Overlay(dl.Polygon(positions=[list(row.geometry.exterior.coords)]),
                                              name=layer_name, checked=False))
                elif row.geometry.geom_type == "Point":
                    overlays.append(dl.Overlay(dl.Marker(position=[row.geometry.y, row.geometry.x]),
                                              name=layer_name, checked=False))
        elif ext in [".tif", ".tiff"]:
            bounds = tiff_to_image_overlay(open(path, "rb").read(), fname)
            overlays.append(dl.Overlay(
                dl.ImageOverlay(
                    url="/assets/your_raster.png",  # You'd need to generate this PNG from the TIFF
                    bounds=bounds,
                    opacity=0.5
                ),
                name=layer_name, checked=False
            ))
    return overlays

def serve_layout(static_overlays):
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Upload Coverage (KML/KMZ/GeoJSON/SHP)"),
                dcc.Upload(
                    id='upload-coverage',
                    children=html.Div(['Drag & Drop or Click to Select Coverage Files']),
                    style={'width': '100%', 'height': '60px', 'lineHeight': '60px',
                           'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                           'textAlign': 'center', 'margin': '10px'},
                    multiple=True
                ),
                html.H4("Upload Nodes (CSV)"),
                dcc.Upload(
                    id='upload-csv',
                    children=html.Div(['Drag & Drop or Click to Select CSV File']),
                    style={'width': '100%', 'height': '60px', 'lineHeight': '60px',
                           'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                           'textAlign': 'center', 'margin': '10px'},
                    multiple=False
                ),
                dcc.Dropdown(id='network-filter', placeholder="Filter by network_name"),
                html.Div(id='stats-section')
            ], width=3),
            dbc.Col([
                dl.Map(center=[46.5, 2.5], zoom=6, id='map', style={'height': '80vh'},
                       children=[
                           dl.TileLayer(),
                           dl.LayerGroup(id='coverage-layers'),
                           dl.LayerGroup(id='node-markers')
                       ])
            ], width=9)
        ])
    ], fluid=True)

if __name__ == '__main__':
    static_overlays = load_static_coverages()
    app.layout = serve_layout(static_overlays)
    app.run_server(debug=True, host="0.0.0.0")
