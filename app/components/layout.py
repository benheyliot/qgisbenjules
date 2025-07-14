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

from app.components.layout import layout
from app.utils.kml_to_geojson import kml_or_kmz_to_gdf

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = layout

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

if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0")
