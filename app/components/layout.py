from dash import dcc, html
import dash_leaflet as dl
import dash_uploader as du
import dash_bootstrap_components as dbc

layout = dbc.Container([
    dcc.Store(id='dataframe-store'),
    html.H1("LoRa Network Visualizer"),
    dbc.Row([
        dbc.Col([
            html.Div(du.Upload(), className='upload'),
            dcc.Dropdown(id='network-filter', placeholder="Filter by network"),
            html.Div(id='stats-section')
        ], width=4),
        dbc.Col([
            dl.Map(id='map', center=[46.5, 2.5], zoom=6,
                   children=[dl.TileLayer(), dl.LayerGroup(id='markers')],
                   style={'width': '100%', 'height': '80vh'})
        ], width=8)
    ])
], fluid=True)
