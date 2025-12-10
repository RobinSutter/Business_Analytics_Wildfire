# Fire Detection Alarm (YOLOv8)

## Overview

This component provides a lightweight fire/smoke detection loop using a trained YOLOv8 model. It opens either a webcam or a video file, overlays detections, plays an audible alarm, and serves an MJPEG stream plus JSON stats over HTTP for remote viewing.

## Capabilities

- Detects fire/smoke/flame classes with confidence filtering
- Live overlay window with annotated frames; press `q` to exit
- Audible alarm when fire or smoke is detected
- Persistence smoothing to avoid flicker between frames
- Optional frame skipping and top/bottom cropping for performance and focus
- HTTP endpoints (port 8001 by default): `GET /video` (MJPEG), `GET /stats` (JSON)

## Requirements

- Python 3.11+ with project dependencies (`uv sync` from repo root)
- Assets in `fire-detection/` (same folder as the script):
  - `best.pt` (YOLO model weights)
  - `alarm.mp3` (alarm sound)
  - Optional sample: `video.mp4` (used when choosing video mode with default path)
- A webcam (for option 1) or a readable video file (for option 2)

## Quick Start

```bash
# From project root
uv run fire-detection/fire_webcam_alarm.py
```

When prompted, choose your source:
- `1` → Webcam (live capture)
- `2` → Video file (enter a path, defaults to `fire-detection/video.mp4`)

While running:
- View live window locally (OpenCV)
- Stream in a browser or dashboard via `http://localhost:8001/video`
- Poll detection status via `http://localhost:8001/stats`

## Configuration

Tune parameters in `fire_webcam_alarm.py`:
- `CONF_THRESHOLD` (default `0.5`)
- `FRAME_SKIP` (default `4`) to reduce compute
- `CROP_TOP_RATIO`, `CROP_BOTTOM_RATIO` to trim non-relevant regions
- `SERVER_PORT` (default `8001`)
- `PERSISTENCE_FRAMES` to smooth transient detections
- `MODEL_PATH`, `ALARM_SOUND` point to assets in this folder by default

## Troubleshooting

- **Model missing**: Ensure `fire-detection/best.pt` exists; path is resolved relative to the script.
- **Alarm missing**: Ensure `fire-detection/alarm.mp3` exists; the mixer will fail without it.
- **Video not found**: Provide a valid path when selecting option 2; the script exits early if the file is missing or unreadable.
- **Webcam access**: Close other apps using the camera; try a different index (edit `cv2.VideoCapture(0)` if needed).
- **Port in use**: Change `SERVER_PORT` in the script if 8001 is occupied.

## Integration with Frontend

The fire detection system integrates with the frontend webcam monitoring page (`modelling_and_prediction/frontend/src/pages/Webcam.tsx`), which:
- Connects to the MJPEG stream at `http://localhost:8001/video`
- Polls detection status via `http://localhost:8001/stats`
- Displays real-time detection alerts and statistics
- Provides a user interface for monitoring multiple camera feeds

For details on the frontend integration, see the [Frontend Documentation](../modelling_and_prediction/frontend/FRONTEND.md).

## Related Documentation

- **[Main Project README](../README.md)**: Comprehensive documentation of machine learning models, methodology, and implementation
- **[About This Project](../ABOUT_THIS_PROJECT.md)**: Project overview, business case, value proposition, and competitive advantages
- **[Frontend Documentation](../modelling_and_prediction/frontend/FRONTEND.md)**: Documentation of the web interface and user-facing features

## Notes

- The MJPEG stream is simple and unsecured; restrict network exposure if running outside localhost.
- Performance depends on your GPU/CPU. Increase `FRAME_SKIP` or lower resolution if needed.
