import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Outdoor Monitor", layout="wide")

# Coordinates -- logic for finding by zip later
LAT = 38.797
LON = -90.298
STATION_NAME = "Florissant, MO"

st.title(f"{STATION_NAME} Fishing & Outdoor Dashboard")
st.subheader("Real-Time Debian Desktop Monitor")

def get_weather():
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           f"&current=temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m"
           f"&hourly=surface_pressure&temperature_unit=fahrenheit&wind_speed_unit=mph"
           f"&precipitation_unit=inch&forecast_days=1")
    response = requests.get(url)
    return response.json()

data = get_weather()
current = data['current']

# Convert hPa (default) to inHg (Inches of Mercury)
# Formula: hPa * 0.02953
current_inhg = round(current['surface_pressure'] * 0.02953, 2)

# Calculate Pressure Trend (Current vs 3 hours ago)
# This is the "WorldMonitor" style logic
past_pressure_hpa = data['hourly']['surface_pressure'][0] 
past_inhg = round(past_pressure_hpa * 0.02953, 2)
trend = round(current_inhg - past_inhg, 2)

# --- DASHBOARD UI ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Temperature", f"{round(current['temperature_2m'])}°F")

with col2:
    # Adding a 'delta' shows if the pressure is rising or falling
    st.metric("Barometer", f"{current_inhg} inHg", delta=f"{trend} inHg (past 3h)")

with col3:
    st.metric("Wind Speed", f"{round(current['wind_speed_10m'])} mph")

# --- FISHING LOGIC ---
st.divider()
if trend < -0.02:
    st.success("**PRESSURE DROPPING:** Fish are likely moving and feeding. Grab your gear!")
elif trend > 0.02:
    st.warning("**PRESSURE RISING:** Post-front conditions. Fish might be deep and lethargic.")
else:
    st.info("**STABLE PRESSURE:** Consistent patterns. Find the structure!")

# --- VISUAL TREND ---
st.write("### Barometric Trend (inHg)")
# Create a dataframe for the chart, converting all hourly hPa to inHg
hourly_inhg = [round(p * 0.02953, 2) for p in data['hourly']['surface_pressure']]
df = pd.DataFrame({
    'Time': data['hourly']['time'],
    'Pressure (inHg)': hourly_inhg
})
st.line_chart(df.set_index('Time'))