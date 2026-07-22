from dash import html, dcc
import dash_bootstrap_components as dbc


def build_layout(counties_df, fips):
    return dbc.Container([
    html.Div([
        html.H1("How Healthy Is Your Air?", className = "text-white fw-bold mt-4"),
        html.P("Enter your county to see how local PM2.5 air pollution — from wildfires and everyday sources — compares to smoking cigarettes, from 2006 to 2023.", 
                className = "text-white mb-4")], 
        style = {'backgroundColor': '#2d6a4f', 'padding': '30px', 'borderRadius': '8px', 'marginBottom': '20px'}),
    html.P("Note: Missing visual lines/bars may indicate years where data is unavailable for the selected county.", 
            style = {'font-size': '12px', 'color': 'gray'}),
    html.Label("Select County", className = "fw-bold mt-3"),
    dcc.Dropdown(id = 'county-dropdown', options = [
            # Only list counties that actually have a row in the .nc data (fips is its index).
            {'label': f"{row['name']}, {row['state']}", 'value': int(row['fips'])}
            for _, row in counties_df.iterrows() if int(row['fips']) in fips.tolist()]),
    html.Label("Set Your Cigarette Tolerance Threshold (cigarettes/year)", className = "fw-bold mt-3"),
    dcc.Slider(id = 'threshold-slider', min = 0, max = 750, step = 1, value = 150, 
            marks = {0: '0', 100: '100', 200: '200', 300: '300', 400: '400', 500: '500'}),
    dbc.Button("Show My Air Quality Risk Profile", id = "submit-button", n_clicks = 0, className = "mt-3", 
                disabled = True, style = {'backgroundColor': '#52b788', 'border': 'none'}),
    html.Div(id = "result-section", style = {"display": "none"}, children = [
        dbc.Row([
            dbc.Col([dcc.Graph(id = 'main-chart', style = {'height': '500px'}, config = {'displayModeBar': False})], width = 6),
            dbc.Col([dcc.Graph(id = 'bar-daily', style = {'height': '500px'}, config = {'displayModeBar': False})], width = 6)
        ]),
        dbc.Card(dbc.CardBody(html.P(id = 'summary-text')), className = "mt-3", id = "summary-card"),
        html.Hr(),
        dbc.Card(
            dbc.CardBody([
                html.H5("About This Tool", className = "card-title"),
                html.P([
                    "Air pollution exposure is converted to cigarette equivalents using the ",
                    html.A("Berkeley Earth methodology", href = "https://berkeleyearth.org/air-pollution-and-cigarette-equivalence/", target="_blank"),
                    ", which estimates that breathing air with 22 µg/m³ of PM2.5 for one day is roughly equivalent to smoking one cigarette."
                ]),
                html.P("Annual exposure: (PM2.5 µg/m³ ÷ 22) × 365 = cigarettes/year"),
                html.P("Daily exposure: PM2.5 µg/m³ ÷ 22 = cigarettes/day")
            ]), className = "mt-3"
        ),
    ]),
    html.Footer([
        html.P("© 2026 PM2.5 Exposure Risk Tool",
        style = {'fontSize': '12px', 'color': 'gray', 'textAlign': 'center'})
    ], style = {'marginTop': '40px', 'paddingTop': '20px', 'borderTop': '1px solid #ddd'})
], fluid = False, style = {'backgroundColor': '#f8f5f0', 'minHeight': '100vh', 'padding': '20px'})