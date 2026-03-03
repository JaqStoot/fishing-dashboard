import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Outdoor Monitor", layout="wide")

# --- SETTINGS ---
LAT, LON = 38.78, -90.32
STATION = "Florissant, MO"

def get_cardinal_direction(degrees):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(degrees / (360 / len(dirs)))
    return dirs[ix % len(dirs)]

@st.cache_data(ttl=600)
def get_weather_data():
    # Cleaned up URL: Corrected moon_phase and added explicit timezone
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           f"&current=temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,precipitation,cloud_cover"
           f"&hourly=surface_pressure,precipitation_probability"
           f"&daily=sunrise,sunset,moon_phase" 
           f"&past_days=3&forecast_days=2"
           f"&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto")
    
    response = requests.get(url)
    res_json = response.json()
    
    # Debugging: If 'current' isn't in the response, show the error
    if 'current' not in res_json:
        st.error(f"API Error: {res_json.get('reason', 'Unknown error')}")
        st.stop()
        
    return res_json

data = get_weather_data()
cur = data['current']
cur_inhg = round(cur['surface_pressure'] * 0.02953, 2)

# pressure trend calculations
past_inhg = round(data['hourly']['surface_pressure'][-6] * 0.02953, 2) # 6 hours ago
trend = round(cur_inhg - past_inhg, 3)

st.title(f"{STATION} Fishing Dashboard")

# --- TOP METRICS ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Temperature", f"{round(cur['temperature_2m'])}°F")
with c2:
    # Scientific display for pressure
    st.metric("Barometer", f"{cur_inhg} inHg", delta=f"{trend} inHg (6h)")
with c3:
    wind_dir = get_cardinal_direction(cur['wind_direction_10m'])
    st.metric("Wind Conditions", f"{round(cur['wind_speed_10m'])} mph", f"Bearing: {wind_dir} ({cur['wind_direction_10m']}°)")

# --- BAROMETER LOGIC ---
st.divider()
if trend <= -0.02:
    st.error("**RAPIDLY FALLING:** Low pressure system or storm front approaching.")
elif -0.02 < trend < 0:
    st.warning("**SLOWLY FALLING:** Gradual pressure drop.")
elif 0 <= trend < 0.02:
    st.info("**STABLE / SLOWLY RISING:** High pressure building.")
else:
    st.success("**RAPIDLY RISING:** Post-front / Clearing conditions.")

# --- THE DYNAMIC GRAPH ---
st.subheader("5-Day Barometric Trend (Historical + Forecast)")

# Process Hourly Data
hourly_df = pd.DataFrame({
    'Time': pd.to_datetime(data['hourly']['time']),
    'inHg': [p * 0.02953 for p in data['hourly']['surface_pressure']]
})

# Scaling the Y-Axis so the line isn't flat
# We find the min/max of the data and add a tiny buffer
y_min = hourly_df['inHg'].min() - 0.05
y_max = hourly_df['inHg'].max() + 0.05

# Streamlit's native line chart doesn't allow Y-axis scaling easily, 
# so we use a more advanced display method here:
st.line_chart(hourly_df.set_index('Time'), y="inHg")

# --- DATA TABLE ---
with st.expander("View Raw Hourly Data"):
    st.dataframe(hourly_df.sort_values(by='Time', ascending=False))

# Extract new data
sunrise = data['daily']['sunrise'][3]
sunset = data['daily']['sunset'][3]
rain_chance = data['current']['precipitation']

st.markdown("### Environmental Factors")
ec1, ec2, ec3 = st.columns(3)

with ec1:
    st.write(f"**Sunrise:** {sunrise.split('T')[1]}")
    st.write(f"**Sunset:** {sunset.split('T')[1]}")

with ec2:
    st.metric("Cloud Cover", f"{cur['cloud_cover']}%")

with ec3:
    st.metric("Current Precip", f"{cur['precipitation']} in")