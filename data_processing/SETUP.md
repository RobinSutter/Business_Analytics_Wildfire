# Setup and Installation Guide

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Optional: GDAL/GEOS (for full geospatial functionality)

```bash
brew install gdal geos
```

If you don't have Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Quick Start

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and setup the project

```bash
cd wildfire-risk
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

### 3. Verify installation

```bash
uv run python -c "from src import config; print('✓ Setup successful!')"
```

### 4. Run data processing scripts

**Approach 1: Individual fire-level matching**
```bash
uv run python src/merge_fire_temperature.py
```

**Approach 2: Aggregated panel creation**
```bash
uv run python src/data_preparation.py
```

**Analysis and visualization**
```bash
uv run python src/analyze_fire_temperature.py
```

## Development Setup

Install development dependencies:

```bash
uv sync --dev
```

This includes:
- Jupyter for notebooks
- pytest for testing
- black and ruff for code formatting

## Jupyter Notebooks

To use the analysis notebooks:

```bash
# Make sure the kernel can see the project environment
uv run jupyter notebook notebooks/
```

Available notebooks:
- `correlation_analysis.ipynb` - Correlation analysis between fires and temperature
- `data_preparation_Temperatures.ipynb` - Temperature data preparation
- `fire_occurrence_correlation.ipynb` - Fire occurrence correlation analysis

Or in VS Code:
1. Open the notebook
2. Select kernel: Python 3.11.x ('.venv': venv)
3. Run cells

## Data Setup

### Required Data Files

Place these files in `data/raw/`:

1. **Wildfire Database** (1.88M US Wildfires):
   - `FPA_FOD_20170508.sqlite`
   - Download from [Kaggle](https://www.kaggle.com/rtatman/188-million-us-wildfires)

2. **Berkeley Earth Temperature Data**:
   - `GlobalLandTemperaturesByCity.csv`
   - Download from [Kaggle](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data)

3. **CMIP6 Climate Projections** (optional):
   - Download using the provided script (see CMIP6 Data Download section below)
   - Required for future risk projections and climate scenario analysis

## Project Structure

```
data_processing/
├── src/
│   ├── config.py                    # Configuration and paths
│   ├── data_preparation.py          # Aggregated panel approach
│   ├── merge_fire_temperature.py    # Individual fire-level matching
│   └── analyze_fire_temperature.py   # Statistical analysis
├── scripts/
│   ├── download_cmip6_tas.py        # CMIP6 data download
│   └── cdsapirc.example              # CDS API credentials template
├── notebooks/                        # Jupyter notebooks
├── data/
│   ├── raw/                          # Input datasets (SQLite DB, CSVs)
│   └── processed/                    # Processed datasets
└── reports/                           # Analysis outputs and visualizations

```

## Common Issues

### "Processed data not found"

Run data preparation scripts first:
```bash
# Individual fire-level matching
uv run python src/merge_fire_temperature.py

# Or aggregated panel creation
uv run python src/data_preparation.py
```

### Import errors in notebooks

Make sure to use the project's virtual environment as the kernel:
- In Jupyter: Kernel → Change Kernel → Python 3.11.x ('.venv': venv)
- In VS Code: Select kernel from top-right of notebook

## Next Steps

1. Run data preparation: 
   - `uv run python src/merge_fire_temperature.py` (individual fire-level)
   - `uv run python src/data_preparation.py` (aggregated panel)
2. Run analysis: `uv run python src/analyze_fire_temperature.py`
3. Explore notebooks: Open notebooks in `notebooks/` directory
4. Review results in `reports/` directory
5. For modeling: See `modelling_and_prediction/` directory

## CMIP6 Data Download

CMIP6 climate projection data can be downloaded for future risk projections and analysis.

### Overview

The project uses **MIROC6** model data for near-surface air temperature (tas):
- **Historical**: 1992-2014 (matches wildfire data period)
- **SSP2-4.5**: 2015-2100 (moderate emissions scenario)
- **SSP5-8.5**: 2015-2100 (high emissions scenario)

Geographic coverage: Continental US (72°N to 18°N, 170°W to 50°W)

### Quick Start

#### 1. Get CDS API Credentials

1. Create a free account at [CDS](https://cds.climate.copernicus.eu/)
2. Go to your [profile page](https://cds.climate.copernicus.eu/user)
3. Copy your API key (looks like: `12345:abcd-1234-5678-efgh`)

#### 2. Setup API Credentials

```bash
# Copy the example file
cp scripts/cdsapirc.example ~/.cdsapirc

# Edit with your credentials
nano ~/.cdsapirc
```

Your `~/.cdsapirc` should look like:
```
url: https://cds.climate.copernicus.eu/api
key: YOUR-UID:YOUR-API-KEY
```

**Note**: The provided key in the example is a placeholder. Replace with your own.

#### 3. Install Dependencies

```bash
uv sync  # Installs cdsapi and other dependencies
```

#### 4. Download Data

```bash
uv run python scripts/download_cmip6_tas.py
```

Expected output:
```
INFO - Starting CMIP6 tas data download from Copernicus CDS...
INFO - Output directory: /path/to/data/raw
INFO - Downloading historical experiment (1992-2014)...
INFO - ✓ Downloaded tas_Amon_MIROC6_historical_1992-2014.nc (234.5 MB)
INFO - Downloading ssp2_4_5 experiment (2015-2100)...
INFO - ✓ Downloaded tas_Amon_MIROC6_ssp245_2015-2100.nc (1.2 GB)
INFO - Downloading ssp5_8_5 experiment (2015-2100)...
INFO - ✓ Downloaded tas_Amon_MIROC6_ssp585_2015-2100.nc (1.2 GB)
INFO - Download complete!
```

**Download time**: 15-30 minutes depending on CDS queue (total ~2.6 GB)

### What Gets Downloaded

#### File Structure
```
data/raw/
├── tas_Amon_MIROC6_historical_1992-2014.nc    # Historical baseline
├── tas_Amon_MIROC6_ssp245_2015-2100.nc        # SSP2-4.5 scenario
└── tas_Amon_MIROC6_ssp585_2015-2100.nc        # SSP5-8.5 scenario
```

#### File Contents
Each NetCDF file contains:
- **Variable**: `tas` (near-surface air temperature in Kelvin)
- **Dimensions**: `time`, `lat`, `lon`
- **Temporal resolution**: Monthly
- **Spatial resolution**: ~1.4° × 1.4° (~150km)
- **Coverage**: Continental US region

### Using Different Models or Scenarios

To download data from other CMIP6 models, edit `scripts/download_cmip6_tas.py`:

```python
COMMON_PARAMS = {
    "model": "ec-earth3",  # Change model here
    # ... other params
}
```

Available models (examples):
- `miroc6` (Japan - default, good balance of resolution and availability)
- `ec-earth3` (Europe)
- `mpi-esm1-2-lr` (Germany - good spatial detail)
- `ukesm1-0-ll` (UK - comprehensive ESM)
- See full list: [CDS Models](https://cds.climate.copernicus.eu/datasets/projections-cmip6?tab=overview)

Additional scenarios:
- `ssp1_2_6`: Low emissions (1.5-2°C warming)
- `ssp3_7_0`: Medium-high emissions
- `ssp1_1_9`: Very low emissions (Paris Agreement best case)

### Troubleshooting

#### "Connection refused" or API errors
- Verify your API key is correct in `~/.cdsapirc`
- Check CDS service status: https://cds.climate.copernicus.eu/

#### "Request queued for a long time"
- CDS has queues during peak hours (EU business hours)
- Try downloading during off-peak times (late evening UTC)
- Large requests can take 30+ minutes

#### "Out of disk space"
- Each scenario file is ~400MB-1.2GB
- Ensure at least 5GB free space in `data/raw/`

#### File already exists
The script skips existing files automatically. To re-download:
```bash
rm data/raw/tas_Amon_MIROC6_*.nc
uv run python scripts/download_cmip6_tas.py
```

### Manual Download (Alternative)

If the script fails, download manually via the web interface:

1. Go to [CDS CMIP6 Dataset](https://cds.climate.copernicus.eu/datasets/projections-cmip6)
2. Select:
   - **Temporal resolution**: Monthly
   - **Experiment**: Historical (or SSP scenario)
   - **Variable**: Near-surface air temperature
   - **Model**: MIROC6
   - **Years**: Select appropriate range
   - **Months**: All (01-12)
   - **Area**: Custom (North: 72, West: -170, South: 18, East: -50)
3. Click "Download"
4. Save to `data/raw/` with naming: `tas_Amon_MIROC6_{scenario}_{years}.nc`

### Data Citation

When using CMIP6 data, cite:

**MIROC6 Model**:
> Tatebe, H., et al. (2019). Description and basic evaluation of simulated mean state, internal variability, and climate sensitivity in MIROC6. Geoscientific Model Development, 12(7), 2727-2765.

**CMIP6 Archive**:
> Eyring, V., et al. (2016). Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) experimental design and organization. Geoscientific Model Development, 9(5), 1937-1958.

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [Project README](README.md)
- [Berkeley Earth Data](https://berkeleyearth.org/data/)
- [CDS API Documentation](https://cds.climate.copernicus.eu/api-how-to)
- [CMIP6 Data Guide](https://pcmdi.llnl.gov/CMIP6/)
- [cdsapi Python Package](https://pypi.org/project/cdsapi/)
- [MIROC6 Model Documentation](https://www.miroc-gcm.jp/)
