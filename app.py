import xarray as xr
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import dash_bootstrap_components as dbc

# County/state names for display — the .nc files below only have FIPS codes, not reliable names.
counties_df = pd.read_csv("data/county_fips.csv")
counties_df = counties_df[counties_df['fips'] % 1000 != 0]  # drop state-level summary rows (FIPS ending in 000)

data = xr.open_dataset("data/PM25_county_2006_2023.nc")
data_dailymax = xr.open_dataset("data/PM25_county_dailymax_2006_2023.nc")

# Pull everything into plain numpy arrays up front; the rest of the app indexes into these
# via fips.tolist().index(selected_fips) instead of touching the xarray Datasets again.
fips = data['fips'].values
years = data['year'].values
firePM25 = data['firePM25'].values
nonfirePM25 = data['nonfirePM25'].values
totalPM25 = data['totalPM25'].values

firePM25_dailymax = data_dailymax['firePM25_dailymax'].values

# Berkeley Earth methodology: 22 ug/m3 of PM2.5 over 24h ~= 1 cigarette.
cigarette_conversion_fire = (firePM25 / 22) * 365
cigarette_conversion_nonfire = (nonfirePM25 / 22) * 365
cigarette_conversion_total = (totalPM25 / 22) * 365

cigarette_conversion_dailymax = firePM25_dailymax / 22

# Placeholder chart shown for counties with no recorded data instead of plotting all-NaN values.
def _no_data_figure(title):
    fig = go.Figure()
    fig.update_layout(title = title, xaxis = {'visible': False}, yaxis = {'visible': False},
                       paper_bgcolor = '#f8f5f0', plot_bgcolor = '#f8f5f0')
    fig.add_annotation(text = "No air quality data available for this county",
                        showarrow = False, font = dict(size = 16, color = "gray"),
                        xref = "paper", yref = "paper", x = 0.5, y = 0.5)
    return fig

app = Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP])
server = app.server
    
app.layout = dbc.Container([
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


@callback(
    Output('main-chart', 'figure'),
    Output('bar-daily', 'figure'),
    Output('result-section', 'style'),
    Output('submit-button', 'style'), 
    Output('submit-button', 'disabled'),
    Output('summary-card', 'style'),
    Output('summary-text', 'children'),
    Input('county-dropdown', 'value'),
    Input('threshold-slider', 'value'),
    Input('submit-button', 'n_clicks')
)
def update_chart(selected_fips, threshold, n_clicks):
    if selected_fips is None:
        # No county picked yet: keep the button disabled and results hidden.
        return go.Figure(), go.Figure(), {"display": "none"}, {"display": "block"}, True, {"backgroundColor": "#f8f9fa"}, ""
    elif n_clicks == 0:
        # County picked but button not yet clicked: results stay hidden until the first reveal.
        return go.Figure(), go.Figure(), {"display": "none"}, {"display": "block"}, False, {"backgroundColor": "#f8f9fa"}, ""
    # After the first click the button permanently hides itself (see Output('submit-button', 'style')
    # below), so from here on this callback re-runs live on every county/threshold change.

    idx = fips.tolist().index(selected_fips)
    # Some counties (mostly Alaska) have all-NaN data in one or both datasets. Guard against that
    # here so np.argmax/np.sum below don't silently produce misleading stats (e.g. a "0 years
    # exceeded" green card) for a county that actually just has no data on record.
    annual_missing = bool(np.all(np.isnan(cigarette_conversion_total[:, idx])))
    dailymax_missing = bool(np.all(np.isnan(cigarette_conversion_dailymax[:, idx])))

    if annual_missing:
        fig = _no_data_figure('Annual Air Pollution Exposure (Cigarette Equivalent)')
    else:
        fig = go.Figure()

        fig.add_trace(go.Scatter(x = years, y = cigarette_conversion_nonfire[:, idx], line = dict(color = "#457b9d", width = 2),
                             stackgroup = 'one', name = "Non-Fire", visible = True))
        fig.add_trace(go.Scatter(x = years, y = cigarette_conversion_fire[:, idx], line = dict(color = "#e76f51", width = 2),
                             stackgroup = 'one', name = "Fire", visible = True))

        fig.add_hline(y = threshold, line_dash = "dash", line_color = "black")

        fig.update_layout(
            title = 'Annual Air Pollution Exposure (Cigarette Equivalent)',
            xaxis_title = 'Year',
            yaxis_title = 'Cigarettes per Year',
            xaxis = dict(range = [2006, 2023]),
            paper_bgcolor = '#f8f5f0',
            plot_bgcolor = '#f8f5f0'
        )

    if dailymax_missing:
        fig_bar = _no_data_figure("Worst Single-Day Wildfire Smoke Exposure Per Year")
    else:
        fig_bar = go.Figure()

        fig_bar.add_trace(go.Bar(x = years, y = cigarette_conversion_dailymax[:, idx],
                                 name = "Daily Max Fire", marker_color = "#e76f51"))

        fig_bar.add_hline(y = threshold / 365, line_dash = "dash", line_color = "black")

        fig_bar.update_layout(
            title = "Worst Single-Day Wildfire Smoke Exposure Per Year",
            xaxis_title = "Year",
            yaxis_title = "Cigarettes in a Single Day",
            xaxis = dict(range = [2005.5, 2024]),
            paper_bgcolor = '#f8f5f0',
            plot_bgcolor = '#f8f5f0'
        )

    if annual_missing:
        card_color = {"backgroundColor": "#e2e3e5"}
        summary_children = [
            html.H5("⚪ No Data Available"),
            html.P("Air quality data is not on record for this county, so no exposure summary can be calculated.")
        ]
    else:
        num_years_above_threshold = np.sum(cigarette_conversion_total[:, idx] >= threshold)
        # <=6/18 years over threshold = green, <=12 = yellow, otherwise red.
        if num_years_above_threshold <= 6:
            card_color = {'backgroundColor': '#d4edda'}
        elif num_years_above_threshold <= 12:
            card_color = {'backgroundColor': '#fff3cd'}
        else:
            card_color = {'backgroundColor': '#F0320C'}

        worst_idx = np.argmax(cigarette_conversion_total[:, idx])
        max_year = int(years[worst_idx])
        max_cigarette = round(float(cigarette_conversion_total[worst_idx, idx]), 2)

        # Index 17 = year 2023, relying on years always being 2006-2023 contiguous
        if cigarette_conversion_total[17, idx] >= threshold:
            summary_2023 = f"In 2023 your exposure was {round(float(cigarette_conversion_total[17, idx]), 2)} cigarettes - above your limit."
        else:
            summary_2023 = f"In 2023 your exposure was {round(float(cigarette_conversion_total[17, idx]), 2)} cigarettes - below your limit."

        pct_wildfire = round((float(cigarette_conversion_fire[17, idx] / cigarette_conversion_total[17, idx]) * 100), 2)

        cumulative_above_threshold = sum(cigarette_conversion_total[year - 2006, idx] - threshold for year in range(2006, 2024)
                                         if cigarette_conversion_total[year - 2006, idx] > threshold)

        summary_children = [html.H5(f"{'🟢' if num_years_above_threshold <= 6 else '🟡' if num_years_above_threshold <= 12 else '🔴'} Your Exposure Summary"),
            html.P(f"In {num_years_above_threshold} out of 18 years from 2006 - 2023, the county exceeded your threshold of {threshold} cigarettes/year.", style = {'fontWeight': 'bold'}),
            html.P(f"Your worst year was {max_year} - equivalent to smoking {max_cigarette} cigarettes that year just from breathing."),
            html.P(summary_2023),
            html.P(f"Wildfire smoke accounted for {pct_wildfire}% of your total exposure in 2023."),
            html.P(f"Over 18 years during 2006-2023, you breathed in {round(float(cumulative_above_threshold))} extra cigarettes worth of pollution above your limit of {threshold} cigarettes/year.")]

    return fig, fig_bar, {"display": "block"}, {"display": "none"}, False, card_color, summary_children


if __name__ == '__main__':
    app.run(debug = False)