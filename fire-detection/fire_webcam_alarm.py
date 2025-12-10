from pathlib import Path

from ultralytics import YOLO
import cv2
import pygame
import time
import threading
from flask import Flask, Response, jsonify
from flask_cors import CORS

# Configuration
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = str(BASE_DIR / "best.pt")
CONF_THRESHOLD = 0.5
FRAME_SKIP = 4
CROP_TOP_RATIO = 0.15
CROP_BOTTOM_RATIO = 0.03
SERVER_PORT = 8001
ALARM_SOUND = str(BASE_DIR / "alarm.mp3")
PERSISTENCE_FRAMES = 5

# Initialize model and input source
print("[INFO] Loading model...")
model = YOLO(MODEL_PATH)

print("\n[INFO] Select input source:")
print("1. Webcam")
print("2. Video file")
choice = input("Enter choice (1 or 2): ").strip()

if choice == "2":
    default_video = BASE_DIR / "video.mp4"
    video_path = input(f"Enter video file path (default: {default_video}): ").strip() or str(default_video)
    if not Path(video_path).exists():
        print(f"[ERROR] Video file not found at: {video_path}")
        exit(1)
    print(f"[INFO] Loading video from {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video file: {video_path}")
        exit(1)
else:
    print("[INFO] Initialising webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not access webcam.")
        exit(1)

# Initialize audio alarm
pygame.mixer.init()
alarm = pygame.mixer.Sound(ALARM_SOUND)

# State variables
alarm_playing = False
frame_count = 0
last_fire_detected = False
last_smoke_detected = False
detection_persistence = 0
last_annotated_frame = None
latest_jpeg = None
latest_stats = {}
frame_lock = threading.Lock()

# Flask streaming server
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.logger.disabled = True

def mjpeg_stream():
    global latest_jpeg
    last_sent = None
    while True:
        with frame_lock:
            current = latest_jpeg
        if current is not None and current != last_sent:
            last_sent = current
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + current + b"\r\n")
        time.sleep(0.03)

@app.route("/video")
def video_feed():
    return Response(mjpeg_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/stats")
def stats_feed():
    with frame_lock:
        stats = latest_stats.copy() if latest_stats else {"status": "waiting"}
    return jsonify(stats)

def run_server():
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False, threaded=True)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Main detection loop

while True:
    ret, frame = cap.read()
    if not ret:
        print("[INFO] End of video/stream.")
        break

    # Crop out top and bottom portions of the frame
    h = frame.shape[0]
    if CROP_TOP_RATIO > 0:
        crop_top_pixels = int(h * CROP_TOP_RATIO)
    else:
        crop_top_pixels = 0

    if CROP_BOTTOM_RATIO > 0:
        crop_bottom_pixels = int(h * CROP_BOTTOM_RATIO)
    else:
        crop_bottom_pixels = 0

    if crop_top_pixels + crop_bottom_pixels < h:
        frame = frame[crop_top_pixels:h - crop_bottom_pixels, :]

    frame_count += 1
    
    if detection_persistence > 0:
        detection_persistence -= 1
    
    # Skip frames for performance
    if frame_count % FRAME_SKIP != 0:
        display = last_annotated_frame if (detection_persistence > 0 and last_annotated_frame is not None) else frame
        cv2.imshow("Fire Detector (YOLOv8)", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Run detection
    results = model(frame, conf=CONF_THRESHOLD)
    annotated = results[0].plot()

    fire_detected = False
    smoke_detected = False
    detection_types = []

    for box in results[0].boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls].lower()

        if conf >= CONF_THRESHOLD and ('fire' in class_name or 'smoke' in class_name or 'flame' in class_name):
            print(f"[DEBUG] Detected: {model.names[cls]} (confidence: {conf:.2f})")
            
            if 'smoke' in class_name:
                smoke_detected = True
                detection_types.append('smoke')
            else:
                fire_detected = True
                detection_types.append('fire')

    # Update state and persistence
    if fire_detected or smoke_detected:
        detection_persistence = PERSISTENCE_FRAMES
        last_fire_detected = fire_detected
        last_smoke_detected = smoke_detected
        last_annotated_frame = annotated.copy()
    elif detection_persistence > 0:
        fire_detected = last_fire_detected
        smoke_detected = last_smoke_detected
    
    # Encode frame for streaming
    ok, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if ok:
        with frame_lock:
            latest_jpeg = buf.tobytes()
            latest_stats = {
                "fire": fire_detected,
                "smoke": smoke_detected,
                "detections": detection_types,
                "timestamp": time.time(),
            }

    # Handle alarm
    if fire_detected or smoke_detected:
        if not alarm_playing:
            if fire_detected:
                print("[ALERT] FIRE DETECTED!")
                cv2.putText(annotated, "FIRE DETECTED!", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            if smoke_detected:
                print("[ALERT] SMOKE DETECTED!")
                cv2.putText(annotated, "SMOKE DETECTED!", (10, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (100, 100, 255), 3)
            alarm.play()
            alarm_playing = True
    else:
        alarm_playing = False

    cv2.imshow("Fire Detector (YOLOv8)", annotated)

cap.release()
cv2.destroyAllWindows()
