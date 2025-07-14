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
    Output('markers', 'children'),
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
    content_type, content_string = csv_contents.split(',')
    decoded = io.BytesIO(base64.b64decode(content_string))
    df = pd.read_csv(decoded)
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
    return markers, options, selected_network, stats

# Coverage Upload and Display
@app.callback(
    Output('coverages', 'children'),
    Input('upload-coverage', 'contents'),
    State('upload-coverage', 'filename'),
    prevent_initial_call=True
)
def update_coverages(coverages_contents, coverages_filenames):
    if not coverages_contents:
        return []
    layers = []
    for content, filename in zip(coverages_contents, coverages_filenames):
        content_type, content_string = content.split(',')
        file_bytes = base64.b64decode(content_string)
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.kml', '.kmz']:
            gdf = kml_or_kmz_to_gdf(file_bytes, filename)
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    layers.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                elif row.geometry.geom_type == "Point":
                    layers.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
        elif ext in ['.geojson', '.json', '.shp']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                gdf = gpd.read_file(tmp.name)
            for _, row in gdf.iterrows():
                if row.geometry.geom_type == "Polygon":
                    layers.append(dl.Polygon(positions=[list(row.geometry.exterior.coords)]))
                elif row.geometry.geom_type == "Point":
                    layers.append(dl.Marker(position=[row.geometry.y, row.geometry.x]))
        # TIFF: For MVP, skip or show a message
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
        # ... your upload and filter UI ...
        dl.Map(center=[46.5, 2.5], zoom=6, id='map', style={'width': '100%', 'height': '80vh'},
               children=[
                   dl.TileLayer(),
                   dl.LayersControl(
                       [dl.BaseLayer(dl.TileLayer(), name="OpenStreetMap", checked=True)] +
                       static_overlays +  # <-- static overlays here
                       [dl.Overlay(dl.LayerGroup(id='markers'), name="Markers", checked=True),
                        dl.Overlay(dl.LayerGroup(id='coverages'), name="Uploaded Coverages", checked=True)]
                   )
               ])
    ], fluid=True)

if __name__ == '__main__':
    static_overlays = load_static_coverages()
    app.layout = serve_layout(static_overlays)
    app.run_server(debug=True, host="0.0.0.0")
