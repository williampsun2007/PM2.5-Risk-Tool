# PM2.5 Risk Tool

This tool converts historical PM2.5 (fine particulate) air pollution data for U.S. counties into an equivalent number of cigarettes smoked.

Pick a county, set a personal tolerance threshold, and get a visual breakdown of 18 years (2006–2023) of exposure, split between everyday ("non-fire") pollution and wildfire smoke.

## What it does

- **Select any U.S. county** with recorded data and see its full 2006–2023 PM2.5 exposure history.
- **Set a personal threshold** (in cigarettes/year) to compare against — the tool tells you how many of the last 18 years exceeded it.
- **See the wildfire vs. everyday-pollution split.** Each year's exposure is broken into smoke from wildfires ("fire") and all other PM2.5 sources ("non-fire"), stacked so you can see which one is driving your county's numbers.
- **Check worst-case single-day exposure.** A separate chart shows the single worst day of wildfire smoke each year, converted to cigarettes.
- **Get a plain-language risk summary**, color-coded green/yellow/red, covering:
  - how many of the 18 years exceeded your threshold
  - your county's single worst year on record
  - your most recent (2023) exposure, above or below threshold
  - what share of 2023's exposure came from wildfire smoke specifically
  - your cumulative "excess" exposure (in cigarettes) across every year you were over threshold

Counties with no recorded air quality data are handled gracefully — you'll see a clear "no data available" message instead of a broken or misleading chart.

## How it works

Exposure is converted to cigarette-equivalents using the **[Berkeley Earth methodology](https://berkeleyearth.org/air-pollution-and-cigarette-equivalence/)**, which estimates that breathing air containing 22 µg/m³ of PM2.5 for 24 hours is roughly equivalent to smoking one cigarette:

```
Annual exposure (cigarettes/year) = (PM2.5 µg/m³ ÷ 22) × 365
Daily exposure (cigarettes/day)   =  PM2.5 µg/m³ ÷ 22
```

This conversion is applied separately to fire-attributable PM2.5, non-fire PM2.5, and total PM2.5, for both the annual-average dataset and a daily-maximum dataset (used for the "worst single day" chart).

## Tech stack

- **[Dash](https://dash.plotly.com/)** + **[Plotly](https://plotly.com/python/)** for the interactive web UI and charts
- **[dash-bootstrap-components](https://dash-bootstrap-components.opensource.faculty.ai/)** for layout/styling
- **[xarray](https://xarray.dev/)** + **netCDF4** for reading the county-level `.nc` climate/air-quality datasets
- **pandas** / **numpy** for data wrangling
- **Gunicorn** + **Docker** for production deployment

## Data

The app reads three files from `data/`:

| File | Contents |
|---|---|
| `PM25_county_2006_2023.nc` | Annual fire / non-fire / total PM2.5 by county, 2006–2023 |
| `PM25_county_dailymax_2006_2023.nc` | Annual worst-single-day fire PM2.5 by county, 2006–2023 |
| `county_fips.csv` | FIPS code → county/state name lookup (the `.nc` files only index by FIPS) |

## Project structure

```
.
├── app.py                  # Dash app: layout, callbacks, and chart logic
├── data/                    # County-level PM2.5 datasets (see above)
├── assets/                  # Static assets (styling, images)
├── requirements.txt
├── Dockerfile
└── .github/workflows/       # CI/deployment automation
```

## Acknowledgments

- Cigarette-equivalence methodology: [Berkeley Earth](https://berkeleyearth.org/air-pollution-and-cigarette-equivalence/)
