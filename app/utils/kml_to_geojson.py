import os
import base64
import requests
from dash import Dash, dcc, html, Output, Input, State, callback, exceptions
import dash_leaflet as dl
from flask import Flask

# --- Flask server and blueprint registration ---
server = Flask(__name__)
from app.utils.vector_file_server import vector_bp
server.register_blueprint(vector_bp)

# --- Directories ---
VECTOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'data', 'vector'))
RASTER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'data', 'raster'))

# --- Dash app ---
app = Dash(__name__, server=server)

app.layout = html.Div([
    html.H1("Map Viewer"),
    dl.Map(center=[48.85, 2.35], zoom=10, id="map", style={'height': '70vh'}, children=[
        dl.TileLayer(),
        dl.LayerGroup(id="vector-layers"),
        # Example raster overlay (uncomment if you have a raster file)
        # dl.ImageOverlay(url="/raster/your_raster.tif", bounds=[[lat1, lon1], [lat2, lon2]])
    ]),
    html.H2("Available Vector Layers"),
    dcc.Dropdown(id="layer-dropdown"),
    html.H2("Upload Geospatial File"),
    dcc.Upload(
        id='upload-geo',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        multiple=False
    ),
    html.Div(id='upload-geo-output'),
])

# --- Helper: Save uploaded file ---
def save_file(name, content):
    data = content.encode("utf8").split(b";base64,")[1]
    ext = os.path.splitext(name)[1].lower()
    if ext in ['.kml', '.kmz', '.gpkg', '.shp']:
        save_dir = VECTOR_DIR
    elif ext in ['.tif', '.tiff']:
        save_dir = RASTER_DIR
    else:
        return "Unsupported file type."
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, name)
    with open(filepath, "wb") as fp:
        fp.write(base64.decodebytes(data))
    return f"Saved {name} to {save_dir}"

# --- Callbacks ---

@app.callback(
    Output("layer-dropdown", "options"),
    Input("map", "id")  # dummy input to trigger on load
)
def update_layer_dropdown(_):
    files = requests.get("http://localhost:8050/vector_layers").json()
    return [{"label": f, "value": f} for f in files]

@app.callback(
    Output("vector-layers", "children"),
    Input("layer-dropdown", "value")
)
def display_layer(filename):
    if filename:
        geojson = requests.get(f"http://localhost:8050/vector_layer/{filename}").json()
        return [dl.GeoJSON(data=geojson)]
    return []

@app.callback(
    Output('upload-geo-output', 'children'),
    Output('layer-dropdown', 'options'),
    Input('upload-geo', 'contents'),
    State('upload-geo', 'filename'),
    State('layer-dropdown', 'options')
)
def upload_geo_file(contents, filename, current_options):
    if contents and filename:
        msg = save_file(filename, contents)
        # Refresh the vector layer list
        files = requests.get("http://localhost:8050/vector_layers").json()
        options = [{"label": f, "value": f} for f in files]
        return msg, options
    raise exceptions.PreventUpdate

if __name__ == "__main__":
    app.run_server(debug=True) 