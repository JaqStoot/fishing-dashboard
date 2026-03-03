import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import math

st.set_page_config(page_title="Outdoor Monitor", layout="wide")

# --- SETTINGS ---
LAT, LON = 38.78, -90.32
STATION = "Florissant, MO"
RIVER_STATION = "07010000" 

def get_cardinal_direction(degrees):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(degrees / (360 / len(dirs)))
    return dirs[ix % len(dirs)]

def calculate_moon_phase(date):
    """Fallback math for moon phase if API fails (0=New, 0.5=Full)"""
    diff = date - datetime(2001, 1, 1)
    days = diff.days + diff.seconds / 86400
    lunations = 0.20439731 + (days * 0.03386319269)
    return lunations % 1.0

@st.cache_data(ttl=600)
def get_all_data():
    # One call to rule them all: Forecast, Sun, and Moon combined
    w_url = (f"https://api.open-meteo.com/v1/forecast?"
             f"latitude={LAT}&longitude={LON}"
             f"&current=temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,precipitation,cloud_cover"
             f"&hourly=surface_pressure"
             f"&daily=sunrise,sunset" # Primary sunrise/sunset location
             f"&past_days=3&forecast_days=2"
             f"&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FChicago")
    
    r_url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={RIVER_STATION}&parameterCd=00065"

    try:
        w_res = requests.get(w_url).json()
        r_res = requests.get(r_url).json()
        return w_res, r_res
    except Exception:
        return None, None

weather, river = get_all_data()

if not weather or 'current' not in weather:
    st.error("Weather data fetch failed. Check connection.")
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

# --- BITE SCORE ---
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
    if bite_score > 70: st.success("CRITICAL: Optimal conditions.")
    elif bite_score > 40: st.warning("MODERATE: Average conditions.")
    else: st.error("TOUGH: Low activity predicted.")

st.divider()

# Primary Metrics
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Temperature", f"{round(cur['temperature_2m'])} F")
with c2: st.metric("Barometer", f"{cur_inhg} inHg", delta=f"{trend} (6h)")
with c3: st.metric("Wind", f"{round(cur['wind_speed_10m'])} mph", f"Bearing: {get_cardinal_direction(cur['wind_direction_10m'])}")
with c4: st.metric("River Stage", f"{river_stage} ft")

# The Trend Graph
st.subheader("Barometric Trend")
hourly_df = pd.DataFrame({
    'Time': pd.to_datetime(weather['hourly']['time']),
    'inHg': [p * 0.02953 for p in weather['hourly']['surface_pressure']]
})
st.area_chart(hourly_df.set_index('Time'), y="inHg")

st.divider()
st.subheader("Environmental Factors")
ec1, ec2, ec3 = st.columns(3)

if 'daily' in weather:
    # Index 3 is 'Today' when past_days=3 is used
    sunrise = weather['daily']['sunrise'][3].split('T')[1]
    sunset = weather['daily']['sunset'][3].split('T')[1]
    
    # Use calculated fallback for moon phase stability
    moon_val = calculate_moon_phase(datetime.now())
    
    if moon_val < 0.03 or moon_val > 0.97: phase = "New Moon"
    elif 0.03 <= moon_val < 0.22: phase = "Waxing Crescent"
    elif 0.22 <= moon_val < 0.28: phase = "First Quarter"
    elif 0.28 <= moon_val < 0.47: phase = "Waxing Gibbous"
    elif 0.47 <= moon_val < 0.53: phase = "Full Moon"
    elif 0.53 <= moon_val < 0.72: phase = "Waning Gibbous"
    elif 0.72 <= moon_val < 0.78: phase = "Last Quarter"
    else: phase = "Waning Crescent"

    with ec1:
        st.write(f"Sunrise: {sunrise}")
        st.write(f"Sunset: {sunset}")
    with ec2:
        st.write(f"Moon Phase: {phase}")
        st.write(f"Cloud Cover: {cur['cloud_cover']}%")
    with ec3:
        st.metric("Precipitation", f"{cur['precipitation']} in")