from dash import dcc, html
import dash_leaflet as dl
import dash_uploader as du
import dash_bootstrap_components as dbc
from app.utils.kml_to_geojson import kml_or_kmz_to_gdf

layout = dbc.Container([
    dcc.Store(id='dataframe-store'),
    dcc.Store(id='coverage-store'),
    html.H1("LoRa Network Visualizer"),
    dbc.Row([
        dbc.Col([
            html.Div(du.Upload(id='upload-csv', text='Upload CSV'), className='upload'),
            html.Div(du.Upload(id='upload-coverage', text='Upload Coverage File'), className='upload'),
            dcc.Dropdown(id='network-filter', placeholder="Filter by network"),
            html.Div(id='stats-section'),
            html.Button("Download Results", id="download-button", disabled=True),
            dcc.Download(id="download-dataframe-csv"),
        ], width=4),
        dbc.Col([
            dl.Map(id='map', center=[46.5, 2.5], zoom=6,
                   children=[dl.TileLayer(), dl.LayerGroup(id='markers')],
                   style={'width': '100%', 'height': '80vh'})
        ], width=8)
    ]),
], fluid=True)
