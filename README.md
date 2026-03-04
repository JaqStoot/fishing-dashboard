# Fishing Dashboard

A Streamlit-based monitoring application providing real-time weather, barometric trends, and river conditions for any coordinate location

## Overview

This tool aggregates data from the Open-Meteo API and USGS Water Services to provide anglers with a "Bite Score" based on atmospheric pressure trends, wind conditions, and lunar phases. The application is structured with a functional separation between the Data Access Layer (WeatherService) and the Presentation Layer (Streamlit UI).

## Technical Stack

* Language: Python 3.11+
* Framework: Streamlit
* Data Handling: Pandas, Requests
* Data Sources:
    * Open-Meteo Forecast API
    * USGS National Water Information System (NWIS)
