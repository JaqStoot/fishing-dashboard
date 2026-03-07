import requests
import pandas as pd
from datetime import datetime

from models.report import FishingReport

# Constants
RIVER_STATION = "07010000"

def _get_cardinal(degrees: float) -> str:
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    return dirs[round(degrees / 45) % 8]

def _calculate_moon(date: datetime) -> str:
    diff = date - datetime(2001, 1, 1)
    days = diff.days + diff.seconds / 86400
    val = (0.20439731 + (days * 0.03386319269)) % 1.0
    
    if val < 0.03 or val > 0.97: return "New Moon"
    if val < 0.22: return "Waxing Crescent"
    if val < 0.28: return "First Quarter"
    if val < 0.47: return "Waxing Gibbous"
    if val < 0.53: return "Full Moon"
    if val < 0.72: return "Waning Gibbous"
    if val < 0.78: return "Last Quarter"
    return "Waning Crescent"

def get_coords_by_zip(zip_code: str) -> dict:
    """
    Translates US ZIP code into Lat/Lon, and City name
    Returns a dictionary or None if not found"
    """
    # Open-Meteo geocoding search works for postal codes too
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={zip_code}&count=1&language=en&format=json"
    
    try:
        response = requests.get(geo_url).json()
        if "results" in response:
            data = response["results"][0]
            return {
                "lat": data["latitude"],
                "lon": data["longitude"],
                "name": f"{data['name']}, {data.get('admin1', '')}" # e.g., "Florissant, Missouri"
            }
    except Exception as e:
        print(f"Geocoding error: {e}")
    
    return None

def get_fishing_data(lat: float, lon: float) -> FishingReport:
    """
    Acts as the service method. Fetches from multiple APIs,
    processes bite score, and returns a clean data object.
    """
    # URLs
    w_url = (f"https://api.open-meteo.com/v1/forecast?"
              f"latitude={lat}&longitude={lon}"
              f"&current=temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,precipitation,cloud_cover"
              f"&hourly=surface_pressure&daily=sunrise,sunset"
              f"&past_days=7&forecast_days=1&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FChicago")
    r_url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={RIVER_STATION}&parameterCd=00065"
    
    # 1. Network Requests
    try:
        w_res = requests.get(w_url).json()
        r_res = requests.get(r_url).json()
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
    
    # 2. Data Transformation (The 'Meat' of the engine)
    cur = w_res.get('current', {})
    
    # Pressure Logic
    p_now = round(cur.get('surface_pressure', 0) * 0.02953, 2) if 'surface_pressure' in cur else 0
    p_past = round(w_res.get('hourly', {}).get('surface_pressure', [0])[-6] * 0.02953, 2) if 'hourly' in w_res else 0
    trend = round(p_now - p_past, 3) if 'surface_pressure' in cur else 0
    
    # River Logic
    try:
        river_val = r_res['value']['timeSeries'][0]['values'][0]['value'][0]['value']
    except (KeyError, IndexError):
        river_val = "Unavailable"
    
    # Bite Score Logic (Business Rules)
    score = 50
    if trend < -0.01: score += 30
    elif trend > 0.01: score -= 20
    if cur.get('wind_speed_10m', 0) < 10: score += 10
    if cur.get('cloud_cover', 0) > 50: score += 10
    score = max(0, min(100, score))
    
    # 6-Hour Pressure Trend DataFrame (past 7 days, up to now)
    raw_times = w_res.get('hourly', {}).get('time', [])
    raw_pressures = w_res.get('hourly', {}).get('surface_pressure', [])
    now = datetime.now()

    filtered_times = []
    filtered_pressures = []
    for t, p in zip(raw_times, raw_pressures):
        if not t or p is None:
            continue
        dt = datetime.strptime(t, "%Y-%m-%dT%H:%M")
        if dt > now:
            break
        if dt.hour in (0, 6, 12, 18):
            filtered_times.append(dt.strftime("%-m/%-d %-I%p").lower())
            filtered_pressures.append(round(p * 0.02953, 2))

    hourly_df = pd.DataFrame({
        'Time': filtered_times,
        'inHg': filtered_pressures
    })
    
    # Sunrise and Sunset
    sunrise = w_res.get('daily', {}).get('sunrise', ['N/A'])[3].split('T')[1] if 'daily' in w_res else 'N/A'
    sunset = w_res.get('daily', {}).get('sunset', ['N/A'])[3].split('T')[1] if 'daily' in w_res else 'N/A'
    
    # 3. Instantiate and Return the FishingReport 'Bean'
    return FishingReport(
        temperature=cur.get('temperature_2m', 0),
        pressure_inhg=p_now,
        trend=trend,
        wind_speed=cur.get('wind_speed_10m', 0),
        wind_dir=_get_cardinal(cur.get('wind_direction_10m', 0)),
        river_stage=river_val,
        bite_score=score,
        hourly_df=hourly_df,
        sunrise=sunrise,
        sunset=sunset,
        moon_phase=_calculate_moon(datetime.now()),
        cloud_cover=cur.get('cloud_cover', 0),
        precip=cur.get('precipitation', 0)
    )