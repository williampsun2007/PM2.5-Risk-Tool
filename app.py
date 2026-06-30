import xarray as xr
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd

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

state_names = {
    1:'Alabama', 2:'Alaska', 4:'Arizona', 5:'Arkansas', 6:'California',
    8:'Colorado', 9:'Connecticut', 10:'Delaware', 11:'District of Columbia',
    12:'Florida', 13:'Georgia', 15:'Hawaii', 16:'Idaho', 17:'Illinois',
    18:'Indiana', 19:'Iowa', 20:'Kansas', 21:'Kentucky', 22:'Louisiana',
    23:'Maine', 24:'Maryland', 25:'Massachusetts', 26:'Michigan', 27:'Minnesota',
    28:'Mississippi', 29:'Missouri', 30:'Montana', 31:'Nebraska', 32:'Nevada',
    33:'New Hampshire', 34:'New Jersey', 35:'New Mexico', 36:'New York',
    37:'North Carolina', 38:'North Dakota', 39:'Ohio', 40:'Oklahoma',
    41:'Oregon', 42:'Pennsylvania', 44:'Rhode Island', 45:'South Carolina',
    46:'South Dakota', 47:'Tennessee', 48:'Texas', 49:'Utah', 50:'Vermont',
    51:'Virginia', 53:'Washington', 54:'West Virginia', 55:'Wisconsin', 56:'Wyoming'
}

app = Dash(__name__)

state_data_fire = {}
state_data_nonfire = {}
for state_id in state_names.keys():
    county_indices = [i for i, f in enumerate(fips) if f // 1000 == state_id and f % 1000 != 0]
    if county_indices:
        state_data_fire[state_id] = np.nanmean(cigarette_conversion_fire[:, county_indices], axis = 1)
        state_data_nonfire[state_id] = np.nanmean(cigarette_conversion_nonfire[:, county_indices], axis = 1)

for state_id in state_names.keys():
    idx = fips.tolist().index(state_id * 1000)
    cigarette_conversion_fire[:, idx] = state_data_fire[state_id]
    cigarette_conversion_nonfire[:, idx] = state_data_nonfire[state_id]
    cigarette_conversion_total[:, idx] = state_data_fire[state_id] + state_data_nonfire[state_id]
    
state_data_max = {}
for state_id in state_names.keys():
     county_indices = [i for i, f in enumerate(fips) if f // 1000 == state_id and f % 1000 != 0]
     if county_indices:
         state_data_max[state_id] = np.nanmax(cigarette_conversion_dailymax[:, county_indices], axis = 1)
         
for state_id in state_names.keys():
    idx = fips.tolist().index(state_id * 1000)
    cigarette_conversion_dailymax[:, idx] = state_data_max[state_id]
    
app.layout = html.Div([
    html.H1("PM2.5 Exposure Risk Tool"),
    html.P("Note: Missing visual lines/bars may indicate years where data is unavailable for the selected county/state.", 
       style = {'font-size': '12px', 'color': 'gray'}),
    dcc.Dropdown(id = 'county-dropdown', options = [
        {'label': f"{row['name']}, {row['state']}", 'value': int(row['fips'])}
        for _, row in counties_df.iterrows() if int(row['fips']) in fips.tolist()
    ] + [{'label': name, 'value': int(id * 1000)} for id, name in state_names.items()]),
    dcc.Slider(id = 'threshold-slider', min = 0, max = 750, step = 1, value = 150, 
               marks = {0: '0', 100: '100', 200: '200', 300: '300', 400: '400', 500: '500'}),
    dcc.Graph(id = 'main-chart'),
    dcc.Graph(id = 'bar-daily'),
    html.P(id = 'summary-text'),
    html.Hr(),
    html.P([
        "Air pollution exposure is converted to cigarette equivalents using the ",
        html.A("Berkeley Earth methodology", href = "https://berkeleyearth.org/air-pollution-and-cigarette-equivalence/", target = "_blank"),
        ", which estimates that breathing air with 22 µg/m³ of PM2.5 for one day is roughly equivalent to smoking one cigarette."
    ]),
    html.P("Annual exposure: (PM2.5 µg/m³ ÷ 22) × 365 = cigarettes/year"),
    html.P("Daily exposure: PM2.5 µg/m³ ÷ 22 = cigarettes/day")
])


@callback(
    Output('main-chart', 'figure'),
    Output('bar-daily', 'figure'),
    Output('summary-text', 'children'),
    Input('county-dropdown', 'value'),
    Input('threshold-slider', 'value')
)
def update_chart(selected_fips, threshold):
    if selected_fips is None:
        return go.Figure(), go.Figure(), ""
    
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
    
    return fig, fig_bar, [html.P(f"In {num_years_above_threshold} out of 18 years from 2006 - 2023, the county/state exceeded your threshold of {threshold} cigarettes/year"),
                          html.P(f"Your worst year was {max_year} at {max_cigarette} cigarettes"),
                          html.P(summary_2023),
                          html.P(f"Wildfire smoke accounted for {pct_wildfire}% of your total exposure in 2023"),
                          html.P(f"Over 2006-2023, you accumulated {round(float(cumulative_above_threshold), 2)} excess cigarettes above your threshold of {threshold} cigarettes/year.")]

if __name__ == '__main__':
    app.run(debug = False)