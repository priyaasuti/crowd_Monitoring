# 🛡️ AI Crowd Monitoring & Incident Detection System

> **Real-time crowd surveillance powered by YOLOv8, LSTM deep learning, and Google Gemini Vision — with automated Twilio SMS/MMS alerts.**

---

## 📌 What's New (Latest Update)

| Update | Details |
|--------|---------|
| ✅ **Weapon Detection Fixed** | `weapon.pt` was stored as an unzipped directory; repackaged as a proper PyTorch ZIP archive so YOLO can load it |
| ✅ **Bug Fix: scene_frame_base64** | Fixed `NameError` crash in `event_analysis.py` when violence tracking failed mid-run |
| ✅ **Full Pipeline Verified** | End-to-end test confirmed: Violence (90%), Weapon/knife (56%) detected in fight video |
| ✅ **Frontend Integrated** | `EventAnalysisPanel` displays weapon class name, confidence, timestamp, and annotated frame |

---

## 🧠 Project Overview

This is a full-stack AI-powered **crowd monitoring and incident detection** platform that combines:

- **Real-time crowd monitoring** — live webcam + YOLOv8 person detection
- **Post-event video analysis** — LSTM-based violence & accident detection
- **Weapon detection** — YOLOv8 custom model for knives, guns, and weapons
- **Person tracking & aggressor identification** — ByteTrack-style tracker
- **Severity scoring** — risk level assessment per incident
- **AI scene description** — Google Gemini Vision generates a natural language description of the incident frame
- **Automated alerts** — Twilio SMS + MMS with annotated scene image via imgbb

---

## 🗂️ Project Structure

```
crowd_Monitoring/
├── backend/
│   ├── api.py                  # Flask REST API server
│   ├── main.py                 # Webcam capture & real-time monitoring loop
│   ├── detector.py             # YOLOv8 person detection (live feed)
│   ├── analysis.py             # Crowd size analysis & spike detection
│   ├── event_analysis.py       # Full video analysis pipeline (violence + accident + weapon)
│   ├── yolo_detector.py        # YOLOv8 person detector for tracking pipeline
│   ├── tracker.py              # Multi-object tracker (ByteTrack-style)
│   ├── aggressor_detector.py   # Identifies aggressor from tracked persons
│   ├── severity.py             # Incident risk/severity scoring
│   ├── notifier.py             # Twilio SMS/MMS alert system
│   ├── violence_detector.py    # LSTM violence inference module
│   ├── test_alerts.py          # Credential checker (run before starting backend)
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # API keys (NOT committed to git)
│   └── models/
│       ├── yolov8n.pt          # YOLOv8 Nano — person detection (live feed)
│       ├── weapon.pt           # YOLOv8 custom — weapon/knife/gun detection ✅ FIXED
│       ├── violence_model.pth  # LSTM — violence classification
│       └── accident_model_run1.pth  # LSTM — accident classification
│
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main app with routing & live dashboard
    │   ├── components/
    │   │   └── EventAnalysisPanel.jsx  # Video upload + analysis results UI
    │   └── utils/              # API helpers
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

---

## ⚙️ Backend Setup

### 1. Prerequisites

- Python 3.10+
- pip
- Webcam (optional — system works without one for video analysis)

### 2. Install Dependencies

```bash
cd crowd_Monitoring/backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `backend/.env` with your API keys:

```env
# Google Gemini (scene description)
GOOGLE_API_KEY=your_google_ai_studio_key_here

# imgbb (uploads annotated scene frame for MMS)
IMGBB_API_KEY=your_imgbb_key_here

# Twilio (SMS/MMS alerts)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
TWILIO_TO_NUMBER=+91XXXXXXXXXX

# Optional: override location label in alerts
# SYSTEM_LOCATION=Gate 3 - Main Entrance
```

### 4. Verify All Credentials

Run this before starting the backend for the first time:

```bash
python test_alerts.py
```

This checks all API keys, tests Twilio, imgbb, and Gemini — and optionally sends a real test SMS.

### 5. Start the Backend

```bash
python api.py
```

**Expected output:**
```
[EVENT_ANALYSIS] Google API Key loaded: True
Initializing monitoring system with source: 0...
Monitoring system initialized successfully
Starting Flask API server on http://localhost:5000
 * Running on http://127.0.0.1:5000
```

> If no webcam is present, the server still starts. Video upload and analysis features remain fully available.

---

## 🎨 Frontend Setup

### 1. Prerequisites

- Node.js 16+ and npm

### 2. Install Dependencies

```bash
cd crowd_Monitoring/frontend
npm install
```

### 3. Start the Dev Server

```bash
npm run dev
```

Frontend runs at **http://localhost:3000**

### 4. Production Build

```bash
npm run build
```

Output goes to `dist/`.

---

## 🚀 Running the Full System

**Terminal 1 — Backend:**
```bash
cd crowd_Monitoring/backend
python api.py
```

**Terminal 2 — Frontend:**
```bash
cd crowd_Monitoring/frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## 📊 Dashboard Features

### 🔴 Live Crowd Monitoring Tab
| Feature | Description |
|---------|-------------|
| **Live Video Feed** | Webcam stream with bounding boxes, updates every 500ms |
| **People Count** | Current number of detected persons |
| **Spike Detection** | Alerts when crowd surges above baseline |
| **Crowd Graph** | Real-time line chart of count history |
| **Event Log** | Timestamped alert history |

### 🎬 Event Analysis Tab (Video Upload)

Upload any video file (MP4, AVI, MOV, etc.) to run the full AI analysis pipeline:

| Model | Task | Architecture |
|-------|------|-------------|
| **MobileNetV2** | Feature extraction from frames | CNN backbone |
| **Violence LSTM** | Detects physical violence | MobileNetV2 + LSTM |
| **Accident LSTM** | Detects accidents/falls | MobileNetV2 + LSTM |
| **Weapon YOLOv8** | Detects knives, guns, weapons | Custom YOLOv8 detect |
| **ByteTracker** | Person tracking + aggressor ID | Multi-object tracking |
| **Gemini Vision** | Natural language scene description | Google Gemini 1.5 Flash |

**Results include:**
- Incident type (Violence / Accident / Weapon / No Incident)
- Confidence score and timestamp
- Annotated scene frame with bounding boxes
- Aggressor ID and severity risk level (Low / Medium / High)
- Weapon class name (knife, gun, weapon)
- AI-generated scene description
- Automatic Twilio SMS + MMS alert if incident detected

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/data` | Live crowd metrics (count, spike, status, etc.) |
| `GET` | `/frame` | Current video frame (base64 JPEG) |
| `GET` | `/events` | Event log |
| `POST` | `/upload-video` | Upload video for live monitoring source |
| `POST` | `/analyze-event-video` | Upload video for full AI incident analysis |
| `GET` | `/analysis-jobs/<id>` | Poll async scene description job status |
| `POST` | `/switch-source` | Switch monitoring between webcam and video |
| `POST` | `/caption-image` | Generate BLIP caption for an image |

### POST `/analyze-event-video` Response Example

```json
{
  "incident_type": "Violence",
  "confidence_score": 0.9041,
  "timestamp": "00:11",
  "location": "Gate 3 - Main Entrance",
  "models": {
    "violence": { "detected": true, "confidence": 0.9041, "risk_level": "High Risk" },
    "accident": { "detected": false, "confidence": 0.0005 },
    "weapon":   { "detected": true,  "confidence": 0.5602, "class_name": "knife", "timestamp": "00:03" }
  },
  "scene_description": "...",
  "scene_frame": "<base64_annotated_image>",
  "analysis_job_id": "abc123"
}
```

---

## 🚨 Alert System

When a **Violence**, **Accident**, or **Weapon** is detected in an uploaded video:

1. **Scene frame** extracted and annotated (bounding boxes / tracking overlays)
2. **imgbb upload** — annotated frame is uploaded to get a public URL
3. **Twilio SMS** sent to configured number with incident type, location, confidence
4. **Twilio MMS** sent with the annotated scene image attached
5. **Gemini Vision** generates a natural language description of the scene (async)

Alert format:
```
🚨 INCIDENT ALERT
Type: Violence
Location: Gate 3 - Main Entrance
Confidence: 90.4%
Time: 00:11
[Annotated image attached]
```

---

## 🔍 Detection Pipeline (Event Analysis)

```
Uploaded Video
    │
    ├─► Frame Sampling (8 fps)
    │       │
    │       ├─► MobileNetV2 Feature Extraction (shared)
    │       │       │
    │       │       ├─► Violence LSTM  ──► Violence Score
    │       │       └─► Accident LSTM  ──► Accident Score
    │       │
    │       └─► Weapon YOLOv8 (every 2nd frame) ──► Best Detection
    │
    ├─► If Violence Detected:
    │       YOLOv8 Person Detection
    │       Multi-Object Tracker
    │       Aggressor Identifier
    │       Severity Scorer
    │       Annotated Frame
    │
    └─► Highest Confidence Incident Wins
            │
            ├─► Gemini Vision → Scene Description
            ├─► imgbb → Public Image URL
            └─► Twilio → SMS + MMS Alert
```

---

## 🛠️ Troubleshooting

### `weapon.pt` fails to load
The model file must be a single `.pt` file (PyTorch ZIP format), **not** an unzipped directory. If it fails, check:
```bash
python -c "from pathlib import Path; p = Path('models/weapon.pt'); print('file?', p.is_file(), 'dir?', p.is_dir())"
```
If it's a directory, run the repackaging script from the previous setup session.

### `PermissionError: weapon.pt`
PyTorch cannot open a directory as a file. The model must be a regular file. See fix above.

### Webcam not found
```bash
python -c "import cv2; c=cv2.VideoCapture(0); print('opened:', c.isOpened())"
```
The backend starts without a webcam — use video file upload instead.

### `None of PyTorch, TensorFlow >= 2.0 found`
This warning from `transformers` is harmless when `torch` 2.0.x is installed. All models still load and run correctly.

### Frontend can't reach backend
- Confirm backend is running: `curl http://localhost:5000/health`
- Check CORS is enabled (already enabled in `api.py` via `flask-cors`)

### Gemini scene description not appearing
Scene descriptions are generated **asynchronously**. Poll `/analysis-jobs/<id>` every 2–3 seconds until `scene_status` becomes `"ready"`.

---

## ⚙️ Configuration

### Detection Thresholds (`event_analysis.py`)
```python
WEAPON_CONFIDENCE_THRESHOLD = 0.3   # Min YOLO confidence for weapon
VIOLENCE_THRESHOLD = 0.6            # Min LSTM score for violence
ACCIDENT_THRESHOLD = 0.5            # Min LSTM score for accident
WEAPON_FRAME_SKIP = 2               # Scan every Nth frame (performance)
```

### Crowd Spike Sensitivity (`analysis.py`)
```python
history_size = 30        # Frames to average over
spike_threshold = 5      # Alert if (current - average) > this
frames_for_alert = 3     # Consecutive spike frames before alert fires
```

---

## 🧩 Models

| File | Type | Purpose | Size |
|------|------|---------|------|
| `yolov8n.pt` | YOLOv8 Nano | Live crowd person detection | ~6 MB |
| `weapon.pt` | YOLOv8 Custom | Knife / gun / weapon detection | ~22 MB |
| `violence_model.pth` | LSTM | Violence classification | ~6 MB |
| `accident_model_run1.pth` | LSTM | Accident classification | ~6 MB |

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10, Flask, Flask-CORS |
| **Computer Vision** | OpenCV, YOLOv8 (Ultralytics) |
| **Deep Learning** | PyTorch, TorchVision, MobileNetV2, LSTM |
| **Scene AI** | Google Gemini 1.5 Flash (Vision) |
| **Image Caption** | Salesforce BLIP (optional) |
| **Alerts** | Twilio SMS/MMS + imgbb image hosting |
| **Frontend** | React 18, Vite 5, Tailwind CSS, Recharts |
| **Tracking** | Custom ByteTrack-style multi-object tracker |

---

## 📝 License

This project is developed for academic and research purposes.

---

**Built with 🔥 by the crowd monitoring team**
