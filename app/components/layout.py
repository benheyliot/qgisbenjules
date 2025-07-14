from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl

def serve_layout(static_overlays):
    return dbc.Container([
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
                               [dl.Overlay(dl.LayerGroup(id='rasters'), name="Rasters", checked=True)] +
                               [dl.Overlay(dl.LayerGroup(children=static_overlays), name="Static Overlays", checked=True)]
                           )
                       ])
            ], width=9)
        ])
    ], fluid=True)
