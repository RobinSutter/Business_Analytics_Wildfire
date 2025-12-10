"""
Data preparation module for wildfire risk prediction.

This module handles:
1. Loading and cleaning wildfire and temperature datasets
2. Spatial and temporal joining of data
3. Feature engineering (anomalies, trends, lags, rolling statistics)
4. Creation of training-ready datasets
"""
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from pandas.tseries.offsets import MonthEnd

from src.config import DataConfig, RAW_DATA_DIR, PROCESSED_DATA_DIR, WILDFIRE_DB, TEMP_BY_CITY
from src.utils import setup_logging

logger = setup_logging()


def load_temperature_data(
    config: DataConfig,
    temperature_file: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load and preprocess temperature data.
    
    Args:
        config: Data configuration
        temperature_file: Optional specific temperature file to load
        
    Returns:
        Cleaned temperature DataFrame
    """
    logger.info("Loading temperature data...")
    
    if temperature_file is None:
        # Default to city-level temperatures for precise matching
        temperature_file = TEMP_BY_CITY
    
    if not temperature_file.exists():
        raise FileNotFoundError(f"Temperature file not found: {temperature_file}")
    
    df = pd.read_csv(temperature_file)
    
    # Standardize column names
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    
    # Parse dates
    df["dt"] = pd.to_datetime(df["dt"])
    df["year"] = df["dt"].dt.year
    df["month"] = df["dt"].dt.month
    
    # Filter by country if applicable
    if "country" in df.columns and config.temperature_countries:
        df = df[df["country"].isin(config.temperature_countries)]
    
    # Filter by date range
    df = df[(df["year"] >= config.start_year) & (df["year"] <= config.end_year)]
    
    # Remove missing temperatures
    df = df.dropna(subset=["averagetemperature"])
    
    # Rename for consistency
    df = df.rename(columns={
        "averagetemperature": "avg_temp",
        "averagetemperatureuncertainty": "temp_uncertainty",
    })
    
    logger.info(f"Loaded {len(df):,} temperature records")
    return df


def load_wildfire_data(config: DataConfig, db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load wildfire data from SQLite database.
    
    Loads the 1.88M US Wildfires dataset (1992-2015) from the SQLite database.
    
    Args:
        config: Data configuration
        db_path: Optional path to SQLite database
        
    Returns:
        Wildfire DataFrame with fire occurrences
    """
    logger.info("Loading wildfire data from SQLite database...")
    
    if db_path is None:
        db_path = WILDFIRE_DB
    
    if not db_path.exists():
        raise FileNotFoundError(
            f"Wildfire database not found: {db_path}\n"
            "Please download the 1.88 Million US Wildfires dataset from Kaggle."
        )
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Query relevant columns
    query = """
    SELECT 
        FIRE_YEAR as year,
        DISCOVERY_DOY as day_of_year,
        STATE as state,
        FIPS_NAME as county,
        LATITUDE as latitude,
        LONGITUDE as longitude,
        FIRE_SIZE as fire_size,
        FIRE_SIZE_CLASS as fire_size_class
    FROM Fires
    WHERE FIRE_YEAR >= ? AND FIRE_YEAR <= ?
        AND STATE IS NOT NULL
        AND LATITUDE IS NOT NULL
        AND LONGITUDE IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn, params=(config.start_year, config.end_year))
    conn.close()
    
    # Convert day of year to month (approximate)
    df["month"] = ((df["day_of_year"] - 1) // 30.4).astype(int) + 1
    df["month"] = df["month"].clip(1, 12)
    
    # Clean state names (trim whitespace, handle abbreviations)
    df["state"] = df["state"].str.strip()
    
    # Map state abbreviations to full names for temperature matching
    state_abbrev_map = {
        "CA": "California", "TX": "Texas", "FL": "Florida", "GA": "Georgia",
        "NC": "North Carolina", "SC": "South Carolina", "NY": "New York",
        "AZ": "Arizona", "AL": "Alabama", "MS": "Mississippi", "OR": "Oregon",
        "WA": "Washington", "CO": "Colorado", "MT": "Montana", "ID": "Idaho",
        "NV": "Nevada", "NM": "New Mexico", "UT": "Utah", "WY": "Wyoming",
        "OK": "Oklahoma", "KS": "Kansas", "AR": "Arkansas", "LA": "Louisiana",
        "TN": "Tennessee", "KY": "Kentucky", "MO": "Missouri", "VA": "Virginia",
        "WV": "West Virginia", "PA": "Pennsylvania", "OH": "Ohio", "MI": "Michigan",
        "IN": "Indiana", "IL": "Illinois", "WI": "Wisconsin", "MN": "Minnesota",
        "IA": "Iowa", "NE": "Nebraska", "SD": "South Dakota", "ND": "North Dakota",
    }
    
    df["state_full"] = df["state"].map(state_abbrev_map).fillna(df["state"])
    df = df.rename(columns={"state": "state_abbrev", "state_full": "state"})
    
    # Create fire occurrence indicator (all records are fires)
    df["fire_occurred"] = 1
    
    logger.info(f"Loaded {len(df):,} wildfire records from database")
    logger.info(f"  Date range: {df['year'].min()}-{df['year'].max()}")
    logger.info(f"  States: {df['state'].nunique()}")
    logger.info(f"  Total fires: {len(df):,}")
    
    return df


def find_nearest_city_vectorized(
    wildfire_df: pd.DataFrame,
    cities_df: pd.DataFrame,
    max_distance_km: float = 150,
) -> pd.Series:
    """
    Find nearest city for each wildfire using vectorized Haversine distance.
    
    Args:
        wildfire_df: DataFrame with wildfire locations (latitude, longitude)
        cities_df: DataFrame with city locations  
        max_distance_km: Maximum distance to consider a match
        
    Returns:
        Series of nearest city names (or None for no match)
    """
    from numpy import radians, sin, cos, arcsin, sqrt, nan
    
    logger.info(f"Finding nearest city for {len(wildfire_df):,} wildfires...")
    
    # Convert to radians
    wf_lat = radians(wildfire_df["latitude"].values)
    wf_lon = radians(wildfire_df["longitude"].values)
    city_lat = radians(cities_df["latitude"].values)
    city_lon = radians(cities_df["longitude"].values)
    
    nearest_cities = []
    
    # Process in batches to avoid memory issues
    batch_size = 5000
    for i in range(0, len(wildfire_df), batch_size):
        batch_wf_lat = wf_lat[i:i+batch_size, np.newaxis]
        batch_wf_lon = wf_lon[i:i+batch_size, np.newaxis]
        
        # Broadcasting: (batch_size, 1) and (1, n_cities) -> (batch_size, n_cities)
        dlat = city_lat - batch_wf_lat
        dlon = city_lon - batch_wf_lon
        
        a = sin(dlat/2)**2 + cos(batch_wf_lat) * cos(city_lat) * sin(dlon/2)**2
        c = 2 * arcsin(sqrt(np.clip(a, 0, 1)))
        distances = 6371 * c  # Earth radius in km
        
        # Find nearest city for each wildfire in batch
        min_indices = distances.argmin(axis=1)
        min_distances = distances[np.arange(len(distances)), min_indices]
        
        # Only keep matches within max distance
        batch_cities = [
            cities_df.iloc[idx]["city"] if dist <= max_distance_km else None
            for idx, dist in zip(min_indices, min_distances)
        ]
        nearest_cities.extend(batch_cities)
        
        if (i // batch_size + 1) % 10 == 0:
            logger.info(f"  Processed {i + len(batch_cities):,} / {len(wildfire_df):,} wildfires")
    
    return pd.Series(nearest_cities, index=wildfire_df.index)


def merge_wildfire_temperature(
    wildfire_df: pd.DataFrame,
    temperature_df: pd.DataFrame,
    config: DataConfig,
) -> pd.DataFrame:
    """
    Merge wildfire and temperature data using city-level nearest-neighbor matching.
    
    Each wildfire is matched to the nearest city in the temperature dataset,
    then joined on city-year-month for precise temperature data.
    
    Args:
        wildfire_df: Wildfire data with lat/lon coordinates
        temperature_df: City-level temperature observations
        config: Data configuration
        
    Returns:
        Merged DataFrame with wildfire and temperature data
    """
    logger.info("Merging wildfire and temperature data using city-level matching...")
    
    # Extract unique city locations from temperature data (US cities only)
    us_temp = temperature_df[temperature_df["country"] == "United States"].copy()
    cities = us_temp[["city", "latitude", "longitude"]].drop_duplicates()
    
    # Parse lat/lon from format like "32.95N" to numeric
    def parse_coordinate(coord_str, coord_type):
        """Convert '32.95N' or '100.53W' to numeric with proper sign."""
        coord_str = str(coord_str).strip()
        # Extract numeric part and direction
        direction = coord_str[-1].upper()
        value = float(coord_str[:-1])
        # Apply sign based on direction
        if coord_type == "lat":
            return value if direction == "N" else -value
        else:  # lon
            return -value if direction == "W" else value
    
    cities["latitude"] = cities["latitude"].apply(lambda x: parse_coordinate(x, "lat"))
    cities["longitude"] = cities["longitude"].apply(lambda x: parse_coordinate(x, "lon"))
    cities = cities.dropna(subset=["latitude", "longitude"])
    
    logger.info(f"Temperature dataset has {len(cities):,} unique US cities with valid coordinates")
    
    # Find nearest city for each wildfire
    wildfire_df["nearest_city"] = find_nearest_city_vectorized(
        wildfire_df, 
        cities, 
        max_distance_km=150
    )
    
    # Filter to wildfires with matched cities
    matched_count = wildfire_df["nearest_city"].notna().sum()
    logger.info(f"Matched {matched_count:,} / {len(wildfire_df):,} wildfires to cities ({matched_count/len(wildfire_df):.1%})")
    
    wildfires_matched = wildfire_df[wildfire_df["nearest_city"].notna()].copy()
    
    # Prepare temperature data: aggregate by city-year-month
    temp_city_monthly = us_temp.groupby(["city", "year", "month"]).agg({
        "avg_temp": "mean",
        "temp_uncertainty": "mean",
    }).reset_index()
    
    # Create fire occurrence aggregation: count fires per city-year-month
    fire_counts = wildfires_matched.groupby(["nearest_city", "year", "month"]).size().reset_index(name="fire_count")
    
    # Create complete grid of all city-year-month combinations in temperature data
    # This gives us both fire and non-fire observations
    all_observations = temp_city_monthly.copy()
    all_observations = all_observations.merge(
        fire_counts,
        left_on=["city", "year", "month"],
        right_on=["nearest_city", "year", "month"],
        how="left",
    )
    
    # Fill NaN fire counts with 0 (no fire occurred)
    all_observations["fire_count"] = all_observations["fire_count"].fillna(0)
    
    # Create binary target: fire_occurred (1 if any fire, 0 otherwise)
    all_observations["fire_occurred"] = (all_observations["fire_count"] > 0).astype(int)
    
    # Use city column (from temperature data) as the main city identifier
    all_observations["nearest_city"] = all_observations["city"]
    
    # Get representative location data for each city (avg lat/lon from wildfires)
    city_locations = wildfires_matched.groupby("nearest_city").agg({
        "latitude": "mean",
        "longitude": "mean",
        "state": lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
        "state_abbrev": lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
        "county": lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
    }).reset_index()
    
    # Merge location data
    merged = all_observations.merge(
        city_locations,
        left_on="city",
        right_on="nearest_city",
        how="left",
        suffixes=("", "_loc"),
    )
    
    fire_obs = merged["fire_occurred"].sum()
    logger.info(f"Created {len(merged):,} monthly observations: {fire_obs:,} with fires, {len(merged)-fire_obs:,} without fires")
    
    return merged


def engineer_features(df: pd.DataFrame, config: DataConfig) -> pd.DataFrame:
    """
    Engineer predictive features from merged data.
    
    Features include:
    - Temperature anomalies (deviation from historical mean)
    - Seasonal effects
    - Lag features (previous months' temperatures)
    - Rolling statistics (moving averages)
    - Trend features
    
    Args:
        df: Merged wildfire and temperature data
        config: Data configuration
        
    Returns:
        DataFrame with engineered features
    """
    logger.info("Engineering features...")
    
    df = df.copy()
    df = df.sort_values(["nearest_city", "year", "month"]).reset_index(drop=True)
    
    # 1. Temperature anomaly (deviation from city's historical mean)
    city_mean_temp = df.groupby("nearest_city")["avg_temp"].transform("mean")
    df["temp_anomaly"] = df["avg_temp"] - city_mean_temp
    
    # 2. Seasonal features
    df["is_summer"] = df["month"].isin([6, 7, 8]).astype(int)
    df["is_fall"] = df["month"].isin([9, 10, 11]).astype(int)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    
    # 3. Lag features (previous months' temperatures)
    for lag in config.lag_months:
        df[f"temp_lag_{lag}m"] = df.groupby("nearest_city")["avg_temp"].shift(lag)
        df[f"anomaly_lag_{lag}m"] = df.groupby("nearest_city")["temp_anomaly"].shift(lag)
    
    # 4. Rolling statistics
    for window in config.rolling_windows:
        df[f"temp_rolling_mean_{window}m"] = (
            df.groupby("nearest_city")["avg_temp"]
            .rolling(window, min_periods=1)
            .mean()
            .reset_index(0, drop=True)
        )
        df[f"temp_rolling_std_{window}m"] = (
            df.groupby("nearest_city")["avg_temp"]
            .rolling(window, min_periods=1)
            .std()
            .reset_index(0, drop=True)
        )
    
    # 5. Trend feature (year as continuous variable, normalized)
    df["year_normalized"] = (df["year"] - df["year"].min()) / (df["year"].max() - df["year"].min())
    
    # 6. Interaction features
    df["temp_anomaly_x_summer"] = df["temp_anomaly"] * df["is_summer"]
    
    # Drop rows with NaN from lag/rolling features (early periods)
    initial_len = len(df)
    df = df.dropna()
    logger.info(f"Features engineered: {len(df):,} records ({initial_len - len(df):,} dropped due to lag/rolling NaN)")
    
    return df


def prepare_datasets(config: Optional[DataConfig] = None) -> Tuple[pd.DataFrame, dict]:
    """
    Main pipeline to prepare training and testing datasets.
    
    Args:
        config: Data configuration (uses default if None)
        
    Returns:
        Tuple of (processed_features_df, summary_dict)
    """
    if config is None:
        from src.config import DEFAULT_DATA_CONFIG
        config = DEFAULT_DATA_CONFIG
    
    logger.info("Starting data preparation pipeline...")
    
    # 1. Load temperature data
    temperature_df = load_temperature_data(config)
    
    # 2. Load wildfire data from SQLite database
    wildfire_df = load_wildfire_data(config)
    
    # 3. Merge datasets using city-level nearest-neighbor matching
    merged_df = merge_wildfire_temperature(wildfire_df, temperature_df, config)
    
    # 4. Engineer features
    features_df = engineer_features(merged_df, config)
    
    # 6. Save processed dataset
    output_path = PROCESSED_DATA_DIR / "wildfire_features.parquet"
    features_df.to_parquet(output_path, index=False)
    logger.info(f"Saved processed features to {output_path}")
    # Also export as CSV for easy sharing
    csv_path = PROCESSED_DATA_DIR / "wildfire_features.csv"
    features_df.to_csv(csv_path, index=False)
    logger.info(f"Saved processed features (CSV) to {csv_path}")
    
    # 7. Create summary statistics
    summary = {
        "total_records": len(features_df),
        "fire_occurrences": int(features_df[config.target_column].sum()),
        "fire_rate": float(features_df[config.target_column].mean()),
        "states": features_df["state"].nunique(),
        "years": features_df["year"].nunique(),
        "date_range": f"{features_df['year'].min()}-{features_df['year'].max()}",
    }
    
    logger.info("\n" + "="*60)
    logger.info("Data Preparation Summary")
    logger.info("="*60)
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    logger.info("="*60 + "\n")
    
    return features_df, summary


if __name__ == "__main__":
    # Run data preparation pipeline
    features_df, summary = prepare_datasets()
    print(f"\nProcessed {len(features_df):,} records")
    print(f"Features shape: {features_df.shape}")
    print(f"Target distribution: {features_df['fire_occurred'].value_counts().to_dict()}")
