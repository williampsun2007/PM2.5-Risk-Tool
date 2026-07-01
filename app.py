import xarray as xr
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State, callback
import pandas as pd
import dash_bootstrap_components as dbc

url = "https://raw.githubusercontent.com/kjhealy/fips-codes/master/state_and_county_fips_master.csv"
counties_df = pd.read_csv(url)
counties_df = counties_df[counties_df['fips'] % 1000 != 0] 

data = xr.open_dataset("PM25_county_2006_2023.nc")
data_dailymax = xr.open_dataset("PM25_county_dailymax_2006_2023.nc")

fips = data['fips'].values
years = data['year'].values
firePM25 = data['firePM25'].values
nonfirePM25 = data['nonfirePM25'].values
totalPM25 = data['totalPM25'].values

firePM25_dailymax = data_dailymax['firePM25_dailymax'].values

cigarette_conversion_fire = (firePM25 / 22) * 365
cigarette_conversion_nonfire = (nonfirePM25 / 22) * 365
cigarette_conversion_total = (totalPM25 / 22) * 365

cigarette_conversion_dailymax = firePM25_dailymax / 22

app = Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP])
    
app.layout = dbc.Container([
    html.Div([
        html.H1("PM2.5 Exposure Risk Tool", className = "text-white fw-bold mt-4"),
        html.P("Explore how wildfire smoke and air pollution in your county compares to smoking cigarettes, from 2006 to 2023.", 
                className = "text-white mb-4")], 
                style = {'backgroundColor': '#2c3e50', 'padding': '30px', 'borderRadius': '8px', 'marginBottom': '20px'}),
    html.P("Note: Missing visual lines/bars may indicate years where data is unavailable for the selected county.", 
            style = {'font-size': '12px', 'color': 'gray'}),
    html.Label("Select County", className = "fw-bold mt-3"),
    dcc.Dropdown(id = 'county-dropdown', options = [
            {'label': f"{row['name']}, {row['state']}", 'value': int(row['fips'])}
            for _, row in counties_df.iterrows() if int(row['fips']) in fips.tolist()]),
    html.Label("Set Your Cigarette Tolerance Threshold (cigarettes/year)", className = "fw-bold mt-3"),
    dcc.Slider(id = 'threshold-slider', min = 0, max = 750, step = 1, value = 150, 
            marks = {0: '0', 100: '100', 200: '200', 300: '300', 400: '400', 500: '500'}),
    dbc.Button("Show My Risk Profile", id = "submit-button", n_clicks = 0, className = "mt-3", disabled = True),
    html.Div(id = "result-section", style = {"display": "none"}, children = [
        dbc.Row([
            dbc.Col([dcc.Graph(id = 'main-chart', style = {'height': '400px'})]),
            dbc.Col([dcc.Graph(id = 'bar-daily', style = {'height': '400px'})])
        ]),
        dbc.Card(dbc.CardBody(html.P(id = 'summary-text')), className = "mt-3"),
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
            ]), className = "mt-3", style = {'backgroundColor': '#f8f9fa'}
        )
    ])
], fluid = False)


@callback(
    Output('main-chart', 'figure'),
    Output('bar-daily', 'figure'),
    Output('result-section', 'style'),
    Output('submit-button', 'style'), 
    Output('submit-button', 'disabled'),
    Output('summary-text', 'children'),
    Input('county-dropdown', 'value'),
    Input('threshold-slider', 'value'),
    Input('submit-button', 'n_clicks')
)
def update_chart(selected_fips, threshold, n_clicks):
    if selected_fips is None:
        return go.Figure(), go.Figure(), {"display": "none"}, {"style": "block"}, True, ""
    elif n_clicks == 0:
        return go.Figure(), go.Figure(), {"display": "none"}, {"display": "block"}, False, ""
    
    fig = go.Figure()
    idx = fips.tolist().index(selected_fips)
    
    fig.add_trace(go.Scatter(x = years, y = cigarette_conversion_nonfire[:, idx], line = dict(color = "red", width = 2),
                         stackgroup = 'one', name = "Non-Fire", visible = True))
    fig.add_trace(go.Scatter(x = years, y = cigarette_conversion_fire[:, idx], line = dict(color = "blue", width = 2),
                         stackgroup = 'one', name = "Fire", visible = True))
    
    fig.add_hline(y = threshold, line_dash = "dash", line_color = "black")

    fig.update_layout(
        title = 'PM2.5 Cigarette Equivalent',
        xaxis_title = 'Year',
        yaxis_title = 'Number of Cigarettes',
        xaxis = dict(range = [2006, 2023])
    )
    
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(x = years, y = cigarette_conversion_dailymax[:, idx], name = "Daily Max Fire", 
                             marker_color = "orange", visible = True))
    
    fig_bar.add_hline(y = threshold / 365, line_dash = "dash", line_color = "black")
    
    fig_bar.update_layout(
        title = "PM2.5 Cigarette Daily Max Per Year",
        xaxis_title = "Year",
        yaxis_title = "Max Number of Cigarettes in a Single Day",
        xaxis = dict(range = [2005, 2024])
    )
    
    num_years_above_threshold = np.sum(cigarette_conversion_total[:, idx] >= threshold)
    
    worst_idx = np.argmax(cigarette_conversion_total[:, idx])
    max_year = int(years[worst_idx])
    max_cigarette = round(float(cigarette_conversion_total[worst_idx, idx]), 2)
            
    if cigarette_conversion_total[17, idx] >= threshold:
        summary_2023 = f"In 2023 your exposure was {round(float(cigarette_conversion_total[17, idx]), 2)} cigarettes - above your threshold"
    else:
        summary_2023 = f"In 2023 your exposure was {round(float(cigarette_conversion_total[17, idx]), 2)} cigarettes - below your threshold"
    
    pct_wildfire = round((float(cigarette_conversion_fire[17, idx] / cigarette_conversion_total[17, idx]) * 100), 2)
    
    cumulative_above_threshold = sum(cigarette_conversion_total[year - 2006, idx] - threshold for year in range(2006, 2024) 
                                     if cigarette_conversion_total[year - 2006, idx] > threshold)
    
    return fig, fig_bar, {"display": "block"}, {"display": "none"}, False, [html.H5("Your Exposure Summary", className = "card-title mb-3"),
        html.P(f"In {num_years_above_threshold} out of 18 years from 2006 - 2023, the county exceeded your threshold of {threshold} cigarettes/year"),
        html.P(f"Your worst year was {max_year} at {max_cigarette} cigarettes"),
        html.P(summary_2023),
        html.P(f"Wildfire smoke accounted for {pct_wildfire}% of your total exposure in 2023"),
        html.P(f"Over 2006-2023, you accumulated {round(float(cumulative_above_threshold), 2)} excess cigarettes above your threshold of {threshold} cigarettes/year.")],


if __name__ == '__main__':
    app.run(debug = True)