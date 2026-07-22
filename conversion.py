'''
Converts PM2.5 concentrations into cigarette-equivalent exposure using the Berkeley Earth
methodology (22 ug/m3 of PM2.5 over 24h ~= 1 cigarette), for fire, non-fire, total, and
daily-max PM2.5.
'''

from data import firePM25, nonfirePM25, totalPM25, firePM25_dailymax

# Berkeley Earth methodology: 22 ug/m3 of PM2.5 over 24h ~= 1 cigarette.
PM25_PER_CIGARETTE = 22
DAYS_PER_YEAR = 365

cigarette_conversion_fire = (firePM25 / PM25_PER_CIGARETTE) * DAYS_PER_YEAR
cigarette_conversion_nonfire = (nonfirePM25 / PM25_PER_CIGARETTE) * DAYS_PER_YEAR
cigarette_conversion_total = (totalPM25 / PM25_PER_CIGARETTE) * DAYS_PER_YEAR
cigarette_conversion_dailymax = firePM25_dailymax / PM25_PER_CIGARETTE