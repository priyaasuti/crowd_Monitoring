"""
FPS and Performance Metrics Module
Tracks inference speed and model performance
"""
import time
from collections import deque
import cv2


class FPSCounter:
    """Calculate and display FPS metrics"""
    
    def __init__(self, window_size=30):
        """
        Initialize FPS counter
        
        Args:
            window_size: Number of frames to average over (default: 30)
        """
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.last_time = time.time()
        self.frame_count = 0
        self.start_time = time.time()
    
    def tick(self):
        """Call this once per frame to update FPS"""
        current_time = time.time()
        frame_time = current_time - self.last_time
        self.frame_times.append(frame_time)
        self.last_time = current_time
        self.frame_count += 1
    
    def get_fps(self):
        """Get current FPS"""
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        if avg_frame_time == 0:
            return 0.0
        return 1.0 / avg_frame_time
    
    def get_avg_frame_time_ms(self):
        """Get average frame time in milliseconds"""
        if not self.frame_times:
            return 0.0
        return (sum(self.frame_times) / len(self.frame_times)) * 1000
    
    def get_total_frames(self):
        """Get total frames processed"""
        return self.frame_count
    
    def get_elapsed_time(self):
        """Get total elapsed time in seconds"""
        return time.time() - self.start_time


class PerformanceTracker:
    """Track detection and inference performance"""
    
    def __init__(self):
        self.fps_counter = FPSCounter()
        self.detection_times = deque(maxlen=30)
        self.total_detections = 0
        self.total_people_detected = 0
    
    def start_frame(self):
        """Call at start of each frame"""
        self.frame_start = time.time()
    
    def end_frame(self, people_count=0):
        """Call at end of each frame"""
        self.fps_counter.tick()
        
        if people_count > 0:
            self.total_detections += 1
            self.total_people_detected += people_count
        
        frame_time = (time.time() - self.frame_start) * 1000  # Convert to ms
        self.detection_times.append(frame_time)
    
    def get_metrics(self):
        """Get all performance metrics"""
        avg_detection_time = (sum(self.detection_times) / len(self.detection_times) 
                             if self.detection_times else 0)
        
        return {
            "fps": self.fps_counter.get_fps(),
            "frame_time_ms": self.fps_counter.get_avg_frame_time_ms(),
            "detection_time_ms": avg_detection_time,
            "total_frames": self.fps_counter.get_total_frames(),
            "total_detections": self.total_detections,
            "total_people": self.total_people_detected,
            "elapsed_seconds": self.fps_counter.get_elapsed_time(),
            "avg_people_per_detection": (
                self.total_people_detected / self.total_detections 
                if self.total_detections > 0 else 0
            )
        }
    
    def print_metrics(self):
        """Print performance metrics"""
        metrics = self.get_metrics()
        print("\n" + "="*70)
        print("📊 PERFORMANCE METRICS")
        print("="*70)
        print(f"FPS: {metrics['fps']:.1f}")
        print(f"Frame Time: {metrics['frame_time_ms']:.1f} ms")
        print(f"Detection Time: {metrics['detection_time_ms']:.1f} ms")
        print(f"Total Frames: {metrics['total_frames']}")
        print(f"Total Detections: {metrics['total_detections']}")
        print(f"Total People: {metrics['total_people']}")
        print(f"Elapsed Time: {metrics['elapsed_seconds']:.1f}s")
        print("="*70 + "\n")


def draw_fps_on_frame(frame, fps, frame_time_ms=None, detection_count=None):
    """
    Draw FPS counter and metrics on video frame
    
    Args:
        frame: OpenCV frame
        fps: Current FPS value
        frame_time_ms: Frame processing time in milliseconds
        detection_count: Number of people detected
    
    Returns:
        Frame with FPS overlay
    """
    frame_copy = frame.copy()
    
    # FPS text (top-left)
    fps_text = f"FPS: {fps:.1f}"
    cv2.putText(
        frame_copy,
        fps_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),  # Green
        2,
        cv2.LINE_AA
    )
    
    # Frame time (top-left, below FPS)
    if frame_time_ms is not None:
        time_text = f"Frame: {frame_time_ms:.1f}ms"
        cv2.putText(
            frame_copy,
            time_text,
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (200, 200, 0),  # Cyan
            2,
            cv2.LINE_AA
        )
    
    # Detection count (top-right)
    if detection_count is not None:
        count_text = f"People: {detection_count}"
        text_size = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        x_pos = frame.shape[1] - text_size[0] - 10
        cv2.putText(
            frame_copy,
            count_text,
            (x_pos, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),  # Blue/Red
            2,
            cv2.LINE_AA
        )
    
    return frame_copy


if __name__ == "__main__":
    # Test the FPS counter
    tracker = PerformanceTracker()
    
    print("Testing FPS Counter...")
    for i in range(60):
        tracker.start_frame()
        time.sleep(0.033)  # Simulate 30 FPS
        tracker.end_frame(people_count=i % 5)
    
    tracker.print_metrics()
