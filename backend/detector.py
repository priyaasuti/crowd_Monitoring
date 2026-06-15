"""
YOLO-based person detector module
GPU acceleration is handled automatically by YOLO framework
"""
import cv2
import torch

# Monkey-patch torch.load to disable weights_only for YOLO model loading
_original_torch_load = torch.load


def _patched_torch_load(f, *args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(f, *args, **kwargs)


torch.load = _patched_torch_load


class PersonDetector:
    def __init__(self, model_path="models/yolov8n.pt"):
        """
        Initialize the YOLO detector
        GPU acceleration is automatic via YOLO framework

        Args:
            model_path: Path to the YOLOv8 model file
        """
        self.model_path = model_path
        self.model = None  # Lazy loaded
        self.person_class_id = 0  # Person is class 0 in COCO dataset
        self.conf_threshold = 0.18
        print(f"PersonDetector initialized", flush=True)

    def _load_model(self):
        """Lazy load the YOLO model on first use"""
        if self.model is None:
            print(f"Loading YOLO model from {self.model_path}...", flush=True)
            from ultralytics import YOLO

            self.model = YOLO(self.model_path)
            print("✅ YOLO model loaded successfully", flush=True)

    def detect(self, frame):
        """
        Detect people in a frame

        Args:
            frame: Input video frame (numpy array)

        Returns:
            Dictionary with:
            - count: Number of people detected
            - boxes: List of bounding boxes [x1, y1, x2, y2]
            - confidences: List of detection confidence scores
        """
        self._load_model()  # Lazy load on first use

        try:
            results = self.model(frame, verbose=False, conf=self.conf_threshold, classes=[self.person_class_id])
            result = results[0]

            people_boxes = []
            confidences = []

            # YOLO is already restricted to the person class, but keep the
            # class check as a safeguard for custom model swaps.
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])

                    # Only count if confidence > 0.25 and it's a person
                    if class_id == self.person_class_id and conf >= self.conf_threshold:
                        people_boxes.append(box.xyxy[0].tolist())
                        confidences.append(conf)

            return {
                "count": len(people_boxes),
                "boxes": people_boxes,
                "confidences": confidences,
                "success": True,
            }
        except Exception as e:
            print(f"Detection error: {e}", flush=True)
            return {
                "count": 0,
                "boxes": [],
                "confidences": [],
                "success": False,
            }

    def draw_boxes(self, frame, detection_result, fps=None, frame_time_ms=None):
        """
        Draw bounding boxes and detection info on the frame

        Args:
            frame: Input video frame
            detection_result: Detection result from detect()
            fps: Optional FPS value to display
            frame_time_ms: Optional frame processing time in ms

        Returns:
            Frame with drawn boxes and metrics
        """
        frame_copy = frame.copy()
        person_count = detection_result.get("count", 0)

        # Draw each detection box
        for box, conf in zip(detection_result["boxes"], detection_result["confidences"]):
            x1, y1, x2, y2 = box
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Draw bounding box with thicker lines for better visibility
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # Draw filled rectangle for label background
            label = f"Person {conf:.2f}"
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(
                frame_copy, 
                (x1, y1 - text_size[1] - 8),
                (x1 + text_size[0] + 4, y1),
                (0, 255, 0),
                -1  # Filled rectangle
            )

            # Draw label text
            cv2.putText(
                frame_copy,
                label,
                (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),  # Black text on green background
                2,
                cv2.LINE_AA
            )

        # Draw FPS if provided
        if fps is not None:
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(
                frame_copy,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                3,
                cv2.LINE_AA
            )
        
        # Draw frame time if provided
        if frame_time_ms is not None:
            time_text = f"Frame: {frame_time_ms:.1f}ms"
            cv2.putText(
                frame_copy,
                time_text,
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (200, 200, 0),
                2,
                cv2.LINE_AA
            )
        
        # Draw person count at top right
        count_text = f"People Detected: {person_count}"
        text_size = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        x_pos = frame.shape[1] - text_size[0] - 10
        cv2.putText(
            frame_copy,
            count_text,
            (x_pos, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            3,
            cv2.LINE_AA
        )

        return frame_copy