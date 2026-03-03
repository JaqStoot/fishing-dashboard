import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Outdoor Monitor", layout="wide")

# --- SETTINGS ---
LAT, LON = 38.78, -90.32
STATION = "Florissant, MO"
RIVER_STATION = "07010000" # Mississippi River at St. Louis

def get_cardinal_direction(degrees):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(degrees / (360 / len(dirs)))
    return dirs[ix % len(dirs)]

@st.cache_data(ttl=600)
def get_weather_and_river():
    # 1. Weather & Pressure Forecast
    w_url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
             f"&current=temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,precipitation,cloud_cover"
             f"&hourly=surface_pressure&past_days=3&forecast_days=2"
             f"&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto")
    
    # 2. Astronomy (Sun/Moon)
    a_url = (f"https://api.open-meteo.com/v1/astronomy?latitude={LAT}&longitude={LON}"
             f"&daily=sunrise,sunset,moon_phase&timezone=auto")
    
    # 3. USGS River Gauge (Mississippi River)
    r_url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={RIVER_STATION}&parameterCd=00065&siteStatus=all"

    w_res = requests.get(w_url).json()
    a_res = requests.get(a_url).json()
    r_res = requests.get(r_url).json()

    return w_res, a_res, r_res

# Get Data
try:
    weather, astro, river = get_weather_and_river()
    cur = weather['current']
    
    # River level extraction
    river_stage = river['value']['timeSeries'][0]['values'][0]['value'][0]['value']
    
    # Pressure logic
    cur_inhg = round(cur['surface_pressure'] * 0.02953, 2)
    past_inhg = round(weather['hourly']['surface_pressure'][-6] * 0.02953, 2)
    trend = round(cur_inhg - past_inhg, 3)

except Exception as e:
    st.error(f"Data Fetch Error: {e}")
    st.stop()

st.title(f"🎣 {STATION} Fishing Dashboard")

# --- TOP ROW: PRIMARY CONDITIONS ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Temp", f"{round(cur['temperature_2m'])}°F")
with c2:
    st.metric("Barometer", f"{cur_inhg} inHg", delta=f"{trend} (6h)")
with c3:
    wind_dir = get_cardinal_direction(cur['wind_direction_10m'])
    st.metric("Wind", f"{round(cur['wind_speed_10m'])} mph", f"{wind_dir}")
with c4:
    st.metric("River Stage", f"{river_stage} ft", help="Mississippi River at St. Louis")

# --- PRESSURE ALERT ---
if trend <= -0.02:
    st.error("📉 **BAROMETER DROPPING:** Prime feeding window active!")
elif trend >= 0.02:
    st.success("📈 **BAROMETER RISING:** Post-front conditions. Slow down your presentation.")
else:
    st.info("⚖️ **STABLE PRESSURE:** Standard patterns apply.")

# --- MIDDLE ROW: THE TREND ---
st.subheader("5-Day Barometric Trend")
hourly_df = pd.DataFrame({
    'Time': pd.to_datetime(weather['hourly']['time']),
    'inHg': [p * 0.02953 for p in weather['hourly']['surface_pressure']]
})
st.area_chart(hourly_df.set_index('Time'), y="inHg")

# --- BOTTOM ROW: ENVIRONMENTAL ---
st.divider()
ec1, ec2, ec3 = st.columns(3)

# Moon Phase Logic
moon_val = astro['daily']['moon_phase'][0]
if moon_val == 0: phase = "New Moon"
elif moon_val < 0.25: phase = "Waxing Crescent"
elif moon_val == 0.25: phase = "First Quarter"
elif moon_val < 0.5: phase = "Waxing Gibbous"
elif moon_val == 0.5: phase = "Full Moon"
elif moon_val < 0.75: phase = "Waning Gibbous"
elif moon_val == 0.75: phase = "Last Quarter"
else: phase = "Waning Crescent"

with ec1:
    st.write(f"☀️ **Sunrise:** {astro['daily']['sunrise'][0].split('T')[1]}")
    st.write(f"🌙 **Sunset:** {astro['daily']['sunset'][0].split('T')[1]}")

with ec2:
    st.write(f"🌑 **Moon Phase:** {phase}")
    st.write(f"☁️ **Cloud Cover:** {cur['cloud_cover']}%")

with ec3:
    st.metric("Precipitation", f"{cur['precipitation']} in")