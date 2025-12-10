# Fire Spread Map Generator

Python module for generating interactive Folium maps with wind-based fire spread visualization and population impact analysis. Used by the FastAPI backend to create dynamic fire simulation maps.

## Overview

This module creates HTML maps that visualize:
- **Fire spread area** as a wind-influenced ellipse
- **Affected counties** colored by percentage of area impacted
- **Population impact** calculated from census data
- **Animated fire progression** with realistic noise patterns
- **Wind direction** shown as animated arrow particles

## Features

### Fire Spread Modeling
- Fire area modeled as ellipse stretched in wind direction
- Stretch factor scales with wind speed (0-60+ mph)
- Fire origin positioned at back edge of ellipse
- Accounts for meteorological wind convention (direction wind comes FROM)

### Population Analysis
- Loads US county polygons from CSV with WKT geometry
- Merges with 2023 population estimates
- Calculates intersection area between fire ellipse and counties
- Computes affected population proportionally

### Visualizations
- **County heatmap**: Red intensity based on fraction of county affected
- **Fire animation**: JavaScript-based spread simulation with Perlin noise
- **Wind arrows**: Canvas-based particle system showing wind direction
- **Interactive controls**: Start/Reset buttons, progress bar

## Architecture

```
county_map_with_wind.py
├── load_county_data()      # Load county polygons + population
├── create_wind_ellipse()   # Generate fire spread ellipse geometry
├── population_map()        # Main function: create map + calculate stats
├── save_map_with_wind()    # Save HTML with embedded animations
├── generate_fire_animation_script()  # Fire spread JS animation
└── generate_wind_script()  # Wind particle JS animation
```

## Dependencies

```
geopandas>=1.0.0      # Spatial operations, CRS transformations
folium>=0.18.0        # Interactive map generation
shapely>=2.0.0        # Geometry operations (ellipse, intersection)
pandas>=2.0.0         # Data manipulation
numpy>=1.24.0         # Numerical operations
```

## Input Parameters

### `population_map()` Function

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `gdf` | GeoDataFrame | - | County data with geometry and population |
| `lat` | float | 20-50 | Latitude of fire origin (USA range) |
| `lon` | float | -125 to -65 | Longitude of fire origin (USA range) |
| `radius_km` | float | 1-100 | Base fire radius in kilometers |
| `wind_speed_mph` | float | 0-100 | Wind speed in miles per hour |
| `wind_direction_deg` | float | 0-360 | Wind direction (meteorological convention) |

### Wind Direction Convention

Wind direction follows **meteorological convention** (where wind comes FROM):
- `0°` = Wind from North → Fire spreads South
- `90°` = Wind from East → Fire spreads West
- `180°` = Wind from South → Fire spreads North
- `270°` = Wind from West → Fire spreads East

## Output

### Return Values
```python
total_pop, table_sorted, map_object, wind_data = population_map(...)
```

| Return | Type | Description |
|--------|------|-------------|
| `total_pop` | float | Total affected population (weighted by fraction) |
| `table_sorted` | GeoDataFrame | Counties sorted by contribution, with columns: COUNTY, STATE, population, fraction, population_contrib, heat |
| `map_object` | folium.Map | Folium map object (before animations added) |
| `wind_data` | dict | Data for animation scripts (wind field, ellipse coords) |

### Generated HTML File

The saved HTML file contains:
- Leaflet.js interactive map
- County polygons with tooltips
- Fire origin marker
- Fire spread animation (JavaScript)
- Wind particle animation (Canvas)
- Control buttons (Start/Reset)
- Progress bar

## Usage

### As Module (Backend Integration)

```python
from modelling_and_prediction.frontend.maps.county_map_with_wind import (
    load_county_data, 
    population_map, 
    save_map_with_wind
)

# Load county data (should be cached in production)
gdf = load_county_data(
    "path/to/US_COUNTIES.csv",
    "path/to/county_population_2023.csv"
)

# Generate map for California fire
total_pop, counties_df, m, wind_data = population_map(
    gdf,
    lat=36.7783,           # Central California
    lon=-119.4179,
    radius_km=8.0,         # 8km fire radius
    wind_speed_mph=35,     # Strong wind
    wind_direction_deg=245 # Wind from WSW
)

# Save with animations
save_map_with_wind(m, wind_data, "fire_simulation.html")

# Print statistics
print(f"Affected population: {total_pop:,.0f}")
print(f"Counties affected: {len(counties_df)}")
print(counties_df[['COUNTY', 'STATE', 'fraction', 'population_contrib']].head(10))
```

### Standalone Execution

```bash
cd /path/to/wildfire-risk
python -m modelling_and_prediction.frontend.maps.county_map_with_wind
```

Default parameters (editable in `__main__` block):
- Location: New York City (40.7128, -74.0060)
- Radius: 10 km
- Wind: 10 mph from 135° (SE)

## Data Files

### Required Input Files

#### `US_COUNTIES.csv`
County polygon boundaries in WKT format.

**Source:** [Kaggle - US Counties Database](https://www.kaggle.com/datasets/flynn28/us-counties-database?select=US_COUNTIES.csv)

| Column | Type | Description |
|--------|------|-------------|
| `GEOID` | string | 5-digit FIPS code |
| `STATE` | string | State name |
| `COUNTY` | string | County name |
| `BORDERS` | string | WKT polygon geometry (MultiPolygon/Polygon) |

**Download:**
1. Go to the Kaggle dataset page (requires Kaggle account)
2. Click "Download" → select `US_COUNTIES.csv`
3. Place in `modelling_and_prediction/data/processed/`

#### `county_population_2023.csv`
Population estimates by county from USDA Economic Research Service.

**Source:** [USDA ERS - County-level Data Sets](https://www.ers.usda.gov/data-products/county-level-data-sets/county-level-data-sets-download-data/)

| Column | Type | Description |
|--------|------|-------------|
| `GEOID` | string | 5-digit FIPS code |
| `POP_ESTIMATE_2023` | int | 2023 population estimate |

**Download:**
1. Go to the USDA ERS data products page
2. Under "Population" section, download the Excel file
3. Extract county-level population estimates for 2023
4. Save as CSV with columns `GEOID` and `POP_ESTIMATE_2023`
5. Place in `modelling_and_prediction/data/processed/`

### Data Preparation Notes

- **GEOID Format**: Must be 5-digit string (zero-padded), e.g., `"06037"` for Los Angeles County, CA
- **Geometry CRS**: County borders should be in WGS84 (EPSG:4326)
- **Population Join**: Files are merged on `GEOID` column

### Excluded Territories

The following are automatically excluded:
- American Samoa
- Commonwealth of the Northern Mariana Islands
- Guam
- Puerto Rico
- U.S. Virgin Islands
- Hawaii

## Fire Spread Model

### Ellipse Geometry

The fire spread is modeled as an ellipse:

```
         Wind Direction (where wind blows TO)
              ↓
    ┌─────────────────────┐
   /                       \
  /     Fire Spread Area    \
 /                           \
│             🔥              │ ← Fire Origin (shifted back)
 \                           /
  \                         /
   \                       /
    └─────────────────────┘
         
Major Axis (a) = radius × stretch_factor
Minor Axis (b) = radius
```

### Stretch Factor

```python
stretch_factor = 1.0 + (wind_speed_mph / 100.0)
```

| Wind Speed | Stretch Factor | Effect |
|------------|----------------|--------|
| 0 mph | 1.0x | Perfect circle |
| 25 mph | 1.25x | Slightly elongated |
| 50 mph | 1.5x | Moderately elongated |
| 75 mph | 1.75x | Highly elongated |
| 100 mph | 2.0x | Very elongated |

### Origin Shift

Fire origin is shifted to the back edge of the ellipse:
```python
shift = (major_axis - minor_axis) × 0.5
```

This positions the fire start point at the upwind edge, with the fire spreading downwind.

## Animation Details

### Fire Animation

The fire animation uses **Perlin noise** for realistic irregular edges:

- **Duration**: 12 seconds (configurable)
- **Edge noise**: Subtle waves along fire perimeter
- **Indentations**: 3-5 random shallow dents
- **Protrusions**: 4-6 fingers extending in wind direction
- **Smoothing**: Edges smooth to perfect ellipse in final 30%

### Wind Animation

Canvas-based particle system:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PARTICLE_COUNT` | 1400 | Number of wind arrows |
| `PARTICLE_MAX_AGE` | 120 | Frames before respawn |
| `WIND_GRID_SIZE` | 30 | Wind field resolution |
| `WIND_GRID_SPAN` | 10 | Geographic extent (degrees) |

Arrow properties:
- Color: Blue gradient (darker = faster)
- Opacity: 25-40% (semi-transparent)
- Direction: Points where wind blows TO
- Speed: Scales with wind speed

## Coordinate Reference Systems

| CRS | EPSG | Usage |
|-----|------|-------|
| WGS84 | 4326 | Input/output coordinates, Leaflet display |
| Albers Equal Area | 5070 | Area calculations, ellipse generation |

The module handles all CRS transformations internally.

## Performance Considerations

### Caching
- **County data**: Load once at backend startup, cache globally
- **Generated maps**: Each request generates new HTML file

### Single File Strategy
The system uses a single `fire_map.html` file that gets overwritten on each request:
- No file accumulation
- Cache-busting via `?t=timestamp` query parameter
- File size: ~50-100 KB

## Related Documentation

- **[Main Project README](../../../../README.md)**: Comprehensive documentation of machine learning models, methodology, and implementation
- **[Frontend README](../README.md)**: Documentation of the web interface and user-facing features
- **[About This Project](../../../../ABOUT_THIS_PROJECT.md)**: Project overview, business case, and value proposition

## Integration with Backend

The FastAPI backend (`main.py`) uses this module via:

```python
@app.post("/api/generate-fire-map")
async def generate_fire_map(request: FireMapRequest):
    # Import functions
    from modelling_and_prediction.frontend.maps.county_map_with_wind import (
        load_county_data, population_map, save_map_with_wind
    )
    
    # Generate map
    total_pop, table, m, wind_data = population_map(
        cached_gdf,
        request.latitude,
        request.longitude,
        request.radius_km,
        request.wind_speed_mph,
        request.wind_direction_deg
    )
    
    # Save (overwrites existing fire_map.html)
    save_map_with_wind(m, wind_data, "fire_map.html")
    
    # Return URL with cache-buster to force browser refresh
    return {"map_url": f"/maps/fire_map.html?t={timestamp}", "total_population": total_pop, ...}
```

## Example Output

For a fire at 36.78°N, 119.42°W with 5km radius and 30mph wind from 245°:

```
Wind from: 245° → blows to: 65°
Direction: dx=0.91, dy=0.42
Ellipse: a=6.5km, b=5.0km, shift=0.8km

Affected population: 127,432

Top affected counties:
  COUNTY          STATE       FRACTION    POPULATION_CONTRIB
  Fresno          California  0.0312      30,847
  Tulare          California  0.0198      9,504
  Kings           California  0.0089      1,387
```
