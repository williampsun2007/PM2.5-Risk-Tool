'''
Entrypoint: creates the Dash app, wires up the layout and callbacks, and starts the server.
'''

from dash import Dash
import dash_bootstrap_components as dbc

from data import counties_df, fips
from layout import build_layout
from callbacks import register_callbacks

app = Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP])
server = app.server

app.layout = build_layout(counties_df, fips)
register_callbacks(app, fips)

if __name__ == '__main__':
    app.run(debug = False)