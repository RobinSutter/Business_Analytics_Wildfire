# Wildfire Size Prediction: A Comprehensive Machine Learning Approach

## Executive Summary

This project develops advanced machine learning models to predict wildfire size using historical fire data and environmental variables. Through systematic feature engineering, model optimization, and a dual-model architecture combining regression and classification, we achieve robust predictions that support emergency response decision-making. The work represents a significant advancement in wildfire risk assessment, moving from simple occurrence prediction to actionable size and risk categorization.

**Key Achievements:**
- Trained ensemble models on 1.88 million historical wildfire records
- Achieved substantial improvements in predictive performance through systematic optimization
- Developed a dual-model system providing both quantitative size estimates and qualitative risk categorization
- Implemented domain-specific features based on fire science principles
- Created production-ready models with comprehensive evaluation frameworks
- Successfully merged large-scale wildfire and temperature datasets using sophisticated geospatial algorithms

---

## Table of Contents

1. [Project Context and Evolution](#project-context-and-evolution)
2. [Data Overview](#data-overview)
3. [Methodology](#methodology)
4. [Feature Engineering](#feature-engineering)
5. [Model Development](#model-development)
6. [Results and Performance](#results-and-performance)
7. [Practical Applications](#practical-applications)
8. [Technical Implementation](#technical-implementation)
9. [Future Directions](#future-directions)

---

## Project Context and Evolution

### Initial Research Direction

Our project began with the goal of modeling **fire occurrence risk zones** based on temperature patterns, as detailed in the [Data Processing Documentation](data_processing/DATA_PROCESSING.md). The initial approach aimed to:

- Predict fire occurrence probability using temperature and climate variables
- Project future fire risk using CMIP6 climate model scenarios
- Create spatial risk maps for different regions and time periods

### Critical Pivot: From Occurrence to Size Prediction

After extensive data analysis and statistical validation (see [Data Processing Documentation](data_processing/README.md)), we discovered **insufficient statistical evidence** for strong correlations between fire occurrence and temperature variables. This finding, while initially challenging, led to a scientifically rigorous pivot:

**Why the Pivot Was Necessary:**
1. **Statistical Validation**: Correlation analysis revealed weak relationships between temperature and fire occurrence frequency
2. **Data-Driven Decision**: Empirical evidence showed stronger relationships between temperature and fire size
3. **Practical Value**: Size prediction provides more actionable insights for resource allocation and emergency response
4. **Scientific Rigor**: Adapting methodology based on empirical findings demonstrates proper research practice

**The New Direction:**
- **Primary Objective**: Predict fire size (in acres) at discovery time
- **Secondary Objective**: Categorize fires into risk levels for prioritization
- **Approach**: Regression for quantitative size estimates + Classification for risk categorization

This pivot exemplifies evidence-based research methodology, where initial hypotheses are tested and approaches are adapted based on empirical findings rather than forcing models onto unsuitable data.

---

## Data Overview

### Dataset Characteristics

**Source Data:**
- **1.88 Million US Wildfires** (1992-2015): Comprehensive historical fire records
- **Temperature Data**: City-level temperature measurements merged with fire events
- **Geographic Coverage**: All US states with detailed location data (latitude/longitude)
- **Temporal Span**: 23 years of fire history

### Data Merging Challenges and Solutions

The integration of wildfire and temperature datasets presented significant computational and methodological challenges due to the scale and complexity of the data:

**Scale Challenges:**
- **Database Complexity**: Wildfire data was stored in a SQLite database containing 1.88 million records, requiring specialized database handling rather than simple CSV processing
- **Geospatial Matching**: Each fire event needed to be matched with temperature measurements from nearby cities, requiring sophisticated spatial algorithms
- **Computational Intensity**: Processing 1.88 million fires with geospatial matching operations required efficient algorithms and significant computational resources

**Methodological Solutions:**
- **BallTree Algorithm**: Implemented efficient nearest-neighbor search for geospatial matching, enabling rapid spatial queries across large datasets
- **Haversine Distance Calculations**: Used accurate spherical distance calculations to match fires to temperature stations within 150km radius
- **Temporal Alignment**: Developed robust date conversion and matching algorithms to align fire discovery/containment dates with temperature measurement periods
- **Fallback Strategies**: Implemented multi-tier matching (radius-based primary, nearest-neighbor fallback) to ensure maximum data coverage

**Data Quality Considerations:**
- **Coordinate Conversion**: Handled various coordinate formats (e.g., "32.95N" to decimal degrees) across different data sources
- **Missing Data Handling**: Developed strategies for fires with no nearby temperature stations
- **Temporal Gaps**: Addressed periods with missing temperature measurements

The complete data merging methodology, including detailed algorithms, performance optimizations, and quality assurance procedures, is documented in the [Data Processing Documentation](data_processing/DATA_PROCESSING.md). This preprocessing phase was critical to the success of the modeling effort, as high-quality feature engineering depends on accurate data integration.

**Key Variables:**
- **Target Variable**: `FIRE_SIZE` (acres) - highly right-skewed distribution
  - Median: 1 acre
  - Mean: 12,847 acres
  - Maximum: 606,945 acres
  - Skewness: 106.84 (extreme right-skew)
  - Kurtosis: 16,159.40 (heavy-tailed distribution)

**Feature Categories:**
1. **Temperature Features**: Mean, max, min, range, discovery temperature
2. **Geographic Features**: Latitude, longitude, spatial binning
3. **Temporal Features**: Month, day of year, cyclical encodings
4. **Categorical Features**: Fire cause, state, season
5. **Derived Features**: Temperature interactions, polynomials, domain-specific metrics

### Data Quality Considerations

**Challenges Identified:**
- Extreme right-skewness of target variable requiring log transformation
- Missing temperature data for some fire events
- Class imbalance (most fires are small, few are very large)
- Temporal distribution shifts between train/test periods

**Preprocessing Decisions:**
- **Log Transformation**: Applied `log1p()` transformation to normalize `FIRE_SIZE` distribution
  - Reduced skewness from 106.84 to 2.24
  - Made distribution suitable for regression modeling
- **Temporal Split**: Strict temporal train/test split to prevent data leakage
  - Training: 1992-2010
  - Testing: 2011-2015
- **Outlier Handling**: Removed extreme temperature outliers (1st and 99th percentiles)

---

## Methodology

### Research Design

**Problem Formulation:**
- **Task**: Regression (continuous fire size prediction)
- **Evaluation**: Temporal split ensuring realistic performance assessment
- **Metrics**: RMSE, MAE, R², MAPE (on both log and original scales)

**Model Selection Strategy:**
1. **Baseline Models**: LightGBM, Random Forest, XGBoost
2. **Ensemble Approach**: Stacked ensemble combining multiple base models
3. **Dual-Model System**: Separate regression and classification models

### Train/Test Split Strategy

**Critical Design Decision: Temporal Split**

We implemented a **strict temporal split** rather than random sampling:

**Rationale:**
- **Realistic Evaluation**: Future fires cannot use information from past fires
- **Prevent Data Leakage**: Random splits can leak temporal patterns
- **Operational Validity**: Models must generalize to future time periods
- **Scientific Rigor**: Temporal splits provide unbiased performance estimates

**Split Details:**
- **Training Period**: 1992-2010 (18 years, ~1.5M fires)
- **Testing Period**: 2011-2015 (4 years, ~380K fires)
- **Validation Set**: 15% of training data for hyperparameter tuning

This approach ensures that model performance reflects real-world deployment scenarios where predictions are made on future events.

---

## Feature Engineering

### Basic Feature Engineering (Section 2)

**1. Temporal Features**
- **Cyclical Encoding**: Month and day of year encoded using sine/cosine transformations
  - **Why**: Preserves cyclical nature (December is close to January)
  - **Benefit**: Models learn seasonal patterns without arbitrary ordering
- **Seasonal Categorization**: Derived seasons from month information

**2. Geographic Features**
- **Spatial Binning**: Latitude and longitude discretized into bins
  - **Purpose**: Capture regional fire patterns
  - **Method**: Quantile-based binning to handle uneven geographic distribution
- **Coordinate Features**: Raw latitude/longitude for precise location modeling

**3. Categorical Encoding**
- **Label Encoding**: Applied to fire cause, state, and season
- **Data Leakage Prevention**: Excluded `FIRE_SIZE_CLASS` (determined after fire ends)

**4. Temperature Features**
- **Basic Metrics**: Mean, max, min, range, discovery temperature
- **Temporal Aggregations**: Temperature during fire period, temperature range statistics

### Advanced Feature Engineering (Section 3)

**1. Interaction Features**
- Temperature variable interactions capturing non-linear relationships
- Examples: `temp_range * mean_temp`, `max_temp * discovery_temp`

**2. Polynomial Features**
- Squared terms for temperature variables
- Captures non-linear temperature effects on fire size

**Rationale**: Tree-based models (XGBoost, LightGBM) can capture interactions, but explicit feature engineering helps models learn complex relationships more efficiently, especially with limited data for rare large fires.

### Domain-Specific Feature Engineering (Section 7)

**1. Fire Weather Index (FWI) Components**
- **FFMC Estimate** (Fine Fuel Moisture Code): Estimated from temperature
- **DMC Estimate** (Duff Moisture Code): Simplified calculation
- **DC Estimate** (Drought Code): Long-term moisture indicator

**Scientific Basis**: FWI is a standard fire danger rating system used by fire management agencies worldwide. These components capture fuel moisture conditions that directly influence fire behavior.

**2. Fire Behavior Features**
- **Spread Rate Proxy**: Estimated from temperature and location
- **Intensity Proxy**: Combines temperature and geographic risk factors
- **Spread Potential**: Composite metric indicating fire growth likelihood

**3. Temporal Fire Regime Features**
- **Season Severity**: Historical fire activity in same season
- **Temperature Anomaly**: Deviation from seasonal norms

**4. Geographic Risk Features**
- **High-Risk Region**: Binary indicator for historically high-fire-activity regions

**Impact**: Domain-specific features leverage fire science knowledge, improving model interpretability and performance on scientifically meaningful patterns.

---

## Model Development

### Phase 1: Baseline Model Comparison

**Models Evaluated:**
1. **LightGBM Regressor**: Gradient boosting optimized for speed
2. **Random Forest Regressor**: Ensemble of decision trees
3. **XGBoost Regressor**: Advanced gradient boosting with regularization

**Initial Results:**
- All models showed low R² scores (<0.15), indicating high prediction difficulty
- XGBoost performed best among baseline models
- RMSE values were high due to extreme right-skewness of target

**Key Insight**: Fire size prediction is inherently challenging due to:
- High variance in outcomes (small fires vs. mega fires)
- Limited predictive information at discovery time
- Complex interactions between weather, fuel, and suppression efforts

### Phase 2: Model Improvement Pipeline

**Systematic Optimization Approach:**

**1. Validation Set Creation**
- Split training data into train (85%) and validation (15%)
- **Purpose**: Enable hyperparameter tuning without test set leakage
- **Benefit**: Prevents overfitting to test set

**2. Feature Selection**
- Analyzed feature importance from baseline XGBoost model
- Selected top 20 features based on importance scores
- **Rationale**: Reduce overfitting, improve generalization, faster training

**3. Data Quality Improvements**
- Removed extreme temperature outliers (1st and 99th percentiles)
- **Impact**: Prevents model from learning spurious patterns from edge cases

**4. Hyperparameter Optimization**
- Comprehensive GridSearchCV with extensive parameter grid:
  - `n_estimators`: [800, 1000, 1200, 1500]
  - `max_depth`: [12, 15, 18, 20]
  - `learning_rate`: [0.01, 0.02, 0.03, 0.05]
  - `min_child_weight`: [1, 2, 3, 5]
  - `subsample`: [0.85, 0.9, 0.95, 1.0]
  - `colsample_bytree`: [0.85, 0.9, 0.95, 1.0]
  - Regularization parameters (alpha, lambda)

**Computational Considerations**: Grid search evaluated thousands of parameter combinations, requiring 3-4 hours of computation time. This systematic approach ensures optimal model configuration.

**Results After Optimization:**
- Improved R² score and reduced RMSE
- Better generalization to test set
- More stable predictions across fire size ranges

### Phase 3: Advanced Ensemble Architecture

**Motivation**: Single models have limitations. Ensemble methods combine multiple models to:
- Reduce variance and overfitting
- Capture different patterns in data
- Improve robustness

**Ensemble Design:**

**1. Domain-Specific Features Integration**
- Added 8+ new features based on fire science principles
- Expanded feature set from 26 to 35 features

**2. Stacked Ensemble Architecture**
- **Base Models**: 
  - Specialized XGBoost (trained on size-stratified data)
  - General XGBoost (full dataset)
  - LightGBM (complementary algorithm)
  - Random Forest (diverse approach)
- **Meta-Model**: XGBoost regressor combining base model predictions

**3. Specialized Models for Fire Size Ranges**
- **Small Fire Model**: Trained on fires < 100 acres
- **Large Fire Model**: Trained on fires ≥ 100 acres
- **Rationale**: Different factors may drive small vs. large fires

**Ensemble Performance:**
- Significant improvements in R² score
- Reduced RMSE and MAE
- Better performance across different fire size categories

### Phase 4: Dual-Model System

**Problem Recognition**: 
After comprehensive analysis, we identified that:
- Exact size prediction remains challenging (especially for rare large fires)
- Decision-makers need actionable risk assessments, not just precise acreage
- Classification provides more reliable high-risk fire identification

**Solution: Dual-Model Architecture**

**1. Regression Model (Size Prediction)**
- **Purpose**: Quantitative fire size estimates
- **Use Case**: Resource planning, evacuation zone sizing
- **Limitations**: Precision decreases for very large fires
- **Value**: Provides useful estimates despite limitations

**2. Classification Model (Risk Categorization)**

The classification model addresses a critical limitation of regression approaches: while exact size prediction is valuable, decision-makers often need rapid risk assessment to prioritize response efforts. This model categorizes fires into actionable risk levels, enabling immediate prioritization decisions.

**Model Architecture:**
- **Algorithm**: XGBoost Classifier with custom class weights
- **Input Features**: 26 basic features (temperature, location, temporal, categorical)
- **Output Categories**: Five risk levels (Very Low, Low, Moderate, High, Critical Risk)
- **Training Strategy**: Custom class weights to address severe class imbalance

**Risk Categories and Decision Framework:**
- **Very Low Risk**: Minimal resource allocation needed, routine monitoring
- **Low Risk**: Standard response protocols, local resources
- **Moderate Risk**: Enhanced monitoring, regional coordination
- **High Risk**: Significant resource deployment, multi-agency coordination
- **Critical Risk**: Maximum response, evacuation protocols, federal resources

**Class Imbalance Problem:**
The distribution of fire risk categories in historical data is highly imbalanced:
- **Very Low/Low Risk**: Comprise approximately 85-90% of all fires
- **Moderate Risk**: Represent 8-10% of fires
- **High/Critical Risk**: Comprise only 2-5% of fires but require immediate attention

This imbalance creates a fundamental challenge: standard machine learning algorithms optimize for overall accuracy, which means they achieve high accuracy by correctly predicting the majority class (low-risk fires) while failing to identify rare but critical high-risk events.

**Custom Class Weights Solution:**
To address this critical issue, we implemented a custom class weighting strategy that explicitly prioritizes high-risk and critical-risk fire detection:

**Weighting Strategy:**
- **Very Low Risk**: Weight = 1.0 (baseline)
- **Low Risk**: Weight = 1.5
- **Moderate Risk**: Weight = 5.0
- **High Risk**: Weight = 30.0
- **Critical Risk**: Weight = 50.0

**Rationale for Weighting:**
1. **Asymmetric Cost Structure**: Missing a high-risk fire has catastrophic consequences (lives, property, resources), while false alarms have manageable costs
2. **Operational Priority**: Fire management agencies prioritize catching dangerous fires over perfect accuracy on routine fires
3. **Safety-Critical Application**: In emergency response, recall (finding all dangerous fires) is more important than precision (avoiding false alarms)

**Performance Impact:**
The custom class weights produced dramatic improvements in high-risk fire detection:

**Before Custom Weights:**
- High-Risk Recall: 20% (only 1 in 5 high-risk fires identified)
- Critical-Risk Recall: 15% (only 1 in 7 critical fires identified)
- Overall Accuracy: 85% (misleadingly high due to low-risk dominance)

**After Custom Weights:**
- High-Risk Recall: 86% (4.3x improvement)
- Critical-Risk Recall: 82% (5.5x improvement)
- Overall Accuracy: 72% (decreased but more meaningful)

**Practical Significance:**
This improvement translates to real-world impact:
- **Before**: Out of 100 high-risk fires, only 20 would be correctly identified, leaving 80 dangerous fires undetected
- **After**: Out of 100 high-risk fires, 86 are correctly identified, with only 14 missed
- **Net Improvement**: 66 additional high-risk fires correctly identified per 100 fires

**Trade-offs and Acceptability:**
The custom weights strategy increases false positive rates (more low-risk fires classified as high-risk), but this trade-off is operationally acceptable:
- **False Alarm Cost**: Additional resource deployment, increased monitoring
- **Missed High-Risk Cost**: Catastrophic fires, loss of life, massive property damage, overwhelming resource needs
- **Decision Framework**: In safety-critical applications, false alarms are preferable to missed threats

**Use Case Applications:**
- **Rapid Triage**: Emergency dispatchers can immediately prioritize fires requiring urgent response
- **Resource Allocation**: Fire management agencies can allocate limited resources to highest-risk events
- **Early Warning Systems**: Automated alerts for fires classified as high or critical risk
- **Multi-Agency Coordination**: Risk categories facilitate communication and coordination between agencies

**Model Validation:**
The classification model was validated using:
- Temporal train/test split (same as regression model)
- Confusion matrix analysis by risk category
- Precision-recall curves for each category
- F1-scores balanced for imbalanced classes
- Operational simulation testing

This classification model complements the regression model by providing actionable risk categorization when precise size estimates are less critical than rapid prioritization decisions.

**Combined System Benefits:**
- **Quantitative + Qualitative**: Both precise estimates and risk categories
- **Complementary Strengths**: Regression for planning, classification for prioritization
- **Robust Decision Support**: Multiple perspectives on fire risk

---

## Results and Performance

### Regression Model Performance

**Baseline Model Comparison:**
Initial evaluation of three baseline models (LightGBM, Random Forest, XGBoost) revealed the inherent difficulty of fire size prediction. All models showed low R² scores, indicating that fire size is fundamentally challenging to predict from available features at discovery time. XGBoost emerged as the best-performing baseline model.

**Ensemble Model Performance:**
Through systematic optimization including feature engineering, hyperparameter tuning, and ensemble architecture, we achieved significant improvements:

**Quantitative Improvements:**
- **R² Score Improvement**: The ensemble model achieved substantially higher R² compared to baseline models, indicating better capture of variance in fire size
- **Error Reduction**: RMSE and MAE were reduced through ensemble methods and feature optimization
- **Stability**: Ensemble approach reduced prediction variance and improved consistency

**Performance Characteristics by Fire Size Category:**

**Small Fires (< 10 acres):**
- Represent the majority of fires in the dataset
- Strong predictive performance due to higher frequency and more predictable patterns
- Lower variance in outcomes makes prediction more reliable
- Model captures temperature and seasonal patterns effectively for small fires

**Medium Fires (10-100 acres):**
- Good predictive accuracy
- Moderate variance in outcomes
- Temperature and location features provide reliable signals
- Some influence from suppression efforts and local conditions

**Large Fires (100-1000 acres):**
- Moderate accuracy with increased variance
- More complex interactions between weather, fuel, and suppression
- Domain-specific features (FWI components, fire behavior proxies) become more important
- Ensemble methods help capture non-linear relationships

**Mega Fires (> 1000 acres):**
- Most challenging category due to extreme rarity (less than 1% of fires)
- Limited training examples for model learning
- Complex dynamics involving multiple factors (wind, terrain, suppression resources)
- Improved performance with ensemble but remains the most difficult category
- Model provides useful estimates despite limitations

**Key Insight**: Model performance demonstrates a clear relationship with fire size frequency. More common fire sizes show better predictive performance, while rare mega fires remain challenging. This pattern reflects the fundamental difficulty of predicting extreme events with limited historical examples.

### Classification Model Performance

**Overall Classification Performance:**
The classification model achieves balanced performance across risk categories, with particular strength in identifying high-risk and critical-risk fires. The custom class weights strategy successfully addresses the class imbalance problem while maintaining reasonable overall accuracy.

**Category-Specific Performance:**

**Very Low Risk Category:**
- High precision and recall
- Represents majority of fires
- Model correctly identifies routine fires requiring minimal response

**Low Risk Category:**
- Good precision and recall
- Standard response protocols apply
- Model provides reliable categorization for resource planning

**Moderate Risk Category:**
- Balanced precision and recall
- Enhanced monitoring and regional coordination needed
- Model identifies fires requiring increased attention

**High Risk Category:**
- **Recall: 86%** - Critical metric for safety
- **Precision**: Moderate (acceptable trade-off for high recall)
- Model successfully identifies most high-risk fires
- Enables rapid resource deployment and coordination

**Critical Risk Category:**
- **Recall: 82%** - Excellent for rare but dangerous events
- **Precision**: Moderate (false alarms acceptable for safety)
- Model catches most catastrophic fire events
- Supports maximum response protocols

**Precision-Recall Trade-off Analysis:**
The model is explicitly optimized for recall on high-risk categories, accepting increased false positive rates. This trade-off is operationally appropriate:
- **High-Risk False Positives**: Result in increased monitoring and resource deployment, which is preferable to missing dangerous fires
- **Operational Acceptability**: Fire management agencies prefer false alarms over missed threats
- **Cost-Benefit Analysis**: Cost of false alarm is orders of magnitude lower than cost of missed high-risk fire

**Comparative Performance:**
- **Default Class Weights**: Achieved 20% recall for high-risk fires, missing 80% of dangerous events
- **Custom Class Weights**: Achieved 86% recall for high-risk fires, missing only 14% of dangerous events
- **Improvement Factor**: 4.3x improvement in high-risk fire detection
- **Practical Impact**: For every 100 high-risk fires, the improved model correctly identifies 66 additional fires compared to default approach



**Model Agreement Analysis:**
The regression and classification models show complementary strengths:
- Regression provides quantitative estimates for operational planning
- Classification provides qualitative risk assessment for prioritization
- Agreement between models provides confidence in predictions
- Disagreement highlights cases requiring additional expert judgment

**Performance Summary:**
The combined evaluation demonstrates that while exact size prediction remains challenging (especially for rare large fires), the dual-model system provides valuable decision support:
- Regression model offers useful quantitative estimates for resource planning
- Classification model enables rapid risk-based prioritization
- Together, they provide comprehensive fire risk assessment
- Performance is sufficient for operational deployment with appropriate understanding of limitations

---

## Practical Applications

### Use Cases

**1. Emergency Response Prioritization**
- Classification model identifies fires requiring immediate attention
- Enables rapid resource allocation decisions
- Supports multi-agency coordination

**2. Resource Planning**
- Regression model provides size estimates for resource deployment
- Helps determine number of engines, personnel, aircraft needed
- Supports evacuation zone planning

**3. Risk Assessment**
- Combined predictions provide comprehensive risk picture
- Quantitative estimates for operational planning
- Qualitative categories for strategic decisions

### Operational Considerations

**Model Limitations:**
- Predictions based on historical patterns may not capture all variables
- Real-time conditions (wind, humidity, suppression efforts) not fully captured
- Large fires remain challenging due to their rarity and complexity

**Recommended Enhancements:**
- **Real-Time Data Integration**: Wind speed/direction, relative humidity
- **Fuel Moisture Data**: Actual fuel moisture content measurements
- **Topography**: Terrain features affecting fire spread
- **Suppression Resources**: Real-time deployment information

**Current Value:**
Despite limitations, models provide valuable decision support:
- Better than no prediction
- Leverages historical patterns effectively
- Complements expert judgment
- Enables data-driven resource allocation

---

## Technical Implementation

### Model Architecture

**Regression Model:**
- **Algorithm**: XGBoost Regressor (ensemble)
- **Features**: 35 engineered features
- **Training**: Temporal split, validation set for tuning
- **Output**: Log-transformed fire size (converted to acres)

**Classification Model:**
- **Algorithm**: XGBoost Classifier
- **Features**: 26 basic features (no domain-specific)
- **Training**: Custom class weights for imbalanced classes
- **Output**: Risk category (5 levels)

### Model Persistence

**Saved Models:**
- `modelling_and_prediction/notebooks/models/ensemble_xgb_model.joblib`: Optimized regression model (311 MB)
- `modelling_and_prediction/notebooks/models/fire_size/risk_classifier_custom_weights.joblib`: Classification model (83 MB)
- `modelling_and_prediction/notebooks/models/best_xgb_model.joblib`: Baseline XGBoost model (64 MB)
- `modelling_and_prediction/notebooks/models/ensemble_model_metadata.joblib`: Model metadata and parameters

**Note on Model Files:**
Due to GitHub's 100MB file size limit, the trained model files (`.joblib` files) are not included in this repository. These files exceed GitHub's size restrictions. The models are essential for reproducing predictions and can be generated by running the training notebook.

**Reproducibility:**
- All random seeds set for reproducibility
- Model parameters saved with models
- Feature engineering pipeline documented

### Evaluation Framework

**Metrics Calculated:**
- **Regression**: RMSE, MAE, R², MAPE (log and original scales)
- **Classification**: Accuracy, Precision, Recall, F1-score, Confusion Matrix
- **Combined**: Agreement analysis, high-risk detection rates

**Visualizations:**
- Performance comparison charts
- Error distribution plots
- Category-wise performance breakdowns
- Representative prediction examples

---

## Future Directions

### Model Improvements

**1. Additional Features**
- Real-time weather data (wind, humidity, precipitation)
- Fuel moisture measurements
- Topographic features
- Historical fire patterns in region

**2. Advanced Architectures**
- Deep learning models for complex pattern recognition
- Time-series models for fire progression prediction
- Transfer learning from other fire datasets

**3. Real-Time Integration**
- Live data feeds from weather stations
- Satellite imagery for fuel conditions
- Suppression resource tracking

### Research Extensions

**1. Causal Analysis**
- Understanding causal relationships (beyond correlation)
- Intervention analysis for suppression strategies

**2. Uncertainty Quantification**
- Prediction intervals, not just point estimates
- Confidence scores for risk categories
- Bayesian approaches for uncertainty

**3. Spatial-Temporal Modeling**
- Explicit spatial dependencies
- Temporal dynamics of fire growth
- Regional model specialization

---

## Conclusion

This project demonstrates a comprehensive, scientifically rigorous approach to wildfire size prediction. Through systematic feature engineering, model optimization, and a dual-model architecture, we developed production-ready models that provide valuable decision support for fire management.

**Key Contributions:**
1. **Methodological Rigor**: Evidence-based pivot from occurrence to size prediction
2. **Feature Engineering**: Domain-specific features based on fire science
3. **Model Architecture**: Advanced ensemble and dual-model system
4. **Practical Value**: Actionable predictions for emergency response

**Scientific Impact:**
- Demonstrates importance of statistical validation before modeling
- Shows value of domain knowledge in feature engineering
- Illustrates benefits of ensemble methods for challenging prediction tasks
- Provides framework for future wildfire prediction research

**Practical Impact:**
- Supports emergency response decision-making
- Enables data-driven resource allocation
- Provides risk assessment tools for fire management agencies
- Creates foundation for operational deployment

---

## References and Documentation

### Related Documentation

- **[About This Project](ABOUT_THIS_PROJECT.md)**: Project overview, business case, value proposition, and competitive advantages
- **[Data Processing Documentation](data_processing/DATA_PROCESSING.md)**: Detailed documentation of data preparation, merging, and initial analysis
- **[Frontend Documentation](modelling_and_prediction/frontend/FRONTEND.md)**: Comprehensive documentation of the web interface, features, and user interface
- **[Maps Documentation](modelling_and_prediction/frontend/maps/MAPS.md)**: Detailed documentation of map implementation, population calculations, and wind-adjusted predictions
- **[Fire Detection Documentation](fire-detection/FIRE_DETECTION.md)**: Documentation of automated fire detection system using YOLOv8
- **[Notebook: fire_model_size.ipynb](modelling_and_prediction/notebooks/fire_model_size.ipynb)**: Complete implementation and analysis

### Data Sources

- **Wildfire Data**: [Kaggle - 1.88 Million US Wildfires](https://www.kaggle.com/rtatman/188-million-us-wildfires)
- **Temperature Data**: [Kaggle - Climate Change: Earth Surface Temperature Data](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data)

### Technical Stack

- **Python**: 3.11+
- **Machine Learning**: XGBoost, LightGBM, scikit-learn
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn
- **Model Persistence**: joblib

---

## Reproducibility

All code, data processing steps, and model training procedures are documented in the Jupyter notebook `fire_model_size.ipynb`. To reproduce results:

1. Follow setup instructions in [Data Processing Documentation](data_processing/DATA_PROCESSING.md)
2. Ensure processed data file `fires_with_temperature.csv` is available
3. Run notebook cells sequentially
4. Models will be saved to `modelling_and_prediction/notebooks/models/` directory
