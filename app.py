import streamlit as st
import altair as alt
from engine import get_fishing_data, get_coords_by_zip
# 1. Page Configuration
st.set_page_config(
    page_title="Fishing Dashboard",
    layout="wide"
)
# 2. State Management (The "Session Bean")
# This block only runs once when the user first opens the app
if "location" not in st.session_state:
    if "last_location" in st.session_state:
        st.session_state.location = st.session_state.last_location
    else:
        st.session_state.location = {
            "lat": None,
            "lon": None,
            "name": "No Location History"
        }
# 3. Sidebar Input Logic
with st.sidebar:
    st.header("Location Settings")
    zip_input = st.text_input("Enter ZIP Code", placeholder="63031")
    if st.button("Update Dashboard"):
        if zip_input:
            with st.spinner("Geocoding..."):
                new_loc = get_coords_by_zip(zip_input)
            if new_loc:
                # update session state
                st.session_state.location = new_loc
                st.session_state.last_location = new_loc  # cache new location
                # clear cache to force fresh data pull for new location
                st.cache_data.clear()
            else:
                st.error("ZIP code not found.")
# 4. Data Fetching
@st.cache_data(ttl=600)
def load_dashboard_data(lat: float, lon: float):
    return get_fishing_data(lat, lon)
# Always pull coordinates from the session state
loc = st.session_state.location
report = load_dashboard_data(loc["lat"], loc["lon"])
if not report:
    st.error("Critical Error: Unable to retrieve fishing data.")
    st.stop()
# 5. UI Layout (Dynamic Title)
st.title(f"Fishing Dashboard: {loc['name']}")
# --- Rest of your UI remains exactly the same ---
score_col, msg_col = st.columns([1, 3])
with score_col:
    st.metric("Bite Score", f"{report.bite_score}/100")
with msg_col:
    if report.bite_score > 70:
        st.success("OPTIMAL: Barometric pressure and conditions are perfect for activity.")
    elif report.bite_score > 40:
        st.warning("MODERATE: Fish should be active, but expect a steady bite.")
    else:
        st.error("TOUGH: High pressure or shifting winds may slow the bite.")
st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Temperature", f"{round(report.temperature)}°F")
m2.metric("Barometer", f"{report.pressure_inhg} inHg", delta=f"{report.trend} (6h)")
m3.metric("Wind Speed", f"{round(report.wind_speed)} mph", f"Direction: {report.wind_dir}")
m4.metric("River Stage", f"{report.river_stage} ft")
st.subheader("Barometric Pressure Trend")
pressure_chart = alt.Chart(report.hourly_df).mark_line().encode(
    x=alt.X('Time', title='Date / Time', sort=None),
    y=alt.Y('inHg', title='inHg', scale=alt.Scale(domain=[28, 32]))
).properties(height=300)
st.altair_chart(pressure_chart, use_container_width=True)
st.divider()
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown(f"**Sunrise:** {report.sunrise}")
    st.markdown(f"**Sunset:** {report.sunset}")
with f2:
    st.markdown(f"**Moon Phase:** {report.moon_phase}")
    st.markdown(f"**Cloud Cover:** {report.cloud_cover}%")
with f3:
    st.metric("Precipitation", f"{report.precip} in")