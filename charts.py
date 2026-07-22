import plotly.graph_objects as go
from conversion import DAYS_PER_YEAR

def no_data_figure(title):
    fig = go.Figure()
    fig.update_layout(title = title, xaxis = {'visible': False}, yaxis = {'visible': False},
                       paper_bgcolor = '#f8f5f0', plot_bgcolor = '#f8f5f0')
    fig.add_annotation(text = "No air quality data available for this county",
                        showarrow = False, font = dict(size = 16, color = "gray"),
                        xref = "paper", yref = "paper", x = 0.5, y = 0.5)
    return fig

def build_annual_chart(years, nonfire_series, fire_series, threshold):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x = years, y = nonfire_series, line = dict(color = "#457b9d", width = 2),
                              stackgroup = 'one', name = "Non-Fire", visible = True))
    fig.add_trace(go.Scatter(x = years, y = fire_series, line = dict(color = "#e76f51", width = 2),
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
    return fig

def build_dailymax_chart(years, dailymax_series, threshold):
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x = years, y = dailymax_series, name = "Daily Max Fire", marker_color = "#e76f51"))
    fig_bar.add_hline(y = threshold / DAYS_PER_YEAR, line_dash = "dash", line_color = "black")
    fig_bar.update_layout(
        title = "Worst Single-Day Wildfire Smoke Exposure Per Year",
        xaxis_title = "Year",
        yaxis_title = "Cigarettes in a Single Day",
        xaxis = dict(range = [2005.5, 2024]),
        paper_bgcolor = '#f8f5f0',
        plot_bgcolor = '#f8f5f0'
    )
    return fig_bar