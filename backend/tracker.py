"""
Centroid and IoU-based Person Tracker.
"""
import numpy as np

class Tracker:
    def __init__(self, max_lost=10, iou_threshold=0.3, max_distance=150.0):
        """
        Initialize the tracker
        
        Args:
            max_lost: Maximum number of consecutive frames a track can be lost before deletion.
            iou_threshold: Minimum IoU overlap to match detections to existing tracks.
            max_distance: Maximum distance (in pixels) for centroid fallback matching.
        """
        self.max_lost = max_lost
        self.iou_threshold = iou_threshold
        self.max_distance = max_distance
        self.next_id = 1
        self.tracks = {}  # id -> {box, history, velocity, lost_count}

    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union (IoU) of two bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1[:4]
        x1_2, y1_2, x2_2, y2_2 = box2[:4]
        
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        inter_area = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        return inter_area / union_area

    def track(self, detections):
        """
        Track detections across frames.
        
        Args:
            detections: List of bounding boxes with confidence: [[x1, y1, x2, y2, confidence], ...]
            
        Returns:
            List of tracked objects:
            [
                {
                    "id": track_id,
                    "box": [x1, y1, x2, y2],
                    "velocity": (vx, vy),
                    "history": [(cx, cy), ...]
                },
                ...
            ]
        """
        updated_tracks = {}
        matched_detection_indices = set()
        
        # Try to match detections to existing tracks
        track_ids = list(self.tracks.keys())
        if track_ids and detections:
            # 1. Match using IoU
            for t_id in track_ids:
                best_iou = -1.0
                best_d_idx = -1
                for d_idx, det in enumerate(detections):
                    if d_idx in matched_detection_indices:
                        continue
                    iou = self._calculate_iou(self.tracks[t_id]["box"], det)
                    if iou > best_iou:
                        best_iou = iou
                        best_d_idx = d_idx
                
                if best_iou >= self.iou_threshold and best_d_idx != -1:
                    # Match found
                    det = detections[best_d_idx]
                    prev_box = self.tracks[t_id]["box"]
                    prev_cx = (prev_box[0] + prev_box[2]) / 2.0
                    prev_cy = (prev_box[1] + prev_box[3]) / 2.0
                    cx = (det[0] + det[2]) / 2.0
                    cy = (det[1] + det[3]) / 2.0
                    velocity = (cx - prev_cx, cy - prev_cy)
                    
                    history = self.tracks[t_id].get("history", [])
                    history.append((cx, cy))
                    if len(history) > 15:
                        history.pop(0)
                        
                    updated_tracks[t_id] = {
                        "box": det[:4],
                        "velocity": velocity,
                        "history": history,
                        "lost_count": 0
                    }
                    matched_detection_indices.add(best_d_idx)
            
            # 2. Centroid distance fallback for remaining unmatched tracks
            for t_id in track_ids:
                if t_id in updated_tracks:
                    continue
                
                prev_box = self.tracks[t_id]["box"]
                prev_cx = (prev_box[0] + prev_box[2]) / 2.0
                prev_cy = (prev_box[1] + prev_box[3]) / 2.0
                
                best_dist = float('inf')
                best_d_idx = -1
                
                for d_idx, det in enumerate(detections):
                    if d_idx in matched_detection_indices:
                        continue
                    cx = (det[0] + det[2]) / 2.0
                    cy = (det[1] + det[3]) / 2.0
                    dist = ((cx - prev_cx)**2 + (cy - prev_cy)**2)**0.5
                    if dist < best_dist:
                        best_dist = dist
                        best_d_idx = d_idx
                
                if best_dist <= self.max_distance and best_d_idx != -1:
                    # Match found by centroid distance fallback
                    det = detections[best_d_idx]
                    cx = (det[0] + det[2]) / 2.0
                    cy = (det[1] + det[3]) / 2.0
                    velocity = (cx - prev_cx, cy - prev_cy)
                    
                    history = self.tracks[t_id].get("history", [])
                    history.append((cx, cy))
                    if len(history) > 15:
                        history.pop(0)
                        
                    updated_tracks[t_id] = {
                        "box": det[:4],
                        "velocity": velocity,
                        "history": history,
                        "lost_count": 0
                    }
                    matched_detection_indices.add(best_d_idx)
        
        # Handle lost tracks
        for t_id in self.tracks:
            if t_id not in updated_tracks:
                lost_count = self.tracks[t_id]["lost_count"] + 1
                if lost_count <= self.max_lost:
                    updated_tracks[t_id] = self.tracks[t_id].copy()
                    updated_tracks[t_id]["lost_count"] = lost_count
                    # Decay velocity
                    vx, vy = updated_tracks[t_id]["velocity"]
                    updated_tracks[t_id]["velocity"] = (vx * 0.5, vy * 0.5)
        
        # Add new tracks for unmatched detections
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_detection_indices:
                cx = (det[0] + det[2]) / 2.0
                cy = (det[1] + det[3]) / 2.0
                updated_tracks[self.next_id] = {
                    "box": det[:4],
                    "velocity": (0.0, 0.0),
                    "history": [(cx, cy)],
                    "lost_count": 0
                }
                self.next_id += 1
                
        self.tracks = updated_tracks
        
        # Return format expected by aggressor detector
        tracked_objects = []
        for t_id, info in self.tracks.items():
            if info["lost_count"] == 0:
                tracked_objects.append({
                    "id": t_id,
                    "box": info["box"],
                    "velocity": info["velocity"],
                    "history": info["history"]
                })
        return tracked_objects
