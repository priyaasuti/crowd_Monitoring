# Performance Monitoring & FPS Tracking

## Overview

Your Crowd Monitoring system now includes:
1. **Real-time FPS Counter** - Shows frames per second directly on video
2. **Bounding Boxes** - Enhanced detection boxes around each person
3. **Performance Metrics** - Detailed performance tracking via API

---

## Features

### 1. Bounding Boxes on Video

Each detected person is displayed with:
- **Green bounding box** - Detection boundary
- **Green label box** - Background for text
- **Confidence score** - Detection confidence (0.0 to 1.0)

Visual Example:
```
┌─────────────────────┐
│  Person 0.95        │ ← Confidence score
│  ┌───────────────┐  │
│  │               │  │
│  │   [Person]    │  │ ← Bounding box (green)
│  │               │  │
│  └───────────────┘  │
└─────────────────────┘
```

### 2. FPS Counter

Three metrics displayed on every frame:

**Top-Left Corner:**
- **FPS: XX.X** - Current frames per second (green text)
- **Frame: XX.X ms** - Time to process one frame (cyan text)

**Top-Right Corner:**
- **People Detected: N** - Count of detected people (red text)

### 3. Performance API Endpoint

New endpoint: `/performance`

```bash
curl http://localhost:5000/performance
```

Response:
```json
{
  "fps": 22.5,
  "frame_time_ms": 44.4,
  "detection_time_ms": 35.2,
  "total_frames": 450,
  "total_detections": 89,
  "total_people": 245,
  "elapsed_seconds": 20.1,
  "avg_people_per_detection": 2.75
}
```

---

## Usage

### Start the System

```bash
cd /home/priya/crowd_Monitoring/backend
source venv/bin/activate
python api.py
```

### Monitor in Real-Time

```bash
# In another terminal
curl http://localhost:5000/frame | jq -r '.frame' > frame.jpg
# View the frame with FPS and bounding boxes
```

### Get Performance Metrics

```bash
# Real-time performance
curl http://localhost:5000/performance | jq .

# Watch performance continuously
watch -n 1 'curl -s http://localhost:5000/performance | jq .'
```

### Full Monitoring Setup

```bash
# Terminal 1: Start API
python api.py

# Terminal 2: Monitor GPU
watch -n 1 nvidia-smi

# Terminal 3: Monitor Performance
watch -n 1 'curl -s http://localhost:5000/performance | jq .'

# Terminal 4: Get video stream
curl http://localhost:5000/frame > output.jpg
```

---

## Performance Metrics Explained

| Metric | Description | Expected Range |
|--------|-------------|-----------------|
| **FPS** | Frames per second | 10-30 |
| **Frame Time** | Milliseconds per frame | 33-100 ms |
| **Detection Time** | Time spent on inference | 20-80 ms |
| **Total Frames** | Cumulative frames processed | Increasing |
| **Total Detections** | Number of times people detected | Increasing |
| **Total People** | Sum of all detections | Increasing |
| **Elapsed Seconds** | Total runtime | Increasing |
| **Avg People/Detection** | Average people per frame | 0-10+ |

### Interpreting Results

**Good Performance:**
- FPS: 15-30
- Frame Time: 33-67 ms
- GPU Usage: 40-80%
- CPU Usage: 10-20%

**Acceptable Performance:**
- FPS: 10-15
- Frame Time: 67-100 ms
- GPU Usage: 80%+
- CPU Usage: 20-30%

**Needs Optimization:**
- FPS: < 10
- Frame Time: > 100 ms
- Could indicate CPU bottleneck or high-resolution input

---

## What's Displayed on Video

### Bounding Box Elements

1. **Green Rectangle** - Detection bounding box
   - Thickness: 3 pixels (visible and clear)
   - Color: Bright green (0, 255, 0)
   - Shows exact detection boundary

2. **Label Background** - Green box above detection
   - Filled rectangle for text background
   - Ensures text is readable

3. **Confidence Score** - "Person X.XX"
   - Shows detection confidence (0.18 to 1.0)
   - Higher = more confident

4. **FPS Counter** (top-left)
   - Shows real-time FPS
   - Updates every frame
   - Bright green for visibility

5. **Frame Time** (top-left, below FPS)
   - Processing time for frame
   - Cyan color for distinction

6. **People Count** (top-right)
   - Total detected people
   - Red color for visibility

---

## Performance Tips

### To Improve FPS

1. **Reduce Resolution** (if using higher than 640x480)
   - Change in main.py: `cv2.resize(frame, (640, 480))`
   - Smaller = faster but less accurate

2. **Reduce Confidence Threshold** (detect more)
   - In detector.py: `self.conf_threshold = 0.18`
   - Lower threshold = more detections = slower

3. **Use Faster Model** (YOLOv8 Nano is already fast)
   - Current: YOLOv8 Nano (fastest)
   - Consider smaller input size

4. **Monitor GPU**
   - Check: `nvidia-smi -l 1`
   - If GPU util < 20%: CPU-bound
   - If GPU util > 80%: GPU-bound

### Typical Performance on Jetson Orin Nano

- **Model**: YOLOv8 Nano
- **Input**: 640x480 frames
- **Expected FPS**: 15-30
- **GPU Memory**: ~300-500 MB
- **CPU Usage**: 10-20%

---

## API Endpoints Summary

### Existing Endpoints

```bash
# Health check with GPU info
curl http://localhost:5000/health

# Get current frame with FPS and boxes
curl http://localhost:5000/frame

# Get current detection data
curl http://localhost:5000/data

# Upload video for analysis
curl -F "file=@video.mp4" http://localhost:5000/upload-video

# Switch video source
curl -X POST http://localhost:5000/switch-source \
  -H "Content-Type: application/json" \
  -d '{"source": 0}'
```

### New Performance Endpoint

```bash
# Get performance metrics
curl http://localhost:5000/performance
```

---

## Console Output Example

When running, you'll see:

```
Detection system ready. Starting monitoring...
✅ YOLO model loaded successfully
PersonDetector initialized
Frame 30: 3 people | FPS: 22.5 | Frame Time: 44.4ms
Frame 60: 5 people | FPS: 23.1 | Frame Time: 43.3ms
Frame 90: 4 people | FPS: 22.8 | Frame Time: 43.8ms

[When stopping the API with Ctrl+C]
======================================================================
📊 PERFORMANCE METRICS
======================================================================
FPS: 22.8
Frame Time: 43.8 ms
Detection Time: 35.2 ms
Total Frames: 450
Total Detections: 89
Total People: 245
Elapsed Time: 20.1s
======================================================================
```

---

## Troubleshooting

### Low FPS (< 10)

1. Check CPU usage: `top` or `htop`
2. Check GPU usage: `nvidia-smi -l 1`
3. Check resolution: Is input > 640x480?
4. Check confidence threshold: Is it too low?

### Bounding Boxes Not Showing

1. Verify detections are happening: `curl http://localhost:5000/data`
2. Check frame is being updated: `curl http://localhost:5000/frame`
3. Verify confidence threshold

### FPS Shows 0

1. Ensure API has been running for at least 1 frame
2. Check console output for errors
3. Verify video source is working

### Performance API Returns Error

1. Check monitoring system is initialized
2. Verify performance_tracker exists
3. Check API logs for errors

---

## Files Modified

1. **detector.py**
   - Enhanced `draw_boxes()` method with FPS and metrics

2. **main.py**
   - Added PerformanceTracker initialization
   - Updated frame processing to track FPS
   - Modified stop() to print metrics

3. **api.py**
   - Added `/performance` endpoint

## Files Created

1. **fps_counter.py**
   - FPSCounter class for FPS calculation
   - PerformanceTracker class for metrics
   - draw_fps_on_frame() utility function

---

## Summary

Your system now provides:
✅ Real-time FPS counter on video
✅ Bounding boxes around detections
✅ Performance metrics via API
✅ Automatic performance tracking
✅ Console performance reports

Expected performance: **10-30 FPS on Jetson Orin Nano with GPU acceleration**

---

Generated: Performance Monitoring Enhancement
System: Jetson Orin Nano with GPU acceleration
Framework: YOLOv8 Nano with real-time metrics
