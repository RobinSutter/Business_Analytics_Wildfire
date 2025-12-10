#!/usr/bin/env python3
"""
Merge wildfire data with temperature data by matching fires to nearest cities.

For each fire:
- Convert Julian dates to standard datetime
- Find cities within 150km; if none, use 5 nearest cities
- Match temperature records for date range (discovery to containment) - taking the mean value
- Export cleaned dataset with essential columns

Usage:
  uv run python src/merge_fire_temperature.py
  uv run python src/merge_fire_temperature.py --output data/processed/fires_with_temp.csv
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree


def parse_latlon(coord_str: str) -> float:
    """Parse lat/lon from format like '32.95N' or '100.53W' to decimal degrees."""
    if not isinstance(coord_str, str):
        return np.nan
    coord_str = coord_str.strip()
    if not coord_str:
        return np.nan
    
    # Extract direction and numeric part
    direction = coord_str[-1].upper()
    try:
        value = float(coord_str[:-1])
    except ValueError:
        return np.nan
    
    # Apply sign based on direction
    if direction in ('S', 'W'):
        value = -value
    
    return value


def haversine_distance(lat1: np.ndarray, lon1: np.ndarray, 
                       lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Calculate haversine distance in kilometers between coordinate pairs."""
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlon = np.radians(lon2 - lon1)
    dlat = np.radians(lat2 - lat1)
    
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return 6371.0 * c  # Earth radius in km


def julian_to_datetime(julian_day: float) -> datetime:
    """Convert Julian day number to datetime (Unix epoch: JD 2440587.5 = 1970-01-01)."""
    if pd.isna(julian_day):
        return pd.NaT
    unix_days = julian_day - 2440587.5
    return datetime(1970, 1, 1) + timedelta(days=unix_days)


def load_fires(db_path: str) -> pd.DataFrame:
    """Load Fires table and convert dates."""
    conn = sqlite3.connect(db_path)
    try:
        query = """
        SELECT 
            OBJECTID, FOD_ID, FIRE_NAME, FIRE_YEAR,
            DISCOVERY_DATE, DISCOVERY_DOY, CONT_DATE, CONT_DOY,
            STAT_CAUSE_CODE, STAT_CAUSE_DESCR,
            FIRE_SIZE, FIRE_SIZE_CLASS,
            LATITUDE, LONGITUDE,
            STATE, COUNTY, FIPS_CODE
        FROM Fires
        WHERE LATITUDE IS NOT NULL 
          AND LONGITUDE IS NOT NULL
          AND DISCOVERY_DATE IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    
    # Convert Julian dates
    df['discovery_date'] = df['DISCOVERY_DATE'].apply(julian_to_datetime)
    df['cont_date'] = df['CONT_DATE'].apply(julian_to_datetime)
    
    # Filter to valid date range (1992-2015 per dataset description)
    df = df[(df['discovery_date'].dt.year >= 1992) & (df['discovery_date'].dt.year <= 2015)].copy()
    
    return df


def load_temperatures(csv_path: str) -> pd.DataFrame:
    """Load US temperature data and parse coordinates."""
    df = pd.read_csv(csv_path)
    df['dt'] = pd.to_datetime(df['dt'])
    
    # Parse lat/lon from strings like '32.95N', '100.53W'
    df['lat_parsed'] = df['Latitude'].apply(parse_latlon)
    df['lon_parsed'] = df['Longitude'].apply(parse_latlon)
    
    # Drop rows with invalid coordinates
    df = df.dropna(subset=['lat_parsed', 'lon_parsed']).copy()
    
    # Filter to date range overlapping with fires (1992-2015)
    df = df[(df['dt'].dt.year >= 1992) & (df['dt'].dt.year <= 2015)].copy()
    
    return df


def build_city_index(temp_df: pd.DataFrame) -> tuple[pd.DataFrame, BallTree]:
    """Build spatial index for city lookups."""
    # Get unique cities with their coordinates
    cities = temp_df[['City', 'lat_parsed', 'lon_parsed']].drop_duplicates().reset_index(drop=True)
    
    # Build BallTree for efficient nearest-neighbor search (using haversine metric)
    coords_rad = np.radians(cities[['lat_parsed', 'lon_parsed']].values)
    tree = BallTree(coords_rad, metric='haversine')
    
    return cities, tree


def match_fire_to_cities(fire_lat: float, fire_lon: float, 
                         cities: pd.DataFrame, tree: BallTree,
                         radius_km: float = 150.0, 
                         fallback_k: int = 5) -> list[str]:
    """
    Find cities to use for temperature matching.
    
    Strategy:
    1. Find all cities within radius_km
    2. If none found, use fallback_k nearest cities
    """
    fire_coord_rad = np.radians([[fire_lat, fire_lon]])
    
    # Query within radius
    radius_rad = radius_km / 6371.0  # Convert km to radians
    indices = tree.query_radius(fire_coord_rad, r=radius_rad)[0]
    
    if len(indices) > 0:
        return cities.iloc[indices]['City'].tolist()
    
    # Fallback: get k nearest
    distances, indices = tree.query(fire_coord_rad, k=fallback_k)
    return cities.iloc[indices[0]]['City'].tolist()


def get_temperature_for_fire(fire_row: pd.Series, temp_df: pd.DataFrame,
                             cities: pd.DataFrame, tree: BallTree) -> dict:
    """
    Get temperature statistics for a fire by matching nearby cities.
    
    Returns dict with:
    - matched_cities: list of city names used
    - discovery_temp: temperature on discovery date
    - mean_temp: mean temperature from discovery to containment
    - max_temp: max temperature in period
    - min_temp: min temperature in period
    """
    fire_lat = fire_row['LATITUDE']
    fire_lon = fire_row['LONGITUDE']
    disc_date = fire_row['discovery_date']
    cont_date = fire_row['cont_date']
    
    # Find cities to use
    matched_cities = match_fire_to_cities(fire_lat, fire_lon, cities, tree)
    
    # Filter temperature data to matched cities
    city_temps = temp_df[temp_df['City'].isin(matched_cities)].copy()
    
    # Match on discovery date (monthly data, so match by year-month)
    disc_month = pd.Timestamp(disc_date.year, disc_date.month, 1)
    discovery_temps = city_temps[city_temps['dt'] == disc_month]
    
    result = {
        'matched_cities': ','.join(matched_cities),
        'num_cities': len(matched_cities),
        'discovery_temp': discovery_temps['AverageTemperature'].mean() if not discovery_temps.empty else np.nan,
    }
    
    # If containment date is valid, get temperature range
    if pd.notna(cont_date) and cont_date >= disc_date:
        # Get all months from discovery to containment
        start_month = disc_month
        end_month = pd.Timestamp(cont_date.year, cont_date.month, 1)
        
        period_temps = city_temps[
            (city_temps['dt'] >= start_month) & 
            (city_temps['dt'] <= end_month)
        ]
        
        if not period_temps.empty:
            result['mean_temp'] = period_temps['AverageTemperature'].mean()
            result['max_temp'] = period_temps['AverageTemperature'].max()
            result['min_temp'] = period_temps['AverageTemperature'].min()
            result['temp_range'] = result['max_temp'] - result['min_temp']
        else:
            result['mean_temp'] = result['discovery_temp']
            result['max_temp'] = result['discovery_temp']
            result['min_temp'] = result['discovery_temp']
            result['temp_range'] = 0.0
    else:
        # No containment date, use discovery temp for all
        result['mean_temp'] = result['discovery_temp']
        result['max_temp'] = result['discovery_temp']
        result['min_temp'] = result['discovery_temp']
        result['temp_range'] = 0.0
    
    return result


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge wildfire data with temperature data"
    )
    parser.add_argument(
        "--db",
        default="data/raw/FPA_FOD_20170508.sqlite",
        help="Path to wildfire SQLite database",
    )
    parser.add_argument(
        "--temp",
        default="data/processed/USTemperaturesByCity/USTemperaturesByCity.csv",
        help="Path to US temperatures CSV",
    )
    parser.add_argument(
        "--output",
        default="data/processed/fires_with_temperature.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of fires to process (for testing)",
    )
    
    args = parser.parse_args(argv)
    
    print("Loading wildfire data...")
    fires_df = load_fires(args.db)
    print(f"Loaded {len(fires_df):,} fire records (1992-2015)")
    
    if args.limit:
        fires_df = fires_df.head(args.limit)
        print(f"Limited to {len(fires_df):,} records for testing")
    
    print("\nLoading temperature data...")
    temp_df = load_temperatures(args.temp)
    print(f"Loaded {len(temp_df):,} temperature records")
    print(f"Covering {temp_df['City'].nunique()} unique cities")
    
    print("\nBuilding spatial index...")
    cities, tree = build_city_index(temp_df)
    print(f"Indexed {len(cities):,} unique city locations")
    
    print("\nMatching fires to temperatures...")
    temp_results = []
    
    for idx, row in fires_df.iterrows():
        if idx % 10000 == 0 and idx > 0:
            print(f"  Processed {idx:,} / {len(fires_df):,} fires...")
        
        temp_info = get_temperature_for_fire(row, temp_df, cities, tree)
        temp_results.append(temp_info)
    
    print(f"  Processed {len(fires_df):,} / {len(fires_df):,} fires.")
    
    # Combine with fire data
    temp_results_df = pd.DataFrame(temp_results)
    merged_df = pd.concat([fires_df.reset_index(drop=True), temp_results_df], axis=1)
    
    # Select final columns
    output_cols = [
        'OBJECTID', 'FOD_ID', 'FIRE_NAME', 'FIRE_YEAR',
        'discovery_date', 'cont_date',
        'STAT_CAUSE_CODE', 'STAT_CAUSE_DESCR',
        'FIRE_SIZE', 'FIRE_SIZE_CLASS',
        'LATITUDE', 'LONGITUDE',
        'STATE', 'COUNTY',
        'matched_cities', 'num_cities',
        'discovery_temp', 'mean_temp', 'max_temp', 'min_temp', 'temp_range',
    ]
    
    final_df = merged_df[output_cols].copy()
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"\nSaving to {args.output}...")
    final_df.to_csv(args.output, index=False)
    
    print(f"\n✓ Saved {len(final_df):,} records")
    print(f"\nSample statistics:")
    print(f"  Fires with temperature data: {final_df['discovery_temp'].notna().sum():,}")
    print(f"  Mean discovery temperature: {final_df['discovery_temp'].mean():.1f}°C")
    print(f"  Mean fire duration temp: {final_df['mean_temp'].mean():.1f}°C")
    print(f"  Avg cities matched per fire: {final_df['num_cities'].mean():.1f}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
