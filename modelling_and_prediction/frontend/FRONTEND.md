# Frontend Application: Wildfire Risk Prediction Interface

## Overview

The frontend application provides an interactive web interface for wildfire risk prediction and monitoring. Built with React, TypeScript, and modern UI libraries, it offers fire management professionals a comprehensive dashboard for fire assessment, visualization, and decision support. The application integrates with machine learning models through a FastAPI backend to deliver real-time predictions, risk assessments, and visual analytics.

**Key Capabilities:**
- Real-time fire size and risk predictions
- Interactive geographic visualization with wind-adjusted spread modeling
- Population impact analysis and mapping
- Automated fire detection via webcam monitoring
- Historical prediction tracking
- Comprehensive risk assessment dashboard

## Features

### 1. Fire Prediction Interface

**Prediction Form (`PredictionForm.tsx`)**
- **Input Fields**: Comprehensive form for fire condition data entry
  - **Temperature Data**: Mean, max, min, discovery temperature with intuitive sliders
  - **Location**: State selection, latitude/longitude coordinates with "Use Current Location" feature
  - **Temporal Data**: Date picker with automatic season and day-of-year calculation
  - **Fire Cause**: Dropdown selection of common fire causes (Lightning, Equipment, Arson, etc.)
  - **Wind Conditions**: Optional wind speed and direction inputs for enhanced predictions
  - **Proximity Data**: Number of nearby cities for geographic context
- **Form Validation**: Real-time validation with helpful error messages
- **Auto-population**: Automatic coordinate population based on state selection
- **User Experience**: Modern glass-morphism design with intuitive controls

**Prediction Results (`PredictionResults.tsx`)**
- **Risk Score Display**: Visual risk gauge showing 0-100 risk score with color coding
- **Fire Size Prediction**: Predicted acreage and hectares with confidence indicators
- **Risk Category**: Five-level categorization (Very Low, Low, Moderate, High, Critical)
- **Response Recommendations**: 
  - Response level classification
  - Resource requirements (engines, personnel, aircraft)
  - Action items for fire management
  - Estimated duration
- **Fire Size Class**: Standard fire classification (A through G)
- **Visual Indicators**: Color-coded risk categories for rapid assessment

### 2. Interactive Map Visualization

**Fire Map Viewer (`FireMapViewer.tsx`, `RealFireMap.tsx`, `PopulationFireMap.tsx`)**
- **Geographic Display**: Interactive maps showing fire location and predicted spread
- **Wind-Adjusted Visualization**: Dynamic fire spread modeling based on wind direction and speed
- **Population Overlay**: Integration with population data showing affected communities
- **Multiple Map Views**: 
  - Standard fire location map
  - Population impact heatmap
  - Wind-adjusted spread scenarios
- **Interactive Controls**: Zoom, pan, and layer toggling
- **Real-Time Updates**: Maps update dynamically with prediction changes

**Map Generation**
- **Backend Integration**: Calls Python-based map generation service
- **Folium Maps**: Server-side generation of interactive HTML maps
- **County-Level Analysis**: Population impact calculated at county level
- **Wind Modeling**: Directional spread visualization based on wind conditions

For detailed information about map implementation, population calculations, and wind-adjusted predictions, see the [Maps Documentation](maps/MAPS.md).

### 3. Population Impact Analysis

**Population Fire Map (`PopulationFireMap.tsx`)**
- **Affected Population Calculation**: Estimates how many people may be impacted
- **County-Level Breakdown**: Detailed analysis by affected counties
- **Population Density Visualization**: Heatmap overlay showing population density
- **Community Identification**: Highlights specific communities and neighborhoods at risk
- **Evacuation Planning Support**: Helps identify areas requiring evacuation

The population impact calculation integrates census data with fire spread predictions to provide actionable insights for emergency planning. See [Maps Documentation](maps/MAPS.md) for technical implementation details.

### 4. Automated Fire Detection

**Webcam Monitoring (`Webcam.tsx`)**
- **Real-Time Video Analysis**: Connects to webcams and security cameras
- **AI-Powered Detection**: Automatic identification of smoke and fire in video feeds
- **Automatic Alerts**: Immediate notifications when fire or smoke is detected
- **Multi-Camera Support**: Simultaneous monitoring of multiple camera feeds
- **Detection Statistics**: Real-time display of detection status and timestamps
- **Historical Tracking**: Review of past detections and alerts

**Alert System:**
- **Fire Detection**: Critical alerts for confirmed fire detection
- **Smoke Detection**: Warning alerts for smoke detection
- **Status Monitoring**: Continuous monitoring with 1-second refresh rate
- **Error Handling**: Graceful handling of connection issues

### 5. Historical Prediction Tracking

**History Panel (`HistoryPanel.tsx`)**
- **Prediction Storage**: Local storage of all predictions for review
- **Quick Access**: Easy retrieval of past predictions
- **Comparison Tools**: Compare current predictions with historical data
- **Export Capabilities**: Save prediction history for reporting
- **Search and Filter**: Find specific predictions by date, location, or risk category

### 6. Risk Assessment Dashboard

**Comprehensive Display:**
- **Risk Gauge (`RiskGauge.tsx`)**: Visual circular gauge showing risk score with color coding
- **Metric Cards (`MetricCard.tsx`)**: Key metrics displayed in card format
- **Recommendations Panel (`RecommendationsPanel.tsx`)**: Actionable recommendations based on risk level
- **Response Level Indicators**: Clear classification of required response intensity

## Risk Scoring and Classification Methodology

### Fire Size Classification (NWCG Standard)

The application uses the **National Wildfire Coordinating Group (NWCG)** standard fire size classification system, which is the industry standard for wildfire management in the United States. This classification system is hardcoded in the backend and provides consistent categorization across all fire management agencies.

**NWCG Fire Size Classes:**

| Class | Acreage Range | Description |
|-------|---------------|-------------|
| **A** | 0 - 0.25 acres | Spot fires, easily contained |
| **B** | 0.25 - 10 acres | Small fires, initial attack |
| **C** | 10 - 100 acres | Extended attack fires |
| **D** | 100 - 300 acres | Large fires requiring additional resources |
| **E** | 300 - 1,000 acres | Very large fires, multi-day operations |
| **F** | 1,000 - 5,000 acres | Major fires requiring coordination |
| **G** | 5,000+ acres | Catastrophic fires, maximum mobilization |

**Source:** National Wildfire Coordinating Group (NWCG) standards, as documented in the [1.88 Million US Wildfires dataset](https://www.kaggle.com/rtatman/188-million-us-wildfires) metadata and USDA Forest Service fire reporting guidelines.

### Composite Risk Score Calculation

The risk score (0-100) is calculated using a composite methodology that combines predicted fire size with environmental risk factors:

**1. Size-Based Risk Component (5-85 points):**
- Based on NWCG fire class of predicted size
- Larger fires inherently pose greater risk
- Mapping:
  - Class A: 5 points (minimal risk)
  - Class B: 15 points (low risk)
  - Class C: 30 points (moderate risk)
  - Class D: 45 points (elevated risk)
  - Class E: 60 points (high risk)
  - Class F: 75 points (very high risk)
  - Class G: 85 points (critical base risk)

**2. Environmental Risk Factors (0-30 points):**
- **Temperature Factor (0-10 points)**: Higher temperatures increase fire behavior intensity
- **Wind Factor (0-10 points)**: Higher wind speeds accelerate spread and ember spotting
- **Geographic Location (0-5 points)**: High-risk states (CA, NV, AZ, etc.) receive additional points
- **Seasonal Factor (0-5 points)**: Summer season increases risk due to fuel dryness
- **Human Causation (0-3 points)**: Human-caused fires often occur near populated areas

**Risk Categories:**
- **0-20**: Very Low Risk
- **20-40**: Low Risk
- **40-60**: Moderate Risk
- **60-80**: High Risk
- **80-100**: Critical Risk

This composite approach ensures that small fires in extreme conditions (e.g., 20 acres during 100°F Santa Ana winds in California) are appropriately classified as high-risk, while large fires in favorable conditions receive proportional risk scores.

### Response Time Estimates

The estimated response durations are based on **industry-standard incident management timelines** derived from NWCG Incident Response Pocket Guide (IRPG) and National Incident Management System (NIMS) protocols. These estimates reflect typical containment timelines for different risk levels with appropriate resource deployment.

**Response Duration by Risk Category:**

| Risk Level | Duration | Basis |
|------------|----------|-------|
| **Very Low Risk** | 2-6 hours | Initial attack timeframe for small, accessible fires with favorable conditions |
| **Low Risk** | 6-24 hours | Extended initial attack, typically contained within one operational period |
| **Moderate Risk** | 1-3 days | Extended attack requiring multiple operational periods and resource rotation |
| **High Risk** | 3-7 days | Major incident requiring Incident Management Team (IMT) Type 2 or 3 |
| **Critical Risk** | 1-2 weeks+ | Complex incident requiring IMT Type 1, multi-agency coordination |

**Methodology Justification:**

These duration estimates are **hardcoded based on established fire management protocols** rather than predicted by machine learning models. The rationale for this approach:

1. **Standardization**: Response timelines follow NWCG and NIMS standards used by all federal, state, and local fire agencies
2. **Resource Planning**: Duration estimates reflect realistic timelines when appropriate resources (as specified in recommendations) are deployed
3. **Operational Constraints**: Containment depends on factors beyond prediction scope (terrain, suppression tactics, resource availability)
4. **Historical Validation**: Duration ranges reflect typical containment times from historical fire data analysis (see [Main README](../../README.md) for dataset details)

**Sources:**
- NWCG Incident Response Pocket Guide (IRPG)
- National Incident Management System (NIMS) protocols
- Historical fire data from 1.88 million US wildfires (1992-2015)
- USDA Forest Service incident management guidelines

**Note:** Actual containment times vary significantly based on suppression resources, weather changes, terrain complexity, and fire behavior. These estimates assume standard resource deployment as specified in the response recommendations.

## Architecture

### Technology Stack

**Core Framework:**
- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type-safe development with comprehensive type definitions
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing for multi-page application

**UI Components:**
- **shadcn/ui**: High-quality, accessible component library built on Radix UI
- **Tailwind CSS**: Utility-first CSS framework for rapid styling
- **Radix UI**: Unstyled, accessible component primitives
- **Lucide React**: Modern icon library

**Data Visualization:**
- **Mapbox GL**: High-performance mapping library for interactive maps
- **Leaflet**: Alternative mapping library for geographic visualization
- **Recharts**: React charting library for data visualization

**State Management:**
- **React Query (TanStack Query)**: Server state management and caching
- **Local Storage**: Client-side persistence for prediction history
- **React Hooks**: Component-level state management

**Form Handling:**
- **React Hook Form**: Performant form library with validation
- **Zod**: Schema validation for form inputs

**Development Tools:**
- **ESLint**: Code linting and quality assurance
- **TypeScript**: Static type checking
- **PostCSS**: CSS processing with Tailwind

### Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/              # shadcn/ui base components
│   │   ├── PredictionForm.tsx
│   │   ├── PredictionResults.tsx
│   │   ├── FireMapViewer.tsx
│   │   ├── RealFireMap.tsx
│   │   ├── PopulationFireMap.tsx
│   │   ├── RiskGauge.tsx
│   │   ├── RecommendationsPanel.tsx
│   │   ├── HistoryPanel.tsx
│   │   └── Header.tsx
│   ├── pages/               # Page components
│   │   ├── Index.tsx        # Main prediction interface
│   │   ├── Webcam.tsx       # Webcam monitoring page
│   │   └── NotFound.tsx     # 404 page
│   ├── lib/                 # Utility libraries
│   │   ├── api.ts           # API client and backend integration
│   │   ├── storage.ts       # Local storage utilities
│   │   └── utils.ts         # General utilities
│   ├── hooks/               # Custom React hooks
│   │   ├── use-mobile.tsx
│   │   ├── use-toast.ts
│   │   └── useTheme.ts
│   ├── types/               # TypeScript type definitions
│   │   └── prediction.ts    # Prediction-related types
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── maps/                     # Map generation scripts
│   ├── county_map_with_wind.py
│   ├── map_pop.html
│   └── README.md            # Maps documentation
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
└── vite.config.ts          # Vite configuration
```

## Component Details

### Core Components

**PredictionForm**
- **Purpose**: Input interface for fire condition data
- **Features**: 
  - Temperature input with sliders
  - Location selection with geolocation API
  - Date picker with automatic season calculation
  - Fire cause selection
  - Wind condition inputs
- **Validation**: Real-time form validation with Zod schemas
- **User Experience**: Auto-population, smart defaults, helpful tooltips

**PredictionResults**
- **Purpose**: Display prediction results and recommendations
- **Features**:
  - Risk score visualization
  - Fire size display (acres and hectares)
  - Risk category with color coding
  - Response recommendations
  - Resource requirements
  - Action items list
- **Visualization**: Risk gauge, metric cards, color-coded categories

**FireMapViewer / RealFireMap / PopulationFireMap**
- **Purpose**: Geographic visualization of fire predictions
- **Features**:
  - Interactive map display
  - Fire location marking
  - Spread radius visualization
  - Wind-adjusted spread modeling
  - Population overlay
  - County-level analysis
- **Integration**: Calls backend map generation service
- **Libraries**: Mapbox GL and Leaflet for mapping

**Webcam**
- **Purpose**: Real-time fire detection via webcam monitoring
- **Features**:
  - Video stream display
  - AI-powered fire/smoke detection
  - Automatic alert system
  - Detection statistics
  - Historical detection log

**HistoryPanel**
- **Purpose**: Track and review past predictions
- **Features**:
  - Local storage persistence
  - Prediction history display
  - Quick access to past predictions
  - Comparison tools

### UI Component Library

The application uses **shadcn/ui**, a collection of reusable components built on Radix UI primitives. This provides:
- **Accessibility**: WCAG-compliant components
- **Customization**: Fully customizable with Tailwind CSS
- **Consistency**: Unified design system across the application
- **Components**: Buttons, forms, dialogs, cards, charts, and more

## Backend Integration

### API Client (`lib/api.ts`)

**Endpoints:**
- **`POST /predict`**: Fire size and risk prediction
  - Input: `PredictionRequest` (temperature, location, temporal, cause data)
  - Output: `PredictionResponse` (predicted size, risk score, category, recommendations)
- **`GET /health`**: Backend health check
- **`POST /api/generate-fire-map`**: Map generation with population analysis
  - Input: `FireMapRequest` (location, radius, wind conditions)
  - Output: `FireMapResponse` (map URL, population data, affected counties)

**Error Handling:**
- Graceful degradation when backend is unavailable
- Mock prediction generation for demo purposes
- User-friendly error messages
- Automatic retry logic

**Configuration:**
- API base URL configurable via environment variable (`VITE_API_URL`)
- Default: `http://localhost:8000`
- CORS handling for cross-origin requests

### Data Flow

1. **User Input**: User fills out prediction form with fire conditions
2. **Form Validation**: Client-side validation using Zod schemas
3. **API Request**: Form data sent to FastAPI backend
4. **Model Prediction**: Backend uses machine learning models (see [Main README](../../README.md))
5. **Response Processing**: Frontend receives prediction results
6. **Visualization**: Results displayed with maps, charts, and recommendations
7. **Storage**: Prediction saved to local storage for history

## Map Features and Population Analysis

The frontend integrates sophisticated mapping capabilities for visualizing fire predictions and population impact. Key features include:

### Wind-Adjusted Fire Spread
- **Dynamic Modeling**: Fire spread predictions adjust based on wind direction and speed
- **Directional Visualization**: Maps show how fire spread changes with different wind conditions
- **Multiple Scenarios**: Visualization of different wind scenarios for contingency planning
- **Real-Time Updates**: Maps update when wind conditions change

### Population Impact Mapping
- **Affected Population Calculation**: Estimates how many people may be impacted by fire
- **County-Level Analysis**: Detailed breakdown by affected counties
- **Population Density Overlay**: Visual representation of population density
- **Community Identification**: Highlights specific communities at risk

### Map Generation
- **Server-Side Generation**: Python scripts generate interactive Folium maps
- **HTML Export**: Maps exported as standalone HTML files
- **Integration**: Frontend displays generated maps in iframes or embedded views

For comprehensive documentation on map implementation, population calculation algorithms, and wind-adjusted spread modeling, see the [Maps Documentation](maps/MAPS.md).

### Development Workflow

1. **Start Backend**: Ensure FastAPI backend is running (see backend documentation)
2. **Start Frontend**: Run `npm run dev` in frontend directory
3. **Make Changes**: Edit files in `src/` directory
4. **Hot Reload**: Changes automatically reflected in browser
5. **Test**: Use browser developer tools for debugging

### Code Organization

- **Components**: Reusable UI components in `src/components/`
- **Pages**: Route-level components in `src/pages/`
- **Utilities**: Helper functions in `src/lib/`
- **Types**: TypeScript definitions in `src/types/`
- **Hooks**: Custom React hooks in `src/hooks/`

### Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Custom Classes**: Additional styles in `src/index.css`
- **Component Styles**: Scoped styles using Tailwind utilities
- **Theme Support**: Dark/light mode support via `next-themes`

## User Interface Features

### Responsive Design
- **Mobile-First**: Optimized for mobile devices
- **Tablet Support**: Responsive layouts for tablet screens
- **Desktop**: Full-featured desktop interface
- **Breakpoints**: Tailwind responsive breakpoints

### Accessibility
- **WCAG Compliance**: Components built on accessible Radix UI primitives
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: ARIA labels and semantic HTML
- **Color Contrast**: High contrast for readability

### User Experience
- **Loading States**: Visual feedback during API calls
- **Error Handling**: User-friendly error messages
- **Toast Notifications**: Non-intrusive notifications
- **Form Validation**: Real-time validation with helpful messages
- **Auto-save**: Prediction history automatically saved

## Integration with Backend

The frontend communicates with the FastAPI backend (see `modelling_and_prediction/backend/`) which provides:

- **Prediction API**: Machine learning model predictions
- **Map Generation**: Server-side map creation with population analysis
- **Health Checks**: Backend status monitoring

The backend uses machine learning models trained on 1.88 million historical fire records. For details on model training, feature engineering, and performance, see the [Main Project README](../../README.md).

## Data Processing Integration

The frontend relies on processed data from the data processing pipeline. The prediction models use features derived from:

- **Temperature Data**: Merged with fire records (see [Data Processing Documentation](../../../data_processing/DATA_PROCESSING.md))
- **Geographic Data**: Location features and spatial binning
- **Temporal Features**: Date, season, cyclical encodings
- **Categorical Data**: Fire cause, state, season encodings

For information about data preparation, merging, and preprocessing, see the [Data Processing Documentation](../../../data_processing/DATA_PROCESSING.md).

## Map Implementation Details

The mapping features integrate multiple technologies:

- **Frontend Visualization**: React components using Mapbox GL and Leaflet
- **Backend Generation**: Python scripts using Folium for interactive map creation
- **Population Data**: County-level census data integration
- **Wind Modeling**: Directional spread algorithms

For comprehensive documentation on:
- Map generation algorithms
- Population calculation methods
- Wind-adjusted spread modeling
- County-level analysis

See the [Maps Documentation](maps/MAPS.md).

## Browser Support

- **Chrome/Edge**: Full support (recommended)
- **Firefox**: Full support
- **Safari**: Full support
- **Mobile Browsers**: iOS Safari and Chrome Mobile supported

## Performance Considerations

- **Code Splitting**: Route-based code splitting for optimal loading
- **Lazy Loading**: Components loaded on demand
- **Caching**: React Query caching for API responses
- **Optimized Builds**: Vite production builds with tree-shaking
- **Image Optimization**: Optimized static assets

## Troubleshooting

### Common Issues

**Backend Connection Errors:**
- Verify backend is running on correct port
- Check `VITE_API_URL` environment variable
- Review CORS settings in backend

**Map Display Issues:**
- Verify Mapbox token is configured (if using Mapbox)
- Check browser console for errors
- Ensure map generation service is accessible

**Build Errors:**
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version compatibility
- Review TypeScript errors in terminal

**Webcam Detection Not Working:**
- Verify webcam service is running
- Check network connectivity to detection service
- Review browser permissions for camera access

## Future Enhancements

Potential improvements for future development:

- **Real-Time Updates**: WebSocket integration for live prediction updates
- **Mobile App**: Native mobile application version
- **Offline Support**: Service worker for offline functionality
- **Advanced Visualizations**: Additional chart types and analytics
- **Export Features**: PDF/Excel export of predictions and reports
- **Multi-Language Support**: Internationalization (i18n)
- **User Authentication**: User accounts and saved preferences
- **Collaboration Features**: Shared predictions and team coordination

## Related Documentation

- **[Main Project README](../../README.md)**: Comprehensive documentation of machine learning models, methodology, and implementation
- **[About This Project](../../ABOUT_THIS_PROJECT.md)**: Project overview, business case, value proposition, and competitive advantages
- **[Data Processing Documentation](../../../data_processing/DATA_PROCESSING.md)**: Information about data integration, preprocessing, and statistical analysis
- **[Maps Documentation](maps/MAPS.md)**: Detailed documentation of map implementation, population calculations, and wind-adjusted predictions
- **[Fire Detection Documentation](../../../fire-detection/FIRE_DETECTION.md)**: Documentation of automated fire detection system using YOLOv8



