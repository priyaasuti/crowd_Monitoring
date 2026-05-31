# 🚀 AI Crowd Monitoring System - Setup Guide

## Project Overview

This is a full-stack AI-powered crowd monitoring system that:
- Detects people in real-time using YOLOv8
- Counts crowd size and tracks history
- Detects sudden crowd spikes with alerts
- Displays real-time metrics and alerts on a modern dashboard

### Tech Stack
- **Backend**: Python, Flask, OpenCV, YOLOv8
- **Frontend**: React, Vite, Tailwind CSS, Recharts
- **AI**: Ultralytics YOLOv8 for person detection

---

## 📁 Project Structure

```
crowd/
├── backend/
│   ├── main.py              # Video capture & processing loop
│   ├── detector.py          # YOLO person detection
│   ├── analysis.py          # Crowd analysis & spike detection
│   ├── api.py               # Flask API server
│   ├── requirements.txt      # Python dependencies
│   └── models/              # YOLO model storage
│
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── App.jsx          # Main app component
    │   ├── main.jsx         # React entry point
    │   └── index.css        # Global styles
    ├── package.json         # Node dependencies
    ├── vite.config.js       # Vite config
    ├── tailwind.config.js   # Tailwind config
    └── index.html           # HTML entry point
```

---

## ⚙️ Backend Setup

### 1. Prerequisites
- Python 3.8+
- pip
- Webcam (or video file)

### 2. Install Dependencies

Navigate to the backend directory:
```bash
cd crowd/backend
pip install -r requirements.txt
```

### 3. Download YOLOv8 Model

The model will auto-download on first run, but you can pre-download it:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

This downloads YOLOv8 Nano (~6MB) to your user directory. The API will automatically find it.

### 4. Run the Backend

```bash
cd crowd/backend
python api.py
```

**Expected Output:**
```
Starting monitoring system with webcam...
Starting Flask API server on http://localhost:5000
```

The backend will:
- Start video capture from your webcam
- Initialize YOLO detection
- Run the Flask server on `http://localhost:5000`

**API Endpoints:**
- `GET /data` - Current metrics (count, average, spike, status)
- `GET /frame` - Current video frame (base64 encoded JPEG)
- `GET /events` - Event log
- `GET /health` - Health check

---

## 🎨 Frontend Setup

### 1. Prerequisites
- Node.js 16+ and npm (or yarn/pnpm)

### 2. Install Dependencies

Navigate to the frontend directory:
```bash
cd crowd/frontend
npm install
```

### 3. Run Development Server

```bash
npm run dev
```

This will:
- Start Vite dev server (usually on `http://localhost:3000`)
- Open the dashboard in your browser
- Enable hot-reload for development

### 4. Build for Production

```bash
npm run build
```

Output will be in the `dist/` folder.

---

## 🎬 Running the Full System

### Step 1: Terminal 1 - Backend
```bash
cd crowd/backend
python api.py
```
Wait for: `Starting Flask API server on http://localhost:5000`

### Step 2: Terminal 2 - Frontend
```bash
cd crowd/frontend
npm run dev
```
Wait for: Application should open in your browser

### Step 3: Access Dashboard
Open `http://localhost:3000` in your browser

---

## 📊 Dashboard Features

### 1. **Real-Time Video Feed**
- Live camera feed with bounding boxes around detected people
- Updates every 500ms

### 2. **Metrics Cards**
- **People Count**: Current number of people detected
- **Average**: Historical average over 30 frames
- **Spike**: Difference between current and average
- **Status**: NORMAL or ALERT (red when spike > threshold)

### 3. **Status Banner**
- Large, color-coded status indicator
- Shows current count and average
- Pulses when alert is active

### 4. **Crowd Size Graph**
- Line chart showing count history (30 frames)
- Real-time updates
- Helps visualize crowd trends

### 5. **Event Log**
- Chronological list of alerts
- Shows timestamp, spike count, and average
- Stores up to 100 events

### 6. **ML Models Panel**
- Shows available models and their status
- YOLOv8 Nano: Person detection model
- Crowd Analyzer: Spike detection engine

---

## ⚙️ Configuration

### Backend Configuration

Edit `backend/analysis.py` to adjust detection sensitivity:

```python
# Constructor parameters:
history_size=30              # Number of frames to track
spike_threshold=5            # Alert threshold (current - average > this)
frames_for_alert=3          # Frames needed before triggering alert
```

**Examples:**
- Sensitive alerts: `spike_threshold=2, frames_for_alert=2`
- Relaxed alerts: `spike_threshold=10, frames_for_alert=5`

### Frontend Configuration

Edit `frontend/src/App.jsx` to change:

```javascript
const API_BASE_URL = 'http://localhost:5000'  // Backend URL
// Fetch intervals:
// Data: 1000ms (1 second)
// Frame: 500ms (0.5 seconds)
// Events: 2000ms (2 seconds)
```

---

## 🎯 Using Different Video Sources

### Option 1: Webcam (Default)
Already configured. Just run the backend.

### Option 2: Video File
Edit `backend/api.py`:

```python
if __name__ == '__main__':
    # Change from 0 to video file path
    start_monitoring(video_source='path/to/video.mp4')
```

### Option 3: IP Camera
```python
start_monitoring(video_source='rtsp://camera_url/stream')
```

---

## 🚨 Alert System

### How Alerts Work:

1. **Detection**: YOLO detects people in each frame
2. **Analysis**: Compares current count to historical average
3. **Spike Calculation**: `spike = current_count - average_count`
4. **Temporal Validation**: Alert only after N consecutive spike frames (default: 3)
5. **Status Change**: 
   - If spike > threshold → Status becomes "ALERT"
   - Red banner appears and pulses
   - Toast notification shown
   - Event logged with timestamp

### Example Scenario:
```
Frame 1: count=5, avg=3 → spike=2  (below threshold)
Frame 2: count=6, avg=3 → spike=3  (below threshold)
Frame 3: count=8, avg=3 → spike=5  (THRESHOLD=5, frame 1 of alert)
Frame 4: count=9, avg=3 → spike=6  (frame 2 of alert)
Frame 5: count=10, avg=3 → spike=7 (frame 3 of alert - ALERT TRIGGERED!)
```

---

## 🐛 Troubleshooting

### Backend Issues

**Error: "Module not found: ultralytics"**
```bash
pip install ultralytics
```

**Error: "Cannot open video source 0" (Webcam)**
- Check if your webcam is connected
- Try: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`
- Give permissions to camera if prompted

**Error: Model download fails**
```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
# Or manually download from: https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### Frontend Issues

**Error: "Cannot fetch from localhost:5000"**
- Ensure backend is running on port 5000
- Check CORS is enabled in Flask (already enabled in api.py)
- Check firewall settings

**Error: "npm ERR! ERESOLVE"**
```bash
npm install --legacy-peer-deps
```

**Video feed not updating**
- Check backend frame endpoint: `curl http://localhost:5000/frame`
- Ensure webcam permission is granted

### Common Solutions

1. **Clear caches**:
   ```bash
   # Frontend
   cd frontend
   rm -rf node_modules dist
   npm install
   
   # Backend
   pip install --upgrade --force-reinstall ultralytics
   ```

2. **Check ports**:
   - Backend: `netstat -an | findstr :5000` (Windows)
   - Frontend: `netstat -an | findstr :3000`

3. **Restart services**:
   - Stop both terminals (Ctrl+C)
   - Kill processes on ports 5000 and 3000
   - Restart backend, then frontend

---

## 📈 Performance Tips

1. **Reduce frame size** (in main.py):
   ```python
   frame = cv2.resize(frame, (320, 240))  # Smaller = faster
   ```

2. **Reduce detection frequency**:
   ```python
   # Process every Nth frame
   if frame_count % 2 == 0:
       detection = self.detector.detect(frame)
   ```

3. **Use faster model**:
   ```python
   # In detector.py, change model
   self.model = YOLO('yolov8n.pt')  # Nano (fast)
   # self.model = YOLO('yolov8s.pt')  # Small
   # self.model = YOLO('yolov8m.pt')  # Medium
   ```

---

## 📚 API Reference

### GET /data
Returns current monitoring metrics.

**Response:**
```json
{
  "count": 5,
  "average": 3.2,
  "spike": 1.8,
  "status": "NORMAL",
  "alert_triggered": false,
  "history": [2, 3, 4, 5, 3, 2, 5, 4, 3, 5]
}
```

### GET /frame
Returns current video frame.

**Response:**
```json
{
  "frame": "base64_encoded_jpeg",
  "content_type": "image/jpeg"
}
```

### GET /events
Returns event log.

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2024-01-15T10:30:45.123456",
      "type": "SUDDEN_CROWD_DETECTED",
      "data": {
        "count": 10,
        "average": 3.5,
        "spike": 6.5
      }
    }
  ]
}
```

---

## 🎓 How It Works

### Detection Pipeline:
```
Webcam → OpenCV Capture → YOLO Inference → Bounding Boxes
         ↓
      Detection Results (count, boxes, confidence)
         ↓
   Crowd Analyzer → History Tracking → Spike Detection
         ↓
   API Response → Frontend → Dashboard Display
```

### Real-Time Updates:
- **Data**: Fetched every 1 second
- **Video Frame**: Fetched every 0.5 seconds
- **Events**: Fetched every 2 seconds

---

## 🌟 Future Enhancements

- [ ] Multi-camera support
- [ ] Recording and playback
- [ ] Custom alert thresholds per region
- [ ] Heatmap visualization
- [ ] Person tracking (multi-object tracking)
- [ ] Behavior analysis (running, grouping)
- [ ] Historical data storage (database)
- [ ] Export reports
- [ ] Mobile app
- [ ] WebSocket for real-time updates

---

## 📝 License

This project is provided as-is for educational and commercial use.

---

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review console/terminal for error messages
3. Ensure all dependencies are installed
4. Check that both backend and frontend are running

---

**Happy Monitoring! 👥📊**
