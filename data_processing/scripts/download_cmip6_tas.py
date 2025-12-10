#!/usr/bin/env python
"""
Download CMIP6 near-surface air temperature (tas) data from Copernicus CDS.

This script downloads MIROC6 monthly tas for:
- Historical: 1992-2014 (baseline and training period)
- SSP2-4.5: 2015-2100 (moderate emissions)
- SSP5-8.5: 2015-2100 (high emissions)

Geographical coverage: Continental US (North: 72°, South: 18°, West: -170°, East: -50°)

Requirements:
    pip install cdsapi

Setup:
    Create ~/.cdsapirc with:
    url: https://cds.climate.copernicus.eu/api
    key: 3c0feaf1-f3eb-477e-a577-63445b16b883
"""
import logging
from pathlib import Path

import cdsapi

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Common request parameters
COMMON_PARAMS = {
    "temporal_resolution": "monthly",
    "variable": "near_surface_air_temperature",
    "model": "miroc6",
    "month": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
    "area": [72, -170, 18, -50],  # [North, West, South, East] - Continental US
}


def download_experiment(client, experiment, years, output_file):
    """
    Download CMIP6 data for a specific experiment.
    
    Args:
        client: CDS API client
        experiment: Experiment name (e.g., 'historical', 'ssp2_4_5')
        years: List of years to download
        output_file: Path to save NetCDF file
    """
    logger.info(f"Downloading {experiment} experiment ({years[0]}-{years[-1]})...")
    
    request = {
        **COMMON_PARAMS,
        "experiment": experiment,
        "year": years,
    }
    
    try:
        result = client.retrieve("projections-cmip6", request)
        
        # Use direct download with shorter timeout
        import urllib.request
        import shutil
        import zipfile
        
        # Get the download URL
        download_url = result.location
        logger.info(f"Downloading from: {download_url}")
        
        # Download with urllib (more reliable for large files)
        with urllib.request.urlopen(download_url, timeout=300) as response:
            with open(output_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        
        logger.info(f"✓ Downloaded {output_file.name} ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
        
        # Extract ZIP archive (CDS returns ZIP files)
        if zipfile.is_zipfile(output_file):
            logger.info(f"Extracting NetCDF files from {output_file.name}...")
            with zipfile.ZipFile(output_file, 'r') as zip_ref:
                # Extract only .nc files
                nc_files = [f for f in zip_ref.namelist() if f.endswith('.nc')]
                for nc_file in nc_files:
                    zip_ref.extract(nc_file, output_file.parent)
                    logger.info(f"  ✓ Extracted {nc_file}")
        
    except Exception as e:
        logger.error(f"✗ Failed to download {experiment}: {e}")
        raise


def main():
    """Download all required CMIP6 tas data."""
    logger.info("Starting CMIP6 tas data download from Copernicus CDS...")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    # Initialize CDS API client
    client = cdsapi.Client()
    
    # Define datasets to download
    datasets = [
        {
            "experiment": "historical",
            "years": [str(y) for y in range(1992, 2015)],  # 1992-2014 (our data range)
            "filename": "tas_Amon_MIROC6_historical_1992-2014.nc",
        },
        {
            "experiment": "ssp2_4_5",
            "years": [str(y) for y in range(2015, 2101)],  # 2015-2100
            "filename": "tas_Amon_MIROC6_ssp245_2015-2100.nc",
        },
        {
            "experiment": "ssp5_8_5",
            "years": [str(y) for y in range(2015, 2101)],  # 2015-2100
            "filename": "tas_Amon_MIROC6_ssp585_2015-2100.nc",
        },
    ]
    
    # Download each dataset
    for dataset in datasets:
        output_file = OUTPUT_DIR / dataset["filename"]
        
        # Skip if already exists
        if output_file.exists():
            logger.info(f"⊙ Skipping {dataset['filename']} (already exists)")
            continue
        
        download_experiment(
            client=client,
            experiment=dataset["experiment"],
            years=dataset["years"],
            output_file=output_file,
        )
    
    logger.info("\n" + "="*60)
    logger.info("Download complete!")
    logger.info("="*60)
    logger.info(f"Files saved to: {OUTPUT_DIR}")
    logger.info("\nNext steps:")
    logger.info("  1. Run data preparation: uv run python main.py --prepare")
    logger.info("  2. Train models: uv run python main.py --train")
    logger.info("  3. Generate projections: uv run python main.py --project")


if __name__ == "__main__":
    main()
