import xarray as xr
import pandas as pd

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