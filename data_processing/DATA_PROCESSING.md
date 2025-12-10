# Data Processing Component: Wildfire-Temperature Data Integration

## Overview

This directory contains the **data processing and preprocessing component** of the larger wildfire risk prediction project. This component focuses specifically on integrating wildfire records with temperature data, performing statistical analysis, and preparing datasets for machine learning models. For the complete project overview, including the final modeling approach and results, see the [Main Project Documentation](../README.md).

This data processing pipeline was developed as the first phase of the project. Initially, the goal was to model fire occurrence risk zones based on temperature and predict how risk changes over time using CMIP6 climate models for future projections. However, after extensive data merging and statistical analysis, we discovered insufficient statistical evidence for a strong correlation between fire occurrence and temperature. This critical finding led to a pivot in the overall project approach, shifting focus to **fire size prediction** instead, which showed more promising relationships with temperature variables.

The pipeline processes real wildfire records from a SQLite database, merges them with city-level temperature observations, and prepares features for machine learning models. This component uses large-scale datasets (1.88M+ fire records) that required sophisticated geospatial matching techniques to combine fire events with corresponding temperature measurements.

## Relationship to Overall Project

This data processing component serves as the foundation for the machine learning models developed in the `modelling_and_prediction/` directory. The processed datasets created here (particularly `fires_with_temperature.csv`) are essential inputs for the fire size prediction models described in the [Main Project Documentation](../README.md).

**Project Structure:**
- **This Component** (`data_processing/`): Data integration, statistical analysis, and preprocessing
- **Modeling Component** (`modelling_and_prediction/`): Machine learning model development and evaluation
- **Main Project** (root): Overall project documentation and results

## Project Evolution: From Initial Idea to Final Approach

### Initial Goal (Original Research Direction)

The project began with the following objectives:
- Model fire occurrence risk zones based on temperature
- Predict how risk changes over time based on CMIP6 models for the future
- Create spatial risk maps for different regions and time periods

This initial direction was based on the hypothesis that temperature would be a strong predictor of fire occurrence frequency.

### Challenges Encountered During Data Processing

During the data processing phase, we encountered several significant challenges:

- **Large-scale datasets**: The wildfire data wasn't simple CSV files but a complete SQLite database containing 1.88 million fire records, requiring specialized database handling
- **Complex data merging**: Matching fire events to corresponding temperature measurements required sophisticated geospatial algorithms
- **CMIP6 data download**: Downloading CMIP6 climate projection files required navigating a complex API (Copernicus Climate Data Store) with authentication, API key setup, and handling large NetCDF files for multiple scenarios and time periods
- **Statistical findings**: After merging and analysis, we found insufficient statistical evidence for correlation between fire occurrence and temperature

### Critical Pivot: Adaptation Based on Empirical Findings

The statistical analysis conducted in this data processing phase revealed a fundamental issue with the initial research direction:

- **Key Finding**: Insufficient statistical evidence for strong correlation between fire occurrence and temperature
- **Discovery**: Fire size showed more promising relationships with temperature variables
- **Decision**: Shifted focus from **fire occurrence** to **fire size** modeling
- **Impact**: This adaptation is reflected in the modeling pipeline in the `modelling_and_prediction/` directory

**The Pivotal Analysis**: The correlation analysis notebook (`notebooks/analysis.ipynb`) was instrumental in demonstrating clear correlations between temperature features and fire size. This comprehensive analysis showed:
- Strong correlations (0.31-0.57) between temperature variables (mean_temp, max_temp, temp_range, discovery_temp) and fire size
- Multiple engineered features with meaningful predictive relationships
- Clear seasonal and temporal patterns in fire size
- Statistical significance across multiple feature types

This evidence-based analysis provided the quantitative justification needed to pivot the project focus from fire occurrence prediction to fire size prediction, where the data showed clear predictive signals.

This pivot exemplifies evidence-based research methodology, where initial hypotheses are tested and approaches are adapted based on empirical findings rather than forcing models onto unsuitable data. The complete story of this evolution and the final modeling approach is documented in the [Main Project Documentation](../README.md).

## Initial Research Questions (Data Processing Phase)

The data processing component was designed to answer these initial research questions:

- How strongly is wildfire occurrence in the U.S. correlated with local temperature variations?
- How does rising temperature affect the frequency and distribution of wildfires?
- What is the relationship between temperature and fire size?
- ~~How will wildfire risk evolve under projected CMIP6 climate scenarios?~~ (Implemented but deprecated - see CMIP6 section)

The answers to these questions, particularly the weak correlation findings, directly informed the project's pivot to fire size prediction.

## Data Sources

- **1.88M US Wildfires** (1992–2015): `data/raw/FPA_FOD_20170508.sqlite`
  - Source: [Kaggle - 1.88 Million US Wildfires](https://www.kaggle.com/rtatman/188-million-us-wildfires)
  - Contains fire locations (lat/lon), dates, sizes, and state/county info
  - **Note**: This is a large SQLite database, not a simple CSV file. See `SETUP.md` for installation instructions.

- **Berkeley Earth Surface Temperatures**: `data/processed/GlobalLandTemperaturesByCity.csv`
  - Source: [Kaggle - Climate Change: Earth Surface Temperature Data](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data)
  - Monthly mean temperatures by city from 1750–2015
  - US-specific subset: `data/processed/USTemperaturesByCity/USTemperaturesByCity.csv`

- **CMIP6 Climate Projections** (implemented but deprecated): 
  - CMIP6 climate model projections were implemented for future risk assessment
  - Includes historical and future scenario data (SSP2-4.5, SSP5-8.5) from models like MIROC6
  - Source: [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/datasets/projections-cmip6)
  - Download script available: `scripts/download_cmip6_tas.py` (see CMIP6 Data Download section below)
  - **Note**: No longer necessary after shifting focus from fire occurrence to fire size modeling

## Data Merging Approaches

We implemented **two different approaches** to merge wildfire data with temperature measurements:

### Approach 1: Individual Fire-Level Matching (`merge_fire_temperature.py`)

This approach matches each individual fire event to nearby temperature stations:

- **Spatial matching**: Uses BallTree algorithm for efficient geospatial nearest-neighbor search
- **Matching strategy**: 
  - Finds all cities within 150km radius of each fire
  - If no cities found within radius, uses the 5 nearest cities as fallback
- **Temporal matching**: 
  - Converts Julian dates to standard datetime format
  - Matches temperature records for the period from fire discovery to containment
  - Calculates mean, max, min, and range of temperatures during the fire period
- **Output**: `data/processed/fires_with_temperature.csv` - Each row represents a fire with its matched temperature measurements

**Key features**:
- Discovery temperature (temperature on the day fire was discovered)
- Mean temperature during fire period
- Maximum and minimum temperatures during fire period
- Temperature range
- Number of cities matched per fire

**Note**: This output file (`fires_with_temperature.csv`) is the primary dataset used by the machine learning models in the `modelling_and_prediction/` directory.

### Approach 2: Aggregated City-Year-Month Panel (`data_preparation.py`)

This approach creates an aggregated panel dataset for modeling fire occurrence:

- **Spatial matching**: Matches each wildfire to the nearest city (within 150km) using vectorized Haversine distance calculations
- **Aggregation**: 
  - Groups fires by city-year-month combinations
  - Creates a complete grid of all city-year-month observations (including periods with no fires)
  - Creates binary target variable: `fire_occurred` (1 if any fire occurred, 0 otherwise)
- **Temperature data**: Aggregates temperature data by city-year-month
- **Output**: Panel dataset suitable for modeling fire occurrence at aggregated temporal and spatial scales

**Key features**:
- City-year-month panel structure
- Binary fire occurrence target
- Fire count per city-year-month
- Average temperature per city-year-month
- Representative location data (average lat/lon from matched fires)

**Note**: This approach was developed for the initial fire occurrence modeling goal. While the aggregated dataset was created, the statistical findings from this data processing phase led to the pivot away from occurrence modeling.

Both approaches use Haversine distance calculations for accurate geospatial matching and handle the coordinate format conversion (e.g., "32.95N" to decimal degrees).

## Methodology

1. **Data Preparation**: 
   - Load wildfires from SQLite database
   - Match each fire to nearest temperature city using geospatial algorithms (Haversine distance, BallTree)
   - Build city-year-month panel and aggregate for modeling
   - Report results at state level

2. **Feature Engineering**: 
   - Temperature anomalies
   - Seasonal signals (sin/cos transformations)
   - Temporal lags
   - Rolling windows
   - Normalized year trend

3. **Statistical Analysis**: 
   - Correlation analysis between temperature and fire occurrence
   - **Fire size correlation analysis** (`notebooks/analysis.ipynb`) - comprehensive analysis demonstrating clear correlations between temperature features and fire size
   - Distribution analysis of fire characteristics
   - Temporal and spatial pattern exploration
   - Statistical validation of initial hypotheses

4. **Model Preparation** (for initial occurrence modeling approach): 
   - Logistic Regression and LightGBM for fire occurrence (initial approach)
   - Regression models for fire size (adapted approach)
   - Temporal split for train/test
   - Primary metrics: PR-AUC, ROC-AUC, Brier score

**Note**: The modeling work itself is conducted in the `modelling_and_prediction/` directory. This data processing component focuses on data preparation and statistical validation.

## Repository Structure

```
data_processing/
├── README.md                    # This file (data processing component documentation)
├── SETUP.md                     # Detailed setup instructions
├── Benni.md                     # Additional project notes
├── src/
│   ├── config.py                # Configuration and paths
│   ├── data_preparation.py      # Aggregated panel approach (city-year-month)
│   ├── merge_fire_temperature.py # Individual fire-level matching approach
│   ├── analyze_fire_temperature.py # Statistical analysis and visualizations
│   └── modeling.py              # Model training (if present)
├── scripts/
│   ├── download_cmip6_tas.py   # CMIP6 data download script
│   └── cdsapirc.example         # CDS API credentials template
├── notebooks/
│   ├── analysis.ipynb                      # Fire size correlation analysis (key pivot analysis)
│   ├── correlation_analysis.ipynb
│   ├── data_preparation_Temperatures.ipynb
│   └── fire_occurrence_correlation.ipynb
├── data/
│   ├── raw/                     # Input datasets (SQLite DB, CSVs)
│   └── processed/               # Processed datasets
│       ├── fires_with_temperature.csv  # Output from Approach 1 (used by ML models)
│       ├── GlobalLandTemperaturesByCity.csv
│       └── USTemperaturesByCity/
└── reports/                     # Analysis outputs and visualizations
    ├── correlation_heatmap.png
    ├── fire_causes.png
    ├── geographic_analysis.png
    ├── temperature_relationships.png
    └── temporal_trends.png
```

## Key Scripts

### `src/merge_fire_temperature.py`
- Spatially joins wildfire events with temperature data by finding the nearest cities within 150km of each fire
- Converts Julian dates to standard datetime and matches temperature records for the period from fire discovery to containment
- Uses BallTree algorithm for efficient geospatial nearest-neighbor search
- Outputs a cleaned dataset with essential fire characteristics and corresponding temperature measurements
- **Output**: `data/processed/fires_with_temperature.csv` - This is the primary dataset used by the machine learning models in `modelling_and_prediction/`

### `src/data_preparation.py`
- Creates aggregated city-year-month panel dataset
- Matches wildfires to nearest cities and aggregates by temporal periods
- Creates binary fire occurrence target for modeling
- Prepares features for machine learning models
- **Output**: Panel dataset suitable for occurrence modeling (developed for initial approach, before pivot)

### `src/analyze_fire_temperature.py`
- Generates comprehensive statistical analyses exploring relationships between temperature and wildfire characteristics
- Creates visualizations examining fire size, frequency, causes, and seasonal patterns in relation to temperature
- Produces correlation analyses and distribution plots
- Outputs results to `reports/` directory
- **Purpose**: Statistical validation that led to the project pivot from occurrence to size prediction

### `notebooks/analysis.ipynb` **Key Analysis Notebook**
- **Comprehensive fire size correlation analysis** that demonstrated clear correlations between temperature features and fire size
- Shows strong correlations (0.31-0.57) with temperature variables: mean_temp, max_temp, temp_range, and discovery_temp
- Includes feature engineering, statistical significance testing, visualizations, and aggregated analyses
- **Critical finding**: This analysis provided quantitative evidence that fire size has meaningful predictive relationships with temperature, justifying the pivot from fire occurrence to fire size prediction
- **Impact**: This notebook's findings directly informed the decision to focus modeling efforts on fire size prediction rather than fire occurrence

## CMIP6 Data Download (Implemented but Deprecated)

CMIP6 climate projections were initially implemented in this data processing component to enable future risk projections under different climate scenarios. However, after shifting focus from fire occurrence to fire size modeling, the CMIP6 data and projections are no longer necessary for the current approach. The download infrastructure remains available for reference or future use.

### How to Download CMIP6 Data

If you want to download CMIP6 data for future use or implementation:

1. **Register for Copernicus CDS API**:
   - Visit [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/)
   - Create an account and log in
   - Navigate to your profile to get your UID and API key

2. **Setup credentials**:
   ```bash
   cp scripts/cdsapirc.example ~/.cdsapirc
   # Edit ~/.cdsapirc and add your UID and API key
   ```

3. **Download data**:
   ```bash
   uv run python scripts/download_cmip6_tas.py
   ```

This script downloads MIROC6 near-surface air temperature (tas) data:
- Historical period: `tas_Amon_MIROC6_historical_1992-2014.nc`
- SSP2-4.5 scenario (moderate emissions): `tas_Amon_MIROC6_ssp245_2015-2100.nc`
- SSP5-8.5 scenario (high emissions): `tas_Amon_MIROC6_ssp585_2015-2100.nc`

Files are saved to `data/raw/` and follow the CDS naming convention. The data can be used with xarray for spatial analysis and future projection work.

## Statistical Findings

After merging the fire dataset with temperature measurements and conducting correlation analysis in this data processing phase, we found:

- **Insufficient statistical evidence** for a strong correlation between fire occurrence and temperature
- This finding led to the adaptation of the overall project's modeling approach
- **Fire size** showed more promising relationships with temperature variables

### Fire Size Correlation Analysis

The comprehensive correlation analysis conducted in `notebooks/analysis.ipynb` revealed **clear and statistically significant correlations** between temperature features and fire size:

- **Mean temperature**: r = 0.45 (moderate to strong correlation)
- **Max temperature**: r = 0.57 (strong correlation)
- **Temperature range**: r = 0.31 (moderate correlation)
- **Discovery temperature**: r = 0.44 (moderate to strong correlation)

Additionally, the analysis showed:
- Multiple engineered features with meaningful predictive relationships
- Strong aggregated patterns at monthly/seasonal levels
- Clear temporal and spatial patterns
- Statistical significance across multiple feature types

**This quantitative evidence from the correlation analysis directly justified the pivot from fire occurrence prediction to fire size prediction**, where the data demonstrated clear predictive signals. The final modeling work focuses on fire size prediction (see `modelling_and_prediction/` directory and [Main Project Documentation](../README.md)).

These statistical findings were critical in guiding the project's evolution from the initial fire occurrence prediction goal to the final fire size prediction approach.

## Typical Workflow

1. **Data preparation and merging**:
   - Run `merge_fire_temperature.py` for individual fire-level analysis
   - Run `data_preparation.py` for aggregated panel creation
   - Both approaches produce different outputs suitable for different types of analysis

2. **Exploratory analysis**:
   - Run `analyze_fire_temperature.py` for statistical analysis and visualizations
   - **Run `notebooks/analysis.ipynb`** for comprehensive fire size correlation analysis (key analysis that led to project pivot)
   - Review outputs in `reports/` directory
   - Explore notebooks in `notebooks/` for interactive analysis

3. **Model training** (in `modelling_and_prediction/` directory):
   - Focus shifted to fire size modeling based on statistical findings from this data processing phase
   - See [Main Project Documentation](../README.md) for complete modeling documentation

## Reproducibility

- Dependencies are pinned via `pyproject.toml` (and `uv.lock` if present) at the project root
- Prefer `uv run ...` to ensure commands use the synced environment
- For notebooks, start kernels from the project venv (after `uv venv && source .venv/bin/activate && uv sync`)

## Impact of This Data Processing Component

This data processing component made several critical contributions to the overall project:

- **Data Integration**: Successfully merged 1.88 million fire records with temperature data using sophisticated geospatial algorithms
- **Statistical Validation**: Quantified temperature–wildfire relationships and provided insights into fire size relationships with temperature
- **Research Direction**: The correlation analysis in `notebooks/analysis.ipynb` demonstrated clear correlations (0.31-0.57) between temperature features and fire size, directly informing the project's pivot from occurrence to size prediction
- **Foundation for Modeling**: Created the processed datasets (particularly `fires_with_temperature.csv`) that serve as inputs for the machine learning models
- **Methodological Lessons**: Documents the importance of statistical validation before committing to modeling approaches
- **Scientific Rigor**: Demonstrates the value of adapting research direction based on empirical findings

The processed datasets and statistical insights from this component are essential prerequisites for the machine learning models developed in the `modelling_and_prediction/` directory. For complete project results and modeling outcomes, see the [Main Project Documentation](../README.md).

## Related Documentation

- **[Main Project Documentation](../README.md)**: Comprehensive documentation of machine learning models, methodology, and implementation
- **[About This Project](../ABOUT_THIS_PROJECT.md)**: Project overview, business case, value proposition, and competitive advantages
- **[Frontend Documentation](../modelling_and_prediction/frontend/FRONTEND.md)**: Documentation of the web interface and user-facing features
- **[Fire Detection Documentation](../fire-detection/FIRE_DETECTION.md)**: Documentation of automated fire detection system
