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
from fpdf import FPDF

from utils.kml_to_geojson import kml_or_kmz_to_gdf
from utils.raster_to_tile import tiff_to_image_overlay

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dcc.ConfirmDialogProvider(
        children=html.Button('Click Me'),
        id='confirm',
        message='Are you sure you want to continue?'
    ),
    dbc.Row([
        dbc.Col([
            html.H2("LoRa Network Map"),
            dcc.Tabs(id="tabs", value='tab-1', children=[
                dcc.Tab(label='Controls', value='tab-1', children=[
                    html.Br(),
                    html.P("Upload a CSV file with LoRa node data. The file should contain 'latitude', 'longitude', and 'network_name' columns."),
                    dcc.Upload(
                        id='upload-csv',
                        children=html.Div(['Drag and Drop or Select Files']),
                        style={'width': '100%', 'height': '60px', 'lineHeight': '60px',
                               'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                               'textAlign': 'center', 'margin': '10px'},
                        multiple=False
                    ),
                    html.P("Upload coverage files in KML, KMZ, GeoJSON, SHP, or TIFF format."),
                    dcc.Upload(
                        id='upload-coverage',
                        children=html.Div(['Drag and Drop or Select Files']),
                        style={'width': '100%', 'height': '60px', 'lineHeight': '60px',
                               'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                               'textAlign': 'center', 'margin': '10px'},
                        multiple=True
                    ),
                    dcc.Dropdown(id='network-filter', placeholder="Filter by network_name"),
                    dcc.Dropdown(id='marker-icon-filter', placeholder="Select marker icon",
                                 options=[
                                     {'label': 'Default', 'value': 'default'},
                                     {'label': 'Red', 'value': 'red'},
                                     {'label': 'Green', 'value': 'green'},
                                     {'label': 'Blue', 'value': 'blue'},
                                 ],
                                 value='default'),
                    html.Br(),
                    html.Button("Download CSV", id="btn_csv", n_clicks=0),
                    html.Button("Download PDF", id="btn_pdf", n_clicks=0),
                    dcc.Download(id="download-dataframe-csv"),
                    dcc.Download(id="download-dataframe-pdf"),
                ]),
                dcc.Tab(label='Stats', value='tab-2', children=[
                    dcc.Loading(id="loading-stats", type="circle", children=html.Div(id='stats'))
                ]),
            ]),
        ], width=3),
        dbc.Col([
            dcc.Loading(id="loading-map", type="circle", children=
                dl.Map(center=[46.603354, 1.888334], zoom=6, id='map', style={'height': '80vh'},
                       children=[
                           dl.TileLayer(),
                           dl.LayersControl(
                               [dl.BaseLayer(dl.TileLayer(), name="OpenStreetMap", checked=True)] +
                           [dl.Overlay(dl.MarkerClusterGroup(id="markers", options={"spiderfyOnMaxZoom": True}), name="Markers", checked=True)] +
                               [dl.Overlay(dl.LayerGroup(id='coverages'), name="Coverages", checked=True)] +
                               [dl.Overlay(dl.LayerGroup(id='rasters'), name="Rasters", checked=True)]
                           )
                       ])
            )
        ], width=9)
    ])
], fluid=True)
server = app.server

@app.callback(
    Output('markers', 'children'),
    Input('network-filter', 'value'),
    State('upload-csv', 'contents'),
    State('upload-csv', 'filename'),
    Input('marker-icon-filter', 'value'),
)
def update_map(selected_network, csv_contents, csv_filename, marker_icon):
    try:
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

        icon = {
            "iconUrl": f"assets/{marker_icon}.png",
            "iconSize": [25, 41],
            "iconAnchor": [12, 41],
            "popupAnchor": [1, -34],
            "shadowSize": [41, 41]
        } if marker_icon != 'default' else None

        markers = [
            dl.Marker(
                position=[row['latitude'], row['longitude']],
                icon=icon,
                children=[
                    dl.Tooltip(str(row['network_name'])),
                    dl.Popup(f"Network: {row['network_name']}<br>Location: {row['latitude']}, {row['longitude']}")
                ]
            ) for _, row in df.iterrows()
        ]
        return markers
    except Exception as e:
        return [], dcc.ConfirmDialog(
            id='confirm-danger',
            message=f'An error occurred: {e}',
        )

@app.callback(
    Output('coverages', 'children'),
    Output('rasters', 'children'),
    Input('upload-coverage', 'contents'),
    State('upload-coverage', 'filename'),
    prevent_initial_call=True
)
def update_coverages(coverages_contents, coverages_filenames):
    try:
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
    except Exception as e:
        return [], [], dcc.ConfirmDialog(
            id='confirm-danger',
            message=f'An error occurred: {e}',
        )

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

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    State('upload-csv', 'contents'),
    prevent_initial_call=True,
)
def download_csv(n_clicks, csv_contents):
    try:
        if not csv_contents:
            return

        content_type, content_string = csv_contents.split(',')
        decoded = io.BytesIO(base64.b64decode(content_string))
        df = pd.read_csv(decoded)

        # Perform spatial join
        points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
        coverages = []
        for file in os.listdir('app/data'):
            if file.endswith(('.kml', '.kmz', '.geojson', '.json', '.shp')):
                with open(os.path.join('app/data', file), 'rb') as f:
                    file_bytes = f.read()
                    ext = os.path.splitext(file)[1].lower()
                    if ext in ['.kml', '.kmz']:
                        gdf = kml_or_kmz_to_gdf(file_bytes, file)
                        coverages.append(gdf)
                    elif ext in ['.geojson', '.json']:
                        gdf = gpd.read_file(io.BytesIO(file_bytes))
                        coverages.append(gdf)
                    elif ext == '.shp':
                        with tempfile.TemporaryDirectory() as tmpdir:
                            with open(os.path.join(tmpdir, file), 'wb') as f:
                                f.write(file_bytes)
                            gdf = gpd.read_file(os.path.join(tmpdir, file))
                            coverages.append(gdf)
        if not coverages:
            return

        coverage = pd.concat(coverages, ignore_index=True)
        joined = gpd.sjoin(points, coverage, how="left", op='within')

        return dcc.send_data_frame(joined.to_csv, "coverage_analysis.csv")
    except Exception as e:
        return dcc.ConfirmDialog(
            id='confirm-danger',
            message=f'An error occurred: {e}',
        )

@app.callback(
    Output("download-dataframe-pdf", "data"),
    Input("btn_pdf", "n_clicks"),
    State('upload-csv', 'contents'),
    prevent_initial_call=True,
)
def download_pdf(n_clicks, csv_contents):
    try:
        if not csv_contents:
            return

        content_type, content_string = csv_contents.split(',')
        decoded = io.BytesIO(base64.b64decode(content_string))
        df = pd.read_csv(decoded)

        # Perform spatial join
        points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
        coverages = []
        for file in os.listdir('app/data'):
            if file.endswith(('.kml', '.kmz', '.geojson', '.json', '.shp')):
                with open(os.path.join('app/data', file), 'rb') as f:
                    file_bytes = f.read()
                    ext = os.path.splitext(file)[1].lower()
                    if ext in ['.kml', '.kmz']:
                        gdf = kml_or_kmz_to_gdf(file_bytes, file)
                        coverages.append(gdf)
                    elif ext in ['.geojson', '.json']:
                        gdf = gpd.read_file(io.BytesIO(file_bytes))
                        coverages.append(gdf)
                    elif ext == '.shp':
                        with tempfile.TemporaryDirectory() as tmpdir:
                            with open(os.path.join(tmpdir, file), 'wb') as f:
                                f.write(file_bytes)
                            gdf = gpd.read_file(os.path.join(tmpdir, file))
                            coverages.append(gdf)
        if not coverages:
            return

        coverage = pd.concat(coverages, ignore_index=True)
        joined = gpd.sjoin(points, coverage, how="left", op='within')

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Coverage Analysis", ln=1, align="C")
        for index, row in joined.iterrows():
            pdf.cell(200, 10, txt=f"Network: {row['network_name']}, Available: {'Yes' if row['index_right'] >= 0 else 'No'}", ln=1)

        return dcc.send_data_frame(pdf.output, "coverage_analysis.pdf")
    except Exception as e:
        return dcc.ConfirmDialog(
            id='confirm-danger',
            message=f'An error occurred: {e}',
        )

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
