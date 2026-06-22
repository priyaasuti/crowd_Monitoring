"""
YOLOv8-based person detector for the violence analysis pipeline.
"""
from pathlib import Path
import torch

# Monkey-patch torch.load to disable weights_only for YOLO model loading
_original_torch_load = torch.load

def _patched_torch_load(f, *args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(f, *args, **kwargs)

torch.load = _patched_torch_load


class YOLODetector:
    def __init__(self, model_path=None):
        """
        Initialize the YOLO detector
        """
        if model_path is None:
            model_path = Path(__file__).resolve().parent / "models" / "yolov8n.pt"
        self.model_path = model_path
        self.model = None  # Lazy load
        self.person_class_id = 0  # Class 0 is person in COCO dataset
        self.conf_threshold = 0.18

    def _load_model(self):
        """Lazy load the YOLO model"""
        if self.model is None:
            print(f"[YOLO_DETECTOR] Loading YOLO model from {self.model_path}...", flush=True)
            from ultralytics import YOLO
            self.model = YOLO(str(self.model_path))
            print("[YOLO_DETECTOR] YOLO model loaded successfully", flush=True)

    def detect(self, frame):
        """
        Detect people in a frame
        
        Args:
            frame: Input video frame (numpy array)
            
        Returns:
            List of detections: [[x1, y1, x2, y2, confidence]]
        """
        self._load_model()
        try:
            results = self.model(frame, verbose=False, conf=self.conf_threshold, classes=[self.person_class_id])
            result = results[0]
            
            persons = []
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    if class_id == self.person_class_id and conf >= self.conf_threshold:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        persons.append([x1, y1, x2, y2, conf])
            return persons
        except Exception as e:
            print(f"[YOLO_DETECTOR] Error during person detection: {e}", flush=True)
            return []
