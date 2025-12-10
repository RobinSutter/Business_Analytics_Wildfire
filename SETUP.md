# FSP Fire Size Predictor - Setup

## Architecture

```
Frontend (React + Vite)    →  http://localhost:8080 (or 5173)
        ↓ HTTP/REST API
Backend (FastAPI)          →  http://localhost:8000
        ↓ joblib (loads model + metadata)
Model (XGBoost)            →  fire_size_model.joblib
Metadata                   →  fire_size_model_metadata.joblib
                               (includes trained label encoders)
```

## Quick Start

### 1. Install Python Dependencies

```bash
# From project root - UV handles everything, no pip needed!
uv sync
```

### 2. Install Frontend Dependencies

```bash
cd modelling_and_prediction/frontend
npm install
cd ../..
```

### 3. Start Backend (Terminal 1)

```bash
# From project root
uv run uvicorn modelling_and_prediction.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend (Terminal 2)

```bash
cd modelling_and_prediction/frontend
npm run dev
```

### 5. Fire Detection Alarm (YOLOv8)

```bash
# From project root
uv run fire-detection/fire_webcam_alarm.py
```

On launch, pick your source:
- `1` uses your webcam (live alarm + stream server on port 8001)
- `2` lets you enter a video file path (defaults to `fire-detection/video.mp4` next to the script)

Ensure `fire-detection/best.pt` (YOLO model) and `fire-detection/alarm.mp3` exist before running.


### 6.. Open the App

Open http://localhost:8080 (or the port shown in your terminal) and make **real predictions** using the trained model!


## Testing the System

### Test Backend API

```powershell
# Health check
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d '{
    "mean_temp": 28.0,
    "max_temp": 35.0,
    "min_temp": 21.0,
    "discovery_temp": 30.0,
    "latitude": 38.5,
    "longitude": -122.5,
    "state": "CA",
    "cause": "Lightning",
    "month": 7,
    "day_of_year": 196,
    "season": "Summer",
    "num_cities": 3
  }'
```

### Verify Frontend Connection

1. Open the frontend in your browser
2. Check that the "Demo Mode" banner is **not** showing (means backend is connected)
3. Make a prediction and check browser DevTools (F12) → Network tab to see API calls
4. Backend logs should show incoming requests

## Requirements

- Python 3.11+
- Node.js 18+
- UV package manager
- Trained model files in `modelling_and_prediction/models/` directory:
  - `fire_size_model.joblib`
  - `fire_size_model_metadata.joblib`

## Model Training

To train the model, run the notebook:
```
modelling_and_prediction/notebooks/fire_model_size.ipynb
```

This generates TWO files that the backend uses:
1. `fire_size_model.joblib` - The trained XGBoost model
2. `fire_size_model_metadata.joblib` - Feature names and trained label encoders

Both files are required for accurate predictions.

## Troubleshooting

### Frontend shows "Demo Mode Active"
- **Cause**: Frontend can't connect to backend
- **Fix**: 
  1. Ensure backend is running on port 8000
  2. Check `.env.local` exists in `frontend/` with: `VITE_API_URL=http://localhost:8000`
  3. Verify CORS is configured for port 8080 in `backend/main.py`
  4. Check browser console (F12) for errors

### Backend won't start
- **Model files missing**: Run `fire_model_size.ipynb` notebook to train and save model
- **Dependencies missing**: Run `uv sync` from project root
- **Port in use**: Stop other processes on port 8000

### Frontend won't start
- **Dependencies missing**: Run `npm install` in `frontend/` directory
- **Port in use**: Vite will automatically try port 8080, then 5173, then others

### Predictions seem wrong
- Backend now uses the **actual trained model** with correct label encoders from metadata
- Check backend logs show: "Model and trained encoders loaded successfully!"
- Verify feature count: 26 features, 13 cause classes, 52 state classes, 4 seasons

## Important Notes

- **No pip needed**: UV manages all Python dependencies via `pyproject.toml`
- **No Streamlit**: We use a modern React frontend + FastAPI backend
- **Real predictions**: Backend loads model AND metadata (which includes trained label encoders)
- **All commands from root**: Run UV commands from the project root directory
- **Trained encoders**: Backend uses the exact same label encoders from training (not recreated)
