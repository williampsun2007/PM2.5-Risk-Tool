'''
Registers the app's single callback, which reacts to county/threshold/button changes and
computes the charts + color-coded exposure summary shown in the result section.
'''

import numpy as np
import plotly.graph_objects as go
from dash import html, Input, Output

from data import years
from conversion import cigarette_conversion_fire, cigarette_conversion_nonfire, cigarette_conversion_total, cigarette_conversion_dailymax
from charts import no_data_figure, build_annual_chart, build_dailymax_chart


def register_callbacks(app, fips):
    @app.callback(
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
            fig = no_data_figure('Annual Air Pollution Exposure (Cigarette Equivalent)')
        else:
            fig = build_annual_chart(years, cigarette_conversion_nonfire[:, idx], cigarette_conversion_fire[:, idx], threshold)

        if dailymax_missing:
            fig_bar = no_data_figure("Worst Single-Day Wildfire Smoke Exposure Per Year")
        else:
            fig_bar = build_dailymax_chart(years, cigarette_conversion_dailymax[:, idx], threshold)

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

    return update_chart