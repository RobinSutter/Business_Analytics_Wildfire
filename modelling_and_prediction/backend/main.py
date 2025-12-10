"""
FSP Fire Size Predictor - FastAPI Backend
Connects the React frontend to the XGBoost fire prediction model
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from pathlib import Path
import os
import time
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Path to model files
BASE_DIR = Path(__file__).parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks" / "models"

# Size prediction model (ensemble XGBoost)
SIZE_MODEL_PATH = NOTEBOOKS_DIR / "ensemble_xgb_model.joblib"

# Risk classification model
RISK_MODEL_PATH = NOTEBOOKS_DIR / "fire_size" / "risk_classifier_custom_weights.joblib"

# Paths for fire map generation
MAPS_DIR = BASE_DIR / "frontend" / "maps"
COUNTIES_FILE = BASE_DIR / "data" / "processed" / "US_COUNTIES.csv"
POPULATION_FILE = BASE_DIR / "data" / "processed" / "county_population_2023.csv"

app = FastAPI(
    title="FSP Fire Size Predictor API",
    description="AI-powered wildfire size prediction for emergency response teams",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for generated maps
app.mount("/maps", StaticFiles(directory=str(MAPS_DIR)), name="maps")

# Global variables for models and encoders
size_model = None  # Ensemble XGBoost for size prediction
risk_model = None  # Risk classifier
risk_metadata = None
le_cause = None
le_state = None
le_season = None

# Global cache for county data (loaded once)
county_gdf_cache = None


def initialize_model():
    """Load models and create label encoders at startup"""
    global size_model, risk_model, risk_metadata, le_cause, le_state, le_season
    
    try:
        print(f"Loading size prediction model from: {SIZE_MODEL_PATH}")
        size_model = joblib.load(SIZE_MODEL_PATH)
        
        print(f"Loading risk classification model from: {RISK_MODEL_PATH}")
        risk_model = joblib.load(RISK_MODEL_PATH)
        
        # Create label encoders with standard US fire data classes
        print("Creating label encoders...")
        
        le_cause = LabelEncoder()
        le_cause.classes_ = np.array([
            'Arson', 'Camping', 'Children', 'Debris and Open Burning', 'Equipment and Vehicle Use',
            'Fireworks', 'Lightning', 'Miscellaneous', 'Missing data/not specified/undetermined',
            'Powerline', 'Railroad', 'Recreation and Ceremony', 'Smoking'
        ])
        
        le_state = LabelEncoder()
        le_state.classes_ = np.array([
            'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'IA', 'ID', 'IL',
            'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND',
            'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'SD',
            'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY'
        ])
        
        le_season = LabelEncoder()
        le_season.classes_ = np.array(['Fall', 'Spring', 'Summer', 'Winter'])
        
        # Create feature names list (35 features for ensemble model)
        risk_metadata = {
            'feature_names': [
                # Base features (26)
                'mean_temp', 'max_temp', 'min_temp', 'temp_range', 'discovery_temp',
                'temp_range_mean', 'temp_range_max', 'mean_max_temp', 'discovery_mean_temp',
                'mean_temp_sq', 'max_temp_sq', 'temp_range_sq',
                'LATITUDE', 'LONGITUDE', 'lat_bin', 'lon_bin',
                'month', 'day_of_year', 'month_sin', 'month_cos', 'day_sin', 'day_cos',
                'cause_encoded', 'state_encoded', 'season_encoded', 'num_cities',
                # Advanced features (9) - for ensemble model
                'ffmc_estimate', 'dmc_estimate', 'dc_estimate',
                'spread_rate_proxy', 'intensity_proxy', 'spread_potential',
                'season_severity', 'temp_anomaly', 'high_risk_region'
            ]
        }
        
        print("✅ Models and label encoders loaded successfully!")
        print(f"   Size Model: {type(size_model).__name__}")
        print(f"   Risk Model: {type(risk_model).__name__}")
        print(f"   Features: {len(risk_metadata['feature_names'])}")
        print(f"   Cause classes: {len(le_cause.classes_)}")
        print(f"   State classes: {len(le_state.classes_)}")
        print(f"   Season classes: {len(le_season.classes_)}")
        
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        raise


# Initialize model at startup
@app.on_event("startup")
async def startup_event():
    initialize_model()


# Pydantic models for request/response
class PredictionRequest(BaseModel):
    mean_temp: float = Field(..., ge=-30, le=55, description="Mean temperature in Celsius")
    max_temp: float = Field(..., ge=-20, le=60, description="Maximum temperature in Celsius")
    min_temp: float = Field(..., ge=-40, le=50, description="Minimum temperature in Celsius")
    discovery_temp: float = Field(..., ge=-30, le=55, description="Temperature at discovery time")
    latitude: float = Field(..., ge=20, le=50, description="Latitude (20-50 for USA)")
    longitude: float = Field(..., ge=-125, le=-65, description="Longitude (-125 to -65 for USA)")
    state: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    cause: str = Field(..., description="Fire cause category")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    day_of_year: int = Field(..., ge=1, le=366, description="Day of year (1-366)")
    season: str = Field(..., description="Season (Winter, Spring, Summer, Fall)")
    num_cities: int = Field(default=0, ge=0, le=100, description="Number of nearby cities/towns")
    wind_speed: float = Field(default=0, ge=0, le=100, description="Wind speed (optional)")
    wind_direction: float = Field(default=0, ge=0, le=360, description="Wind direction in degrees (optional)")


class PredictionResponse(BaseModel):
    predicted_acres: float
    predicted_hectares: float
    risk_score: float
    risk_category: str
    risk_color: str
    fire_size_class: str
    response_level: str
    resources: str
    actions: list[str]
    estimated_duration: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_type: str = None
    message: str = None


# Fire Map Request/Response Models
class FireMapRequest(BaseModel):
    latitude: float = Field(..., ge=20, le=50, description="Latitude (20-50 for USA)")
    longitude: float = Field(..., ge=-125, le=-65, description="Longitude (-125 to -65 for USA)")
    radius_km: float = Field(..., ge=1, le=100, description="Fire radius in kilometers")
    wind_speed_mph: float = Field(default=10, ge=0, le=100, description="Wind speed in mph")
    wind_direction_deg: float = Field(default=0, ge=0, le=360, description="Wind direction in degrees (0=N, 90=E)")


class AffectedCounty(BaseModel):
    county: str
    state: str
    population: int
    affected_share: float
    contributing_pop: int


class FireMapResponse(BaseModel):
    map_url: str
    total_population: int
    affected_counties: list[AffectedCounty]
    radius_km: float
    center_lat: float
    center_lon: float


# Response recommendations mapping
RECOMMENDATIONS = {
    "Very Low Risk": {
        "response_level": "Minimal Response",
        "resources": "1-2 engines, local crew",
        "actions": [
            "Monitor fire development",
            "Establish fire perimeter",
            "Assess containment strategy"
        ],
        "estimated_duration": "2-6 hours"
    },
    "Low Risk": {
        "response_level": "Standard Response",
        "resources": "2-4 engines, 10-20 personnel",
        "actions": [
            "Establish firebreaks",
            "Deploy initial attack crews",
            "Monitor weather conditions",
            "Coordinate with local authorities"
        ],
        "estimated_duration": "6-24 hours"
    },
    "Moderate Risk": {
        "response_level": "Enhanced Response",
        "resources": "5-10 engines, 30-50 personnel, air support",
        "actions": [
            "Activate incident command system",
            "Request mutual aid if needed",
            "Establish evacuation plans",
            "Deploy heavy equipment",
            "Continuous aerial surveillance"
        ],
        "estimated_duration": "1-3 days"
    },
    "High Risk": {
        "response_level": "Major Response - ALERT",
        "resources": "15+ engines, 100+ personnel, multiple aircraft",
        "actions": [
            "🚨 IMMEDIATE evacuation planning",
            "Deploy all available resources",
            "Request state/federal assistance",
            "Establish incident management team",
            "24/7 operations",
            "Public safety alerts"
        ],
        "estimated_duration": "3-7 days"
    },
    "Critical Risk": {
        "response_level": "⚠️ EMERGENCY RESPONSE - CRITICAL ⚠️",
        "resources": "Maximum mobilization: 20+ engines, 200+ personnel, air tankers, helicopters",
        "actions": [
            "🚨 IMMEDIATE EVACUATIONS - PRIORITY",
            "Activate state/federal emergency response",
            "Full incident management team",
            "Deploy all available air assets",
            "Establish unified command",
            "Request National Guard if needed",
            "Continuous media coordination"
        ],
        "estimated_duration": "1-2 weeks+"
    }
}


def prepare_features(request: PredictionRequest) -> pd.DataFrame:
    """
    Prepare feature vector for prediction
    Must match EXACTLY the features and order used in training
    """
    temp_range = request.max_temp - request.min_temp
    
    # Encode categorical variables using TRAINED encoders
    try:
        cause_encoded = le_cause.transform([request.cause])[0]
    except:
        # If cause not in training set, use most common (Miscellaneous)
        cause_encoded = le_cause.transform(['Miscellaneous'])[0]
        
    try:
        state_encoded = le_state.transform([request.state.upper()])[0]
    except:
        raise HTTPException(status_code=400, detail=f"Invalid state code: {request.state}")
    
    try:
        season_encoded = le_season.transform([request.season])[0]
    except:
        raise HTTPException(status_code=400, detail=f"Invalid season: {request.season}")
    
    # Calculate lat/lon bins (same as training)
    lat_bin = int((request.latitude - 20.0) / 30.0 * 10)
    lat_bin = max(0, min(9, lat_bin))
    
    lon_bin = int((request.longitude + 125.0) / 60.0 * 10)
    lon_bin = max(0, min(9, lon_bin))
    
    # Create feature dictionary in EXACT order from metadata
    # Order MUST match: metadata['feature_names']
    features = {
        # Temperature features
        'mean_temp': request.mean_temp,
        'max_temp': request.max_temp,
        'min_temp': request.min_temp,
        'temp_range': temp_range,
        'discovery_temp': request.discovery_temp,
        
        # Temperature interactions
        'temp_range_mean': temp_range * request.mean_temp,
        'temp_range_max': temp_range * request.max_temp,
        'mean_max_temp': request.mean_temp * request.max_temp,
        'discovery_mean_temp': request.discovery_temp * request.mean_temp,
        
        # Temperature polynomials
        'mean_temp_sq': request.mean_temp ** 2,
        'max_temp_sq': request.max_temp ** 2,
        'temp_range_sq': temp_range ** 2,
        
        # Location features
        'LATITUDE': request.latitude,
        'LONGITUDE': request.longitude,
        'lat_bin': lat_bin,
        'lon_bin': lon_bin,
        
        # Temporal features
        'month': request.month,
        'day_of_year': request.day_of_year,
        
        # Cyclical time features
        'month_sin': np.sin(2 * np.pi * request.month / 12),
        'month_cos': np.cos(2 * np.pi * request.month / 12),
        'day_sin': np.sin(2 * np.pi * request.day_of_year / 365),
        'day_cos': np.cos(2 * np.pi * request.day_of_year / 365),
        
        # Categorical encodings
        'cause_encoded': cause_encoded,
        'state_encoded': state_encoded,
        'season_encoded': season_encoded,
        
        # Other features
        'num_cities': request.num_cities,
        
        # ADVANCED FEATURES (for ensemble model - 9 additional features)
        # Canadian Fire Weather Index (FWI) approximations
        'ffmc_estimate': (request.mean_temp + 10) * 2.5,
        'dmc_estimate': request.mean_temp * request.month * 0.8,
        'dc_estimate': request.mean_temp ** 1.5,
        
        # Fire behavior proxies
        'spread_rate_proxy': (request.max_temp / 10) * (temp_range + 1),
        'intensity_proxy': request.mean_temp ** 2 / (abs(request.latitude) + 1),
        'spread_potential': temp_range * request.mean_temp * 0.1,
        
        # Seasonal and regional risk factors
        'season_severity': (1 if request.season in ['Summer', 'Fall'] else 0) * request.mean_temp,
        'temp_anomaly': (request.mean_temp - 20.0) / 10.0,  # Normalized temp anomaly (assuming global mean ~20°C)
        'high_risk_region': int((request.latitude >= 32) and (request.latitude <= 45) and 
                                (request.longitude >= -125) and (request.longitude <= -100))
    }
    
    # Create DataFrame with features in the EXACT order from training
    # First try ensemble model features (35 features), fallback to base features (26 features)
    try:
        features_df = pd.DataFrame([features])
        return features_df
    except Exception as e:
        print(f"Warning: Could not create feature DataFrame: {e}")
        raise


def calculate_risk_score(predicted_acres: float) -> float:
    """Calculate risk score (0-100) from predicted fire size"""
    if predicted_acres < 10:
        risk_score = 10 + (predicted_acres / 10) * 10
    elif predicted_acres < 100:
        risk_score = 20 + ((predicted_acres - 10) / 90) * 20
    elif predicted_acres < 1000:
        risk_score = 40 + ((predicted_acres - 100) / 900) * 20
    elif predicted_acres < 10000:
        risk_score = 60 + ((predicted_acres - 1000) / 9000) * 20
    else:
        risk_score = 80 + min(20, ((predicted_acres - 10000) / 100000) * 20)
    
    return min(100, max(0, risk_score))


def get_risk_category(risk_score: float) -> tuple[str, str]:
    """Get risk category and color from risk score"""
    if risk_score < 20:
        return "Very Low Risk", "#2ECC71"
    elif risk_score < 40:
        return "Low Risk", "#3498DB"
    elif risk_score < 60:
        return "Moderate Risk", "#F39C12"
    elif risk_score < 80:
        return "High Risk", "#E67E22"
    else:
        return "Critical Risk", "#E74C3C"


def get_fire_size_class(predicted_acres: float) -> str:
    """Get NWCG fire size class (National Wildfire Coordinating Group)"""
    if predicted_acres < 0.25:
        return "A"  # 0-0.25 acres
    elif predicted_acres < 10:
        return "B"  # 0.25-9.9 acres
    elif predicted_acres < 100:
        return "C"  # 10-99 acres
    elif predicted_acres < 300:
        return "D"  # 100-299 acres
    elif predicted_acres < 1000:
        return "E"  # 300-999 acres
    elif predicted_acres < 5000:
        return "F"  # 1000-4999 acres
    else:
        return "G"  # 5000+ acres


# API Endpoints
@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with API info"""
    return {
        "message": "FSP Fire Size Predictor API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "predict": "/predict"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Check API and model health"""
    if size_model is None or risk_model is None:
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            message="Models not loaded"
        )
    
    return HealthResponse(
        status="ok",
        model_loaded=True,
        model_type="Ensemble XGBoost + Risk Classifier",
        message="API and models are operational"
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict_fire_size(request: PredictionRequest):
    """
    Predict wildfire size and risk level using two models:
    1. Ensemble XGBoost for size prediction
    2. Risk classifier for risk assessment
    
    Takes environmental conditions and location data, returns:
    - Predicted fire size in acres and hectares
    - Risk score (0-100) and category
    - Fire size classification (A-G)
    - Emergency response recommendations
    """
    
    if size_model is None or risk_model is None:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please contact administrator."
        )
    
    try:
        print(f"\n🔥 === NEW PREDICTION REQUEST ===")
        print(f"   Location: {request.latitude}, {request.longitude} ({request.state})")
        print(f"   Temperature: {request.mean_temp}°C (range: {request.min_temp}-{request.max_temp}°C)")
        print(f"   Cause: {request.cause}, Season: {request.season}")
        
        # Prepare features (includes all 35 features)
        features_df_full = prepare_features(request)
        print(f"   ✅ Features prepared: {features_df_full.shape}")
        
        # 1. SIZE PREDICTION using Ensemble XGBoost (needs all 35 features)
        print(f"\n📊 MODEL 1: Size Prediction (Ensemble XGBoost)")
        log_pred = size_model.predict(features_df_full)[0]
        pred_acres = np.expm1(log_pred)
        pred_acres = float(pred_acres)
        print(f"   → Predicted size: {pred_acres:.1f} acres")
        
        # 2. RISK SCORING - Combine size prediction with environmental factors
        print(f"\n⚠️  RISK ASSESSMENT: Calculating operational risk score")
        
        # Base risk from predicted fire size (NWCG classes)
        if pred_acres < 0.25:
            size_risk = 5      # Class A
        elif pred_acres < 10:
            size_risk = 15     # Class B
        elif pred_acres < 100:
            size_risk = 30     # Class C
        elif pred_acres < 300:
            size_risk = 45     # Class D
        elif pred_acres < 1000:
            size_risk = 60     # Class E
        elif pred_acres < 5000:
            size_risk = 75     # Class F
        else:
            size_risk = 85     # Class G
        
        print(f"   → Size risk component: {size_risk}/100 (based on {pred_acres:.1f} acres)")
        
        # Environmental risk factors (0-30 points)
        env_risk = 0
        
        # Temperature factor (0-10 points)
        if request.mean_temp > 35:
            env_risk += 10
        elif request.mean_temp > 30:
            env_risk += 8
        elif request.mean_temp > 25:
            env_risk += 6
        elif request.mean_temp > 20:
            env_risk += 4
        elif request.mean_temp > 15:
            env_risk += 2
        
        # Wind factor (0-10 points)
        wind_speed = request.wind_speed if hasattr(request, 'wind_speed') else 0
        if wind_speed > 30:
            env_risk += 10
        elif wind_speed > 20:
            env_risk += 8
        elif wind_speed > 15:
            env_risk += 6
        elif wind_speed > 10:
            env_risk += 4
        elif wind_speed > 5:
            env_risk += 2
        
        # Location risk factor (0-10 points)
        high_risk_states = ['CA', 'NV', 'AZ', 'NM', 'TX', 'OR', 'WA', 'ID', 'MT', 'WY', 'CO', 'UT']
        if request.state.upper() in high_risk_states:
            env_risk += 5
        
        # Summer season boost
        if request.season == 'Summer':
            env_risk += 5
        
        # Human-caused fires are higher risk
        human_causes = ['Arson', 'Equipment Use', 'Smoking', 'Campfire', 'Children', 'Railroad', 'Fireworks', 'Debris Burning']
        if request.cause in human_causes:
            env_risk += 3
        
        print(f"   → Environmental risk component: {env_risk}/30")
        
        # Combined risk score (capped at 100)
        risk_score = min(100, size_risk + env_risk)
        
        # Determine risk category from combined score
        risk_category, _ = get_risk_category(risk_score)
        
        print(f"   → TOTAL RISK SCORE: {risk_score}/100")
        print(f"   → Risk category: {risk_category}")
        
        # Get color for risk category
        _, risk_color = get_risk_category(risk_score)
        fire_size_class = get_fire_size_class(pred_acres)
        
        # Get recommendations
        recommendations = RECOMMENDATIONS.get(risk_category, RECOMMENDATIONS["Moderate Risk"])
        
        print(f"\n✅ PREDICTION COMPLETE")
        print(f"   Size: {pred_acres:.1f} acres (Class {fire_size_class})")
        print(f"   Risk: {risk_category} ({risk_score:.1f}/100)")
        print(f"   Response: {recommendations['response_level']}")
        print(f"=" * 60 + "\n")
        
        return PredictionResponse(
            predicted_acres=round(pred_acres, 1),
            predicted_hectares=round(pred_acres * 0.404686, 1),
            risk_score=round(risk_score, 1),
            risk_category=risk_category,
            risk_color=risk_color,
            fire_size_class=fire_size_class,
            response_level=recommendations["response_level"],
            resources=recommendations["resources"],
            actions=recommendations["actions"],
            estimated_duration=recommendations["estimated_duration"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"\n❌ PREDICTION ERROR:")
        print(error_traceback)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@app.get("/api/population/{lat}/{lng}/{radius_km}")
async def get_population_impact(lat: float, lng: float, radius_km: float):
    """
    Get population impact within radius of fire location
    Currently returns estimated data - will integrate with county data
    
    Parameters:
    - lat: Latitude of fire center
    - lng: Longitude of fire center  
    - radius_km: Radius in kilometers
    
    Returns GeoJSON with affected counties and population data
    (Placeholder implementation - integrate your friend's GeoPandas logic here)
    """
    try:
        # Placeholder: rough population density estimate
        # TODO: Integrate with US_COUNTIES.csv and county_population_2023.csv
        area_sq_km = np.pi * radius_km * radius_km
        avg_density = 100  # people per sq km (placeholder)
        estimated_population = int(area_sq_km * avg_density)
        
        return {
            "type": "FeatureCollection",
            "properties": {
                "center": {"lat": lat, "lng": lng},
                "radius_km": radius_km,
                "estimated_population": estimated_population,
                "area_sq_km": round(area_sq_km, 2)
            },
            "features": [
                # TODO: Add actual county GeoJSON features here
                # Each feature should have:
                # - geometry: county polygon
                # - properties: {name, state, population, affected_fraction, contribution}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Population calculation error: {str(e)}")


# ============================================================
# FIRE MAP GENERATION ENDPOINT
# ============================================================

def load_county_data_cached():
    """Load county data with caching for performance"""
    global county_gdf_cache
    
    if county_gdf_cache is not None:
        return county_gdf_cache
    
    try:
        # Import the map generation module
        from modelling_and_prediction.frontend.maps.county_map_with_wind import load_county_data
        
        county_gdf_cache = load_county_data(str(COUNTIES_FILE), str(POPULATION_FILE))
        print(f"✅ County data loaded: {len(county_gdf_cache)} counties")
        return county_gdf_cache
    except Exception as e:
        print(f"❌ Error loading county data: {e}")
        raise


@app.post("/api/generate-fire-map", response_model=FireMapResponse, tags=["Fire Map"])
async def generate_fire_map(request: FireMapRequest):
    """
    Generate interactive fire spread map with wind animation
    
    Takes fire location and conditions, generates a Folium map with:
    - Wind-based elliptical fire spread visualization
    - Animated fire progression
    - County population impact analysis
    - Wind particle animation
    
    Returns URL to generated map and population statistics.
    """
    try:
        # Import map generation functions
        from modelling_and_prediction.frontend.maps.county_map_with_wind import (
            population_map, save_map_with_wind
        )
        
        # Load county data (cached)
        gdf = load_county_data_cached()
        
        # Fixed filename - overwrites previous map
        map_filename = "fire_map.html"
        output_path = MAPS_DIR / map_filename
        
        print(f"🔥 Generating fire map: lat={request.latitude}, lon={request.longitude}, "
              f"radius={request.radius_km}km, wind={request.wind_speed_mph}mph @ {request.wind_direction_deg}°")
        
        # Generate the map
        total_pop, table, m, wind_data = population_map(
            gdf,
            request.latitude,
            request.longitude,
            request.radius_km,
            request.wind_speed_mph,
            request.wind_direction_deg
        )
        
        # Save map with wind and fire animations
        save_map_with_wind(m, wind_data, str(output_path))
        
        # Extract affected counties info
        affected_counties = []
        if not table.empty:
            for _, row in table.head(15).iterrows():  # Top 15 affected counties
                affected_counties.append(AffectedCounty(
                    county=str(row.get("COUNTY", "Unknown")),
                    state=str(row.get("STATE", "Unknown")),
                    population=int(row.get("population", 0)),
                    affected_share=round(float(row.get("fraction", 0)) * 100, 1),
                    contributing_pop=int(row.get("population_contrib", 0))
                ))
        
        print(f"✅ Map generated: {map_filename}, affected population: {int(total_pop):,}")
        
        # Cache-busting timestamp to force browser refresh
        cache_buster = int(time.time() * 1000)
        
        return FireMapResponse(
            map_url=f"/maps/{map_filename}?t={cache_buster}",
            total_population=int(total_pop),
            affected_counties=affected_counties,
            radius_km=request.radius_km,
            center_lat=request.latitude,
            center_lon=request.longitude
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Required data files not found: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Fire map generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fire map generation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
