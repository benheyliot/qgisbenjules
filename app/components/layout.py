from dash import dcc, html
import dash_leaflet as dl
import dash_uploader as du
import dash_bootstrap_components as dbc
from dash_extensions.javascript import assign

layout = dbc.Container([
    dcc.Store(id='dataframe-store'),
    html.H1("LoRa Network Visualizer"),
    dbc.Row([
        dbc.Col([
            html.Div(du.Upload(), className='upload'),
            dcc.Dropdown(id='network-filter', placeholder="Filter by network"),
            html.Div(id='stats-section'),
            html.Button("Download Results", id="download-button", disabled=True),
            dcc.Download(id="download-dataframe-csv"),
            html.Div(id='table-container')
        ], width=4),
        dbc.Col([
            dl.Map(id='map', center=[46.5, 2.5], zoom=6,
                   children=[
                       dl.TileLayer(),
                       dl.LayersControl(
                           [dl.BaseLayer(dl.TileLayer(), name="OpenStreetMap", checked=True)] +
                           [dl.Overlay(dl.LayerGroup(id='markers'), name="Markers", checked=True)]
                       )
                   ],
                   style={'width': '100%', 'height': '80vh'})
        ], width=8)
    ]),
    dl.GeoJSON(url="/assets/search.js", id="search", format="geojson")
], fluid=True)
