import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Outdoor Monitor", layout="wide")

# --- SETTINGS ---
LAT, LON = 38.78, -90.32
STATION = "Florissant, MO"
RIVER_STATION = "07010000" 

def get_cardinal_direction(degrees):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(degrees / (360 / len(dirs)))
    return dirs[ix % len(dirs)]

@st.cache_data(ttl=600)
def get_all_data():
    # 1. Forecast API (Atmospheric data only)
    w_url = (f"https://api.open-meteo.com/v1/forecast?"
             f"latitude={LAT}&longitude={LON}"
             f"&current=temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,precipitation,cloud_cover"
             f"&hourly=surface_pressure"
             f"&past_days=3&forecast_days=2"
             f"&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FChicago")
    
    # 2. Astronomy API (Sun and Moon data)
    a_url = (f"https://api.open-meteo.com/v1/astronomy?"
             f"latitude={LAT}&longitude={LON}"
             f"&daily=sunrise,sunset,moon_phase"
             f"&timezone=America%2FChicago")
    
    # 3. USGS River Gauge
    r_url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={RIVER_STATION}&parameterCd=00065"

    try:
        w_res = requests.get(w_url).json()
        a_res = requests.get(a_url).json()
        r_res = requests.get(r_url).json()
        return w_res, a_res, r_res
    except Exception:
        return None, None, None

weather, astro, river = get_all_data()

if not weather or 'current' not in weather:
    st.error("Weather data fetch failed. The Forecast API may be temporarily down.")
    st.stop()

# --- DATA EXTRACTION ---
cur = weather['current']
cur_inhg = round(cur['surface_pressure'] * 0.02953, 2)
past_inhg = round(weather['hourly']['surface_pressure'][-6] * 0.02953, 2)
trend = round(cur_inhg - past_inhg, 3)

river_stage = "Unavailable"
try:
    river_stage = river['value']['timeSeries'][0]['values'][0]['value'][0]['value']
except:
    pass

# --- BITE SCORE LOGIC ---
bite_score = 50 
if trend < -0.01: bite_score += 30
if trend > 0.01: bite_score -= 20
if cur['wind_speed_10m'] < 10: bite_score += 10
if cur['cloud_cover'] > 50: bite_score += 10
bite_score = max(0, min(100, bite_score))

# --- UI DISPLAY ---
st.title(f"{STATION} Fishing Dashboard")

score_col1, score_col2 = st.columns([1, 3])
with score_col1:
    st.metric("Bite Score", f"{bite_score}/100")
with score_col2:
    if bite_score > 70: 
        st.success("CRITICAL: Optimal conditions for activity.")
    elif bite_score > 40: 
        st.warning("MODERATE: Average conditions. Monitor barometer for shifts.")
    else: 
        st.error("TOUGH: Low activity predicted. Focus on deep cover.")

st.divider()

c1, c2, c3, c4 = st.columns(4)
with c1: 
    st.metric("Temperature", f"{round(cur['temperature_2m'])} F")
with c2: 
    st.metric("Barometer", f"{cur_inhg} inHg", delta=f"{trend} (6h)")
with c3: 
    wind_dir = get_cardinal_direction(cur['wind_direction_10m'])
    st.metric("Wind", f"{round(cur['wind_speed_10m'])} mph", f"Bearing: {wind_dir}")
with c4: 
    st.metric("River Stage", f"{river_stage} ft")

st.subheader("Barometric Trend")
hourly_df = pd.DataFrame({
    'Time': pd.to_datetime(weather['hourly']['time']),
    'inHg': [p * 0.02953 for p in weather['hourly']['surface_pressure']]
})
st.area_chart(hourly_df.set_index('Time'), y="inHg")

st.divider()
st.subheader("Environmental Factors")
ec1, ec2, ec3 = st.columns(3)

# Astronomy handling from the correct endpoint
if astro and 'daily' in astro:
    # Astronomy API typically returns a list starting from the current day
    sunrise = astro['daily']['sunrise'][0].split('T')[1]
    sunset = astro['daily']['sunset'][0].split('T')[1]
    moon_val = astro['daily']['moon_phase'][0]
    
    if moon_val == 0 or moon_val == 1: phase = "New Moon"
    elif 0 < moon_val < 0.25: phase = "Waxing Crescent"
    elif moon_val == 0.25: phase = "First Quarter"
    elif 0.25 < moon_val < 0.5: phase = "Waxing Gibbous"
    elif moon_val == 0.5: phase = "Full Moon"
    elif 0.5 < moon_val < 0.75: phase = "Waning Gibbous"
    elif moon_val == 0.75: phase = "Last Quarter"
    else: phase = "Waning Crescent"

    with ec1:
        st.write(f"Sunrise: {sunrise}")
        st.write(f"Sunset: {sunset}")
    with ec2:
        st.write(f"Moon Phase: {phase}")
        st.write(f"Cloud Cover: {cur['cloud_cover']}%")
    with ec3:
        st.metric("Precipitation", f"{cur['precipitation']} in")
else:
    st.write("Astronomy data currently unavailable from the API.")