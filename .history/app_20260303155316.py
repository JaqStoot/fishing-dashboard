import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Outdoor Monitor", layout="wide")

st.title("Fishing & Outdoor Dashboard")
st.subheader("Real-Time Debian Desktop Monitor")

# Coordinates -- logic for finding by zip later
LAT = 38.797
LON = -90.298

def get_weather():
	url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m&hourly=temperature_2m,surface_pressure&forecast_days=1"
	response = requests.get(url)
	return response.json()

data = get_weather()
current = data['current']

# Create dashboard layout
col1, col2, col3, col4 = st.columns(4)

with col1:
	st.metric("Temperature", f"{currentwith col1:
    st.metric("Temperature", f"{current['temperature_2m']}°C")
with col2:
    # Pressure is huge for fishing!
    st.metric("Pressure", f"{current['surface_pressure']} hPa")
with col3:
    st.metric("Wind Speed", f"{current['wind_speed_10m']} km/h")
with col4:
    st.metric("Wind Dir", f"{current['wind_direction_10m']}°")

# Simple pressure trend chart
st.write("### 24-Hour Pressure Trend")
pressure_df = pd.DataFrame({
	'Time': data['hourly']['time'],
	'Pressure': data['hourly']['surface_pressure']
})
st.line_chart(pressure_df.set_index('Time'))
