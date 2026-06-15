# 🚀 Deployment Checklist - GPU Acceleration Enabled

## ✅ Pre-Deployment Verification

### Step 1: Verify GPU Hardware
```bash
nvidia-smi
```
Expected: Shows "Orin (nvgpu)" with Driver Version 540.4.0

### Step 2: Check Python Environment
```bash
cd /home/priya/crowd_Monitoring/backend
source venv/bin/activate
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
```
Expected: PyTorch 2.0.1

### Step 3: Verify YOLO Framework
```bash
python3 -c "from ultralytics import YOLO; print('✅ YOLO ready')"
```
Expected: ✅ YOLO ready

### Step 4: Check Imports
```bash
python3 -c "from detector import PersonDetector; from api import app; print('✅ All imports OK')"
```
Expected: ✅ All imports OK

---

## 🚀 Deployment Steps

### Step 1: Start API Server
```bash
cd /home/priya/crowd_Monitoring/backend
source venv/bin/activate
python api.py
```

Expected Output:
```
[EVENT_ANALYSIS] Google API Key loaded: False
PersonDetector initialized
Starting Flask API server on http://localhost:5000
Detection system ready. Starting monitoring...
```

### Step 2: Monitor GPU (New Terminal)
```bash
watch -n 1 nvidia-smi
```

Look for GPU memory and utilization changes during inference.

### Step 3: Test Endpoints (New Terminal)
```bash
# Health check
curl http://localhost:5000/health

# Upload video
curl -F "file=@test_video.mp4" http://localhost:5000/upload-video

# Get current frame
curl http://localhost:5000/frame
```

---

## 📊 Expected Performance

| Metric | Expected Value |
|--------|-----------------|
| Inference Speed | 10-30 FPS |
| GPU Memory | 200-500 MB |
| GPU Utilization | 40-80% |
| CPU Load | 10-20% |
| Latency | 30-100 ms |

---

## 🔍 Verification Tests

### Test 1: API Responds
```bash
curl http://localhost:5000/health
```
Status: HTTP 200 with GPU info

### Test 2: Frame Streaming
```bash
curl http://localhost:5000/frame
```
Status: HTTP 200 with base64 frame data

### Test 3: Video Upload
```bash
curl -F "file=@video.mp4" http://localhost:5000/upload-video
```
Status: HTTP 200 with processing started

### Test 4: GPU Memory Increase
```bash
# Monitor during upload:
watch -n 1 nvidia-smi
```
Observe: GPU memory increases when model loads, increases again during inference

### Test 5: Run Test Script
```bash
python test_gpu_access.py
```
Expected: All tests pass ✅

---

## ⚠️ Common Issues & Solutions

### Issue: API doesn't start
**Solution:**
1. Check port 5000 is available: `lsof -i :5000`
2. Ensure venv is activated
3. Check error logs for details

### Issue: YOLO model download fails
**Solution:**
1. Check internet connection
2. Try manually: `python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`
3. Model will be cached in `~/.ultralytics/`

### Issue: Slow inference (< 5 FPS)
**Solution:**
1. Check GPU utilization: `nvidia-smi -l 1`
2. If GPU utilization is high (>80%): Normal, processing complete
3. If GPU utilization is low (<20%): CPU-bound, check video source

### Issue: High memory usage
**Solution:**
1. YOLO model uses ~300 MB first time (normal)
2. Subsequent runs reuse cached model
3. Memory is released after batch processing

---

## 📈 Production Configuration

### For 24/7 Monitoring
```bash
# Use nohup to keep running after logout
nohup python api.py > api.log 2>&1 &

# Monitor in background
nohup watch -n 1 nvidia-smi > gpu.log 2>&1 &
```

### For Multiple Videos
Current setup: Single stream
To scale:
1. Create worker threads
2. Queue videos for processing
3. Monitor queue depth

### For Better Performance
Current model: YOLOv8 Nano (optimized for edge)
To increase accuracy: Use YOLOv8 Small (slower but more accurate)

---

## 🔐 Security Checklist

- [ ] API port 5000 is firewalled (if external access)
- [ ] Upload folder has permissions set correctly
- [ ] Large file uploads are rate-limited
- [ ] Temporary files are cleaned up

---

## 📊 Monitoring Metrics

Track during deployment:
```bash
# GPU Memory Growth
nvidia-smi --query-gpu=memory.used --format=csv,noheader -l 1

# GPU Utilization
nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader -l 1

# Frame Processing Rate
tail -f api.log | grep "Frame"

# Error Rate
tail -f api.log | grep "Error"
```

---

## ✅ Go/No-Go Criteria

### Go (Green Light)
- [ ] GPU detected by nvidia-smi
- [ ] API server starts without errors
- [ ] /health endpoint responds with GPU info
- [ ] Video upload completes successfully
- [ ] Frame streaming works
- [ ] GPU memory increases during inference
- [ ] Performance 10-30 FPS

### No-Go (Red Light)
- [ ] GPU not detected
- [ ] API fails to start
- [ ] Endpoints return errors
- [ ] Video processing hangs
- [ ] GPU utilization stays at 0%
- [ ] Performance < 2 FPS

---

## 🎯 Final Deployment Commands

### Quick Start
```bash
cd /home/priya/crowd_Monitoring/backend
source venv/bin/activate
python api.py
```

### Full Deployment (3 Terminals)
```bash
# Terminal 1: API
python api.py

# Terminal 2: GPU Monitor
watch -n 1 nvidia-smi

# Terminal 3: Tests
python test_gpu_access.py
```

### Production (Background)
```bash
nohup python api.py > api.log 2>&1 &
tail -f api.log
```

---

## ✅ Deployment Status

- **Code**: ✅ Ready (GPU acceleration enabled)
- **Dependencies**: ✅ Installed (PyTorch, YOLO)
- **Hardware**: ✅ Detected (Jetson + GPU)
- **Configuration**: ✅ Complete (Auto GPU detection)
- **Testing**: ✅ Verified (All imports pass)
- **Documentation**: ✅ Complete (Full guides available)

**Status**: 🚀 **READY FOR DEPLOYMENT**

---

Generated: Deployment Checklist
System: Jetson Orin Nano with NVIDIA GPU
Framework: YOLO v8 with GPU acceleration
