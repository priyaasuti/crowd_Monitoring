"""
Main processing loop - capture video and run detection + analysis
"""
import cv2
import numpy as np
import threading
from detector import PersonDetector
from analysis import CrowdAnalyzer
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "yolov8n.pt"


class CrowdMonitoringSystem:
    def __init__(self, model_path=DEFAULT_MODEL_PATH, video_source=0):
        """
        Initialize the monitoring system
        
        Args:
            model_path: Path to YOLO model
            video_source: Video source (0 for webcam, or video file path)
        """
        self.detector = PersonDetector(model_path)
        self.analyzer = CrowdAnalyzer()
        self.video_source = video_source
        self.running = False
        self.current_frame = None
        self.is_processing = False
        self.stop_reason = None
    def _stop_processing(self, reason):
        self.stop_reason = reason
        self.running = False
        print(f"Stopping crowd processing: {reason}", flush=True)
        
    def _create_placeholder_frame(self, width=640, height=480):
        """Create a placeholder frame when camera is unavailable"""
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (20, 20, 30)  # Dark blue-black background
        cv2.putText(frame, "Camera Unavailable", (140, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 2)
        cv2.putText(frame, "Upload video to analyze", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
        return frame

    def process_video_stream(self):
        """
        Main processing loop - capture frames and run detection
        """
        cap = None
        camera_available = False
        test_frame = None
        
        # Only for webcam (source 0), try different backends
        if isinstance(self.video_source, int) and self.video_source == 0:
            print(f"Trying to open webcam with multiple backends...", flush=True)
            
            # Try DirectShow backend first (works better on Windows)
            backends = [
                (cv2.CAP_DSHOW, "DirectShow"),
                (cv2.CAP_MSMF, "Windows Media Foundation"),
                (-1, "Default"),
            ]
            
            for backend_id, backend_name in backends:
                if backend_id == -1:
                    cap = cv2.VideoCapture(self.video_source)
                else:
                    cap = cv2.VideoCapture(self.video_source, backend_id)
                
                print(f"Trying {backend_name}...", flush=True)
                
                if cap.isOpened():
                    # Try to actually read a frame to verify it works
                    ret, test_frame = cap.read()
                    if ret:
                        print(f"Success! Camera opened with {backend_name}", flush=True)
                        camera_available = True
                        break
                    else:
                        print(f"{backend_name} failed to read frame", flush=True)
                        cap.release()
                else:
                    print(f"{backend_name} failed to open", flush=True)
                    cap.release()
        else:
            # For video files, just open normally
            cap = cv2.VideoCapture(self.video_source)
            
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret:
                    print(f"Successfully opened video file: {self.video_source}", flush=True)
                    camera_available = True
                else:
                    print(f"Cannot read from video file: {self.video_source}", flush=True)
            else:
                print(f"Cannot open video file: {self.video_source}", flush=True)
        
        if not camera_available:
            print(f"Warning: Camera not available", flush=True)
            print("System ready for uploaded videos. Showing placeholder frame.", flush=True)
            self.current_frame = self._create_placeholder_frame()
        else:
            # Set initial frame from the test read - just resize and use it directly
            if test_frame is not None:
                test_frame = cv2.resize(test_frame, (640, 480))
                self.current_frame = test_frame
                print(f"Initial frame set. Size: {test_frame.shape}", flush=True)
            else:
                self.current_frame = self._create_placeholder_frame()
        
        print(f"Detection system ready. Starting monitoring...", flush=True)
        frame_count = 0
        
        while self.running:
            if not camera_available:
                # If camera not available, keep placeholder frame and wait for video upload
                import time
                time.sleep(0.1)
                continue
            
            try:
                ret, frame = cap.read()
                if not ret:
                    print("End of video or camera frame error", flush=True)
                    # Assume camera died, set placeholder
                    camera_available = False
                    self.current_frame = self._create_placeholder_frame()
                    print("Switched to placeholder frame. Ready for video upload.", flush=True)
                    break
            except Exception as e:
                print(f"Error reading frame: {e}", flush=True)
                camera_available = False
                self.current_frame = self._create_placeholder_frame()
                break
            
            try:
                frame_count += 1
                # Resize frame for faster processing
                frame = cv2.resize(frame, (640, 480))
                
                # Run detection
                detection = self.detector.detect(frame)
                
                if detection.get("success", True):
                    person_count = detection["count"]
                    status = self.analyzer.add_detection(
                        count=person_count,
                        boxes=detection.get("boxes", []),
                        frame_shape=frame.shape,
                    )
                    
                    # Log every 30 frames (roughly every second at 30fps)
                    if frame_count % 30 == 0:
                        print(f"Frame {frame_count}: Detected {person_count} people", flush=True)
                    
                    # Draw boxes on frame
                    frame_with_boxes = self.detector.draw_boxes(frame, detection)
                    
                    self.current_frame = frame_with_boxes

                    if status.get("sudden_crowd_formation") or status.get("alert_triggered") or status.get("stampede_risk"):
                        self._stop_processing("sudden crowd detected")
                        break
                else:
                    self.current_frame = frame
                
                self.is_processing = False
                
            except Exception as e:
                print(f"Error processing frame: {e}", flush=True)
        
        if camera_available and cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("Video stream closed", flush=True)
    
    
    def start(self):
        """Start the monitoring system"""
        self.running = True
        self.thread = threading.Thread(target=self.process_video_stream, daemon=True)
        self.thread.start()
        print("Crowd monitoring system started")
    
    def stop(self):
        """Stop the monitoring system"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=5)
        print("Crowd monitoring system stopped")
    
    def get_current_status(self):
        """Get current analysis status"""
        return self.analyzer.get_status()
    
    def get_current_frame(self):
        """Get current frame"""
        return self.current_frame
    
    def get_event_log(self):
        """Get event log"""
        return self.analyzer.get_event_log()


# Global instance
monitoring_system = None


def initialize_monitoring(model_path=DEFAULT_MODEL_PATH, video_source=0):
    """Initialize the global monitoring system"""
    global monitoring_system
    monitoring_system = CrowdMonitoringSystem(model_path, video_source)
    monitoring_system.start()
    return monitoring_system


if __name__ == "__main__":
    system = initialize_monitoring()
    
    try:
        import time
        while True:
            time.sleep(1)
            status = system.get_current_status()
            print(f"Count: {status['count']}, Avg: {status['average']}, Status: {status['status']}")
    except KeyboardInterrupt:
        print("Shutting down...")
        system.stop()
