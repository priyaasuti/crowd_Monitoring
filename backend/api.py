"""
Flask API server for crowd monitoring
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import base64
import cv2
import io
import os
import platform
import torch
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from main import initialize_monitoring
from pathlib import Path
import threading
from uuid import uuid4
from werkzeug.utils import secure_filename
from event_analysis import _analyze_event_video_core, generate_scene_description
from notifier import trigger_alert

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent

# Configuration
UPLOAD_FOLDER = BASE_DIR / 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize monitoring system
monitoring_system = None
last_alert_logged = False
analysis_jobs = {}
analysis_jobs_lock = threading.Lock()
analysis_scene_executor = ThreadPoolExecutor(max_workers=1)


def _set_analysis_job(job_id, **updates):
    with analysis_jobs_lock:
        job = analysis_jobs.setdefault(job_id, {})
        job.update(updates)
        return dict(job)


def _get_analysis_job(job_id):
    with analysis_jobs_lock:
        job = analysis_jobs.get(job_id)
        return dict(job) if job else None


def _generate_scene_description_async(job_id, scene_frame, incident_type):
    try:
        description = generate_scene_description(scene_frame, incident_type)
        _set_analysis_job(job_id, scene_status="ready", scene_description=description, error=None)
    except Exception as e:
        _set_analysis_job(job_id, scene_status="error", scene_description=None, error=str(e))

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_image_file(filename):
    """Check if image file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_system_location():
    """Return a human-readable local system location label."""
    configured_location = os.getenv('SYSTEM_LOCATION')
    if configured_location:
        return configured_location

    hostname = platform.node() or 'unknown-host'
    return f"{hostname} (local monitoring workstation)"


@lru_cache(maxsize=1)
def get_blip_captioner(model_name="Salesforce/blip-image-captioning-large"):
    """Load and cache the BLIP captioning model."""
    import torch
    from transformers import BlipForConditionalGeneration, BlipProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = BlipProcessor.from_pretrained(model_name)
    model = BlipForConditionalGeneration.from_pretrained(model_name).to(device)
    model.eval()

    return processor, model, device


def build_caption(image, model_name="Salesforce/blip-image-captioning-large"):
    """Generate a BLIP caption for an image."""
    import torch

    processor, model, device = get_blip_captioner(model_name)

    inputs = processor(image, text="a photo of", return_tensors="pt").to(device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=30,
            min_length=10,
            num_beams=5,
            no_repeat_ngram_size=2,
            length_penalty=1.0,
            early_stopping=True,
        )

    caption = processor.decode(output[0], skip_special_tokens=True)
    caption = " ".join(caption.split())

    if caption:
        caption = caption[0].upper() + caption[1:]
        if caption[-1] not in ".!?":
            caption += "."

    return caption


def start_monitoring(video_source=0):
    """Start the monitoring system"""
    global monitoring_system
    
    # Stop existing monitoring if any
    if monitoring_system is not None:
        monitoring_system.stop()
        import time
        time.sleep(0.5)  # Wait for threads to clean up
    
    try:
        monitoring_system = initialize_monitoring(video_source=video_source)
        print(f"Monitoring system started with source: {video_source}", flush=True)
    except Exception as e:
        print(f"Error starting monitoring: {e}", flush=True)
        raise


@app.route('/data', methods=['GET'])
def get_data():
    """Get current crowd monitoring data"""
    if monitoring_system is None:
        return jsonify({
            "error": "Monitoring system not initialized",
            "count": 0,
            "average": 0,
            "recent_average": 0,
            "spike": 0,
            "status": "ERROR",
            "alert_triggered": False,
            "history": [],
            "density_index": 0,
            "occupancy_ratio": 0,
            "concentration_ratio": 0,
            "recent_growth": 0,
            "sudden_crowd_formation": False,
            "overcrowded": False,
            "stampede_risk": False,
            "stampede_risk_score": 0,
            "unusual_gathering": False,
            "risk_level": "LOW",
            "baseline_ready": False
        }), 500
    
    try:
        status = monitoring_system.get_current_status()
        
        response = {
            "count": status.get("count", 0),
            "average": status.get("average", 0),
            "recent_average": status.get("recent_average", 0),
            "spike": status.get("spike", 0),
            "status": status.get("status", "NORMAL"),
            "alert_triggered": status.get("alert_triggered", False),
            "history": status.get("history", []),
            "density_index": status.get("density_index", 0),
            "occupancy_ratio": status.get("occupancy_ratio", 0),
            "concentration_ratio": status.get("concentration_ratio", 0),
            "recent_growth": status.get("recent_growth", 0),
            "sudden_crowd_formation": status.get("sudden_crowd_formation", False),
            "crowd_detected": status.get("crowd_detected", False),
            "overcrowded": status.get("overcrowded", False),
            "stampede_risk": status.get("stampede_risk", False),
            "stampede_risk_score": status.get("stampede_risk_score", 0),
            "unusual_gathering": status.get("unusual_gathering", False),
            "risk_level": status.get("risk_level", "LOW"),
            "baseline_ready": status.get("baseline_ready", False)
        }
        
        return jsonify(response)
    except Exception as e:
        print(f"Error in /data endpoint: {e}", flush=True)
        return jsonify({
            "error": str(e),
            "count": 0,
            "average": 0,
            "recent_average": 0,
            "spike": 0,
            "status": "ERROR",
            "alert_triggered": False,
            "history": [],
            "density_index": 0,
            "occupancy_ratio": 0,
            "concentration_ratio": 0,
            "recent_growth": 0,
            "sudden_crowd_formation": False,
            "overcrowded": False,
            "stampede_risk": False,
            "stampede_risk_score": 0,
            "unusual_gathering": False,
            "risk_level": "LOW",
            "baseline_ready": False
        }), 500


@app.route('/frame', methods=['GET'])
def get_frame():
    """Get current video frame as base64 encoded JPEG"""
    if monitoring_system is None:
        return jsonify({"error": "Monitoring system not initialized"}), 500
    
    frame = monitoring_system.get_current_frame()
    
    if frame is None:
        return jsonify({"error": "No frame available"}), 204
    
    # Encode frame as JPEG
    ret, jpeg_data = cv2.imencode('.jpg', frame)
    if not ret:
        return jsonify({"error": "Failed to encode frame"}), 500
    
    # Convert to base64
    frame_base64 = base64.b64encode(jpeg_data).decode('utf-8')
    
    return jsonify({
        "frame": frame_base64,
        "content_type": "image/jpeg"
    })


@app.route('/events', methods=['GET'])
def get_events():
    """Get event log"""
    if monitoring_system is None:
        return jsonify({"error": "Monitoring system not initialized"}), 500
    
    events = monitoring_system.get_event_log()
    
    return jsonify({
        "events": events
    })


@app.route('/performance', methods=['GET'])
def get_performance():
    """Get performance metrics"""
    if monitoring_system is None:
        return jsonify({"error": "Monitoring system not initialized"}), 500
    
    try:
        if hasattr(monitoring_system, 'performance_tracker'):
            metrics = monitoring_system.performance_tracker.get_metrics()
            return jsonify({
                "fps": metrics['fps'],
                "frame_time_ms": metrics['frame_time_ms'],
                "detection_time_ms": metrics['detection_time_ms'],
                "total_frames": metrics['total_frames'],
                "total_detections": metrics['total_detections'],
                "total_people": metrics['total_people'],
                "elapsed_seconds": metrics['elapsed_seconds'],
                "avg_people_per_detection": metrics['avg_people_per_detection']
            })
        else:
            return jsonify({"error": "Performance tracker not available"}), 500
    except Exception as e:
        print(f"Error getting performance metrics: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint with GPU info"""
    device_info = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "pytorch_version": torch.__version__,
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else "N/A",
    }
    
    return jsonify({
        "status": "healthy",
        "monitoring_active": monitoring_system is not None,
        "gpu_info": device_info,
        "note": "GPU acceleration enabled through YOLO framework on Jetson"
    })


@app.route('/config', methods=['POST'])
def update_config():
    """Update system configuration"""
    data = request.json
    
    # Implement config updates as needed
    # For now, just acknowledge
    return jsonify({
        "message": "Configuration updated",
        "config": data
    })


@app.route('/upload-video', methods=['POST'])
def upload_video():
    """Upload and process a video file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
    
    try:
        # Save the file
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        import time
        filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print(f"Video uploaded: {filepath}", flush=True)
        
        # Start monitoring with this video file
        start_monitoring(video_source=filepath)
        
        return jsonify({
            "message": "Video uploaded and processing started",
            "filename": filename,
            "filepath": filepath
        }), 200
        
    except Exception as e:
        print(f"Error uploading video: {e}", flush=True)
        return jsonify({
            "error": f"Failed to upload video: {str(e)}"
        }), 500


@app.route('/caption-image', methods=['POST'])
def caption_image():
    """Generate a caption for an uploaded image using BLIP."""
    if 'file' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No image file selected"}), 400

    if not allowed_image_file(file.filename):
        return jsonify({
            "error": f"Image type not allowed. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
        }), 400

    model_name = request.form.get('model', 'Salesforce/blip-image-captioning-large')
    try:
        from PIL import Image

        image = Image.open(file.stream).convert('RGB')
        caption = build_caption(image, model_name=model_name)

        return jsonify({
            "message": "Caption generated successfully",
            "caption": caption,
            "model": model_name,
            "filename": secure_filename(file.filename),
        }), 200
    except Exception as e:
        print(f"Error generating image caption: {e}", flush=True)
        return jsonify({
            "error": f"Failed to generate caption: {str(e)}"
        }), 500


@app.route('/analyze-event-video', methods=['POST'])
def analyze_event_video_upload():
    """Analyze an uploaded video for violence and accident detection."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    try:
        filename = secure_filename(file.filename)
        import time

        filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        system_location = request.form.get('system_location') or get_system_location()
        analysis_result = _analyze_event_video_core(filepath, system_location=system_location)
        
        print(f"[API] Analysis result: incident_type={analysis_result.get('incident_type')}, confidence={analysis_result.get('confidence_score')}", flush=True)

        if analysis_result.get('incident_type') in ['Violence', 'Accident']:
            confidence = analysis_result.get('confidence_score', 0)
            scene_desc = analysis_result.get('scene_description', '')
            print(f"[API] Triggering alert for {analysis_result['incident_type']} (confidence: {confidence})", flush=True)
            alert_result = trigger_alert(
                incident_type=analysis_result['incident_type'],
                location=system_location,
                confidence=confidence,
                scene_description=scene_desc
            )
            print(f"[API] Alert result: {alert_result}", flush=True)

        job_id = uuid4().hex
        scene_frame = None
        if analysis_result.get('scene_frame') and analysis_result.get('incident_type') != 'No Incident':
            try:
                scene_image_data = base64.b64decode(analysis_result['scene_frame'])
                from PIL import Image

                scene_frame = Image.open(io.BytesIO(scene_image_data)).convert('RGB')
                _set_analysis_job(
                    job_id,
                    scene_status='pending',
                    scene_description=None,
                    error=None,
                    filepath=filepath,
                    incident_type=analysis_result['incident_type'],
                )
                analysis_scene_executor.submit(_generate_scene_description_async, job_id, scene_frame, analysis_result['incident_type'])
            except Exception as e:
                _set_analysis_job(job_id, scene_status='error', scene_description=None, error=str(e))
        else:
            _set_analysis_job(job_id, scene_status='ready', scene_description=analysis_result.get('scene_description'), error=None)

        return jsonify({
            **analysis_result,
            "filename": filename,
            "filepath": filepath,
            "analysis_job_id": job_id,
            "scene_status": _get_analysis_job(job_id).get('scene_status', 'ready'),
        }), 200
    except Exception as e:
        print(f"Error analyzing video: {e}", flush=True)
        return jsonify({
            "error": f"Failed to analyze video: {str(e)}"
        }), 500


@app.route('/analysis-jobs/<job_id>', methods=['GET'])
def get_analysis_job(job_id):
    job = _get_analysis_job(job_id)
    if job is None:
        return jsonify({"error": "Analysis job not found"}), 404

    return jsonify({
        "job_id": job_id,
        "scene_status": job.get("scene_status", "ready"),
        "scene_description": job.get("scene_description"),
        "error": job.get("error"),
        "incident_type": job.get("incident_type"),
    })


@app.route('/switch-source', methods=['POST'])
def switch_source():
    """Switch between camera (0) and uploaded video"""
    data = request.json or {}
    source = data.get('source', 0)
    
    try:
        # Convert string "0" to int if needed
        if source == "0" or source == 0:
            source = 0
        
        print(f"Switching to source: {source}", flush=True)
        start_monitoring(video_source=source)
        
        return jsonify({
            "message": f"Switched to source: {source}",
            "current_source": source
        }), 200
        
    except Exception as e:
        print(f"Error switching source: {e}", flush=True)
        return jsonify({
            "error": f"Failed to switch source: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Check if model exists
    model_path = BASE_DIR / "models" / "yolov8n.pt"
    if not model_path.exists():
        print(f"Model not found at {model_path}", flush=True)
        print("Please download YOLOv8n model first:", flush=True)
        print("  from ultralytics import YOLO", flush=True)
        print("  YOLO('yolov8n.pt')  # This will download the model", flush=True)
        exit(1)
    
    # Start monitoring system (0 for webcam, or use a video file path)
    # CHANGE THIS to your video file if camera doesn't work:
    # video_source = "path/to/your/video.mp4"
    video_source = 0  # Use 0 for webcam
    
    print(f"Initializing monitoring system with source: {video_source}...", flush=True)
    try:
        start_monitoring(video_source=video_source)
        print("Monitoring system initialized successfully", flush=True)
    except Exception as e:
        print(f"Warning: Could not initialize monitoring system: {e}", flush=True)
        print("If camera is unavailable, you can still upload videos for analysis", flush=True)
        print("Attempting to start monitoring with camera anyway...", flush=True)
        try:
            start_monitoring(video_source=video_source)
        except:
            print("Could not start monitoring system. API will start without live camera.", flush=True)
    
    # Run Flask app
    print("Starting Flask API server on http://localhost:5000", flush=True)
    print("Press Ctrl+C to stop", flush=True)
    app.run(debug=False, port=5000, use_reloader=False, threaded=True)
