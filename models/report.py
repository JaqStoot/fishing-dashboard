# models/report.py
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True) #frozen = immutable
class FishingReport:
    temperature: float
    pressure_inhg: float
    trend: float
    wind_speed: float
    wind_dir: str
    river_stage: str
    bite_score: int
    hourly_df: pd.DataFrame
    sunrise: str
    sunset: str
    moon_phase: str
    cloud_cover: int
    precip: float