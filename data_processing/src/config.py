"""
Configuration module for wildfire risk prediction project.
Centralizes paths, parameters, and settings.
"""
from pathlib import Path
from dataclasses import dataclass
from typing import List

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure directories exist
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Raw data files
# Wildfire database (1.88M US Wildfires from Kaggle)
WILDFIRE_DB = RAW_DATA_DIR / "FPA_FOD_20170508.sqlite"

# Berkeley Earth Temperature Data
TEMP_BY_CITY = RAW_DATA_DIR / "GlobalLandTemperaturesByCity.csv"
TEMP_BY_STATE = RAW_DATA_DIR / "GlobalLandTemperaturesByState.csv"
TEMP_BY_COUNTRY = RAW_DATA_DIR / "GlobalLandTemperaturesByCountry.csv"
GLOBAL_TEMPS = RAW_DATA_DIR / "GlobalTemperatures.csv"

# Processed data files
PROCESSED_FEATURES = PROCESSED_DATA_DIR / "wildfire_features.parquet"
TRAIN_DATA = PROCESSED_DATA_DIR / "train_data.parquet"
TEST_DATA = PROCESSED_DATA_DIR / "test_data.parquet"

# Model artifacts
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOGISTIC_MODEL = MODELS_DIR / "logistic_regression.joblib"
LIGHTGBM_MODEL = MODELS_DIR / "lightgbm_model.joblib"
FEATURE_NAMES = MODELS_DIR / "feature_names.json"


@dataclass
class DataConfig:
    """Configuration for data processing."""
    
    # Geographic aggregation level
    aggregation_level: str = "city"  # 'city', 'county', or 'state'
    
    # Date range for historical analysis
    start_year: int = 1992
    end_year: int = 2015
    
    # Temperature data filtering
    temperature_countries: List[str] = None
    
    # Feature engineering
    lag_months: List[int] = None  # e.g., [1, 3, 6, 12]
    rolling_windows: List[int] = None  # e.g., [3, 6, 12] months
    
    # Target variable
    target_column: str = "fire_occurred"
    
    def __post_init__(self):
        if self.temperature_countries is None:
            self.temperature_countries = ["United States"]
        if self.lag_months is None:
            self.lag_months = [1, 3, 6, 12]
        if self.rolling_windows is None:
            self.rolling_windows = [3, 6, 12]


@dataclass
class ModelConfig:
    """Configuration for model training."""
    
    # Train/test split
    test_size: float = 0.2
    random_state: int = 42
    
    # Model hyperparameters - Logistic Regression
    logistic_max_iter: int = 1000
    logistic_solver: str = "liblinear"
    logistic_class_weight: str = "balanced"
    
    # Model hyperparameters - LightGBM
    lgbm_n_estimators: int = 500
    lgbm_max_depth: int = 7
    lgbm_learning_rate: float = 0.05
    lgbm_num_leaves: int = 31
    lgbm_min_child_samples: int = 20
    lgbm_subsample: float = 0.8
    lgbm_colsample_bytree: float = 0.8
    lgbm_class_weight: str = "balanced"
    
    # Evaluation
    cv_folds: int = 5
    
    # Model selection
    primary_metric: str = "pr_auc"  # 'pr_auc', 'brier_score', 'roc_auc'


@dataclass
class ProjectionConfig:
    """Configuration for future climate projections."""
    
    # CMIP6 scenarios to evaluate
    scenarios: List[str] = None
    
    # Projection time periods
    projection_years: List[int] = None
    
    # Warming scenarios for visualization
    warming_levels: List[float] = None  # e.g., [2.0, 4.0] degrees C
    
    def __post_init__(self):
        if self.scenarios is None:
            self.scenarios = ["SSP2-4.5", "SSP5-8.5"]
        if self.projection_years is None:
            self.projection_years = [2040, 2060, 2080, 2100]
        if self.warming_levels is None:
            self.warming_levels = [2.0, 4.0]


# Default configurations
DEFAULT_DATA_CONFIG = DataConfig()
DEFAULT_MODEL_CONFIG = ModelConfig()
DEFAULT_PROJECTION_CONFIG = ProjectionConfig()
