"""
Crowd analysis module - track crowd size, density, and risk signals.
"""
from collections import deque
from datetime import datetime


class CrowdAnalyzer:
    def __init__(
        self,
        history_size=60,
        min_frames_for_analysis=8,
        spike_threshold=4,
        frames_for_alert=3,
        crowd_presence_threshold=5,
        overcrowding_count_threshold=14,
        density_threshold=22.0,
        occupancy_threshold=0.16,
        gathering_threshold=0.55,
        spatial_spread_threshold=0.65,
        spatial_cluster_threshold=0.20,
    ):
        """
        Initialize crowd analyzer.

        Args:
            history_size: Number of frames to keep in history.
            min_frames_for_analysis: Warm-up frames before risk logic becomes active.
            spike_threshold: Minimum increase from recent average to flag sudden formation.
            frames_for_alert: Consecutive risky frames required before alerting.
            crowd_presence_threshold: Minimum count before we even consider it a crowd.
            overcrowding_count_threshold: Absolute count threshold for overcrowding.
            density_threshold: Normalized density threshold (people per megapixel).
            occupancy_threshold: Bounding-box area ratio threshold.
            gathering_threshold: Cluster concentration threshold for unusual gathering.
        """
        self.history = deque(maxlen=history_size)
        self.sample_history = deque(maxlen=history_size)
        self.event_log = deque(maxlen=100)

        self.min_frames_for_analysis = min_frames_for_analysis
        self.spike_threshold = spike_threshold
        self.frames_for_alert = frames_for_alert
        self.crowd_presence_threshold = crowd_presence_threshold
        self.overcrowding_count_threshold = overcrowding_count_threshold
        self.density_threshold = density_threshold
        self.occupancy_threshold = occupancy_threshold
        self.gathering_threshold = gathering_threshold
        self.spatial_spread_threshold = spatial_spread_threshold
        self.spatial_cluster_threshold = spatial_cluster_threshold

        self.risky_frame_count = 0
        self.last_alert_time = None
        self.previous_state = {
            "sudden_crowd_formation": False,
            "overcrowded": False,
            "unusual_gathering": False,
            "stampede_risk": False,
            "risk_level": "LOW",
        }

        self.latest_status = self._build_default_status()

    def _build_default_status(self):
        return {
            "count": 0,
            "average": 0.0,
            "spike": 0.0,
            "history": [],
            "density_index": 0.0,
            "occupancy_ratio": 0.0,
            "concentration_ratio": 0.0,
            "spatial_spread_ratio": 0.0,
            "spatial_cluster_ratio": 0.0,
            "recent_growth": 0,
            "sudden_crowd_formation": False,
            "crowd_detected": False,
            "overcrowded": False,
            "stampede_risk": False,
            "stampede_risk_score": 0,
            "unusual_gathering": False,
            "risk_level": "LOW",
            "status": "NORMAL",
            "alert_triggered": False,
        }

    def add_count(self, count):
        """Backward-compatible helper when only a count is available."""
        return self.add_detection(count=count)

    def add_detection(self, count, boxes=None, frame_shape=None):
        """Add a new detection sample and refresh the risk state."""
        boxes = boxes or []

        self.history.append(int(count))
        self.sample_history.append(self._build_sample(count, boxes, frame_shape))
        self.latest_status = self._evaluate_state()
        return self.latest_status

    def _build_sample(self, count, boxes, frame_shape):
        frame_height = frame_width = 0
        if frame_shape is not None and len(frame_shape) >= 2:
            frame_height = int(frame_shape[0])
            frame_width = int(frame_shape[1])

        frame_area = frame_width * frame_height if frame_width and frame_height else 0
        total_box_area = 0.0
        quadrant_counts = [0, 0, 0, 0]
        grid_size = 4
        grid_counts = [[0 for _ in range(grid_size)] for _ in range(grid_size)]

        for box in boxes:
            if len(box) != 4:
                continue

            x1, y1, x2, y2 = [float(value) for value in box]
            width = max(0.0, x2 - x1)
            height = max(0.0, y2 - y1)
            total_box_area += width * height

            if frame_width and frame_height:
                center_x = (x1 + x2) / 2.0
                center_y = (y1 + y2) / 2.0
                quadrant = 0
                if center_x >= frame_width / 2.0:
                    quadrant += 1
                if center_y >= frame_height / 2.0:
                    quadrant += 2
                quadrant_counts[quadrant] += 1

                cell_x = min(grid_size - 1, max(0, int((center_x / frame_width) * grid_size)))
                cell_y = min(grid_size - 1, max(0, int((center_y / frame_height) * grid_size)))
                grid_counts[cell_y][cell_x] += 1

        density_index = 0.0
        if frame_area:
            density_index = (count / frame_area) * 1_000_000

        occupancy_ratio = 0.0
        if frame_area:
            occupancy_ratio = min(total_box_area / frame_area, 1.0)

        concentration_ratio = 0.0
        if count > 0 and any(quadrant_counts):
            concentration_ratio = max(quadrant_counts) / count

        occupied_cells = 0
        max_cell_count = 0
        for row in grid_counts:
            for cell_count in row:
                if cell_count > 0:
                    occupied_cells += 1
                if cell_count > max_cell_count:
                    max_cell_count = cell_count

        spatial_spread_ratio = occupied_cells / float(grid_size * grid_size) if count > 0 else 0.0
        spatial_cluster_ratio = max_cell_count / float(count) if count > 0 else 0.0

        return {
            "count": int(count),
            "frame_shape": list(frame_shape) if frame_shape is not None else None,
            "frame_area": frame_area,
            "boxes": boxes,
            "density_index": round(density_index, 2),
            "occupancy_ratio": round(occupancy_ratio, 3),
            "concentration_ratio": round(concentration_ratio, 3),
            "spatial_spread_ratio": round(spatial_spread_ratio, 3),
            "spatial_cluster_ratio": round(spatial_cluster_ratio, 3),
        }

    def get_average(self):
        """Get average count from history."""
        if not self.history:
            return 0
        return sum(self.history) / len(self.history)

    def get_recent_average(self, window_size=8):
        """Get a short rolling average for more stable crowd decisions."""
        if not self.history:
            return 0

        recent_history = list(self.history)[-window_size:]
        return sum(recent_history) / len(recent_history)

    def get_current_count(self):
        """Get the most recent count."""
        if not self.history:
            return 0
        return self.history[-1]

    def get_spike(self):
        """Calculate current spike (current - average)."""
        current = self.get_current_count()
        average = self.get_average()
        return current - average

    def _get_recent_growth(self, window_size=5):
        if len(self.history) < 2:
            return 0

        recent_history = list(self.history)[-window_size:]
        return recent_history[-1] - recent_history[0]

    def _get_signal_set(self, count, sample, recent_average, recent_growth):
        has_crowd_presence = count >= self.crowd_presence_threshold
        has_density_pressure = sample["density_index"] >= self.density_threshold or sample["occupancy_ratio"] >= self.occupancy_threshold
        has_concentration = count >= 4 and sample["spatial_cluster_ratio"] >= self.spatial_cluster_threshold
        has_compact_spread = sample["spatial_spread_ratio"] <= self.spatial_spread_threshold
        recent_jump = count - recent_average
        sudden_jump_threshold = max(3, self.spike_threshold // 2)
        has_surge = recent_jump >= sudden_jump_threshold or recent_growth >= sudden_jump_threshold
        has_sudden_formation = count >= self.crowd_presence_threshold and has_surge and has_compact_spread and (
            has_density_pressure or has_concentration
        )
        has_overcrowding = has_density_pressure and has_compact_spread and (
            count >= self.overcrowding_count_threshold or has_concentration
        )

        return {
            "has_crowd_presence": has_crowd_presence,
            "has_density_pressure": has_density_pressure,
            "has_concentration": has_concentration,
            "has_compact_spread": has_compact_spread,
            "has_sudden_formation": has_sudden_formation,
            "has_overcrowding": has_overcrowding,
        }

    def _get_current_sample(self):
        if not self.sample_history:
            return {
                "density_index": 0.0,
                "occupancy_ratio": 0.0,
                "concentration_ratio": 0.0,
                "spatial_spread_ratio": 0.0,
                "spatial_cluster_ratio": 0.0,
            }

        return self.sample_history[-1]

    def _calculate_risk_score(self, count, spike, recent_growth, sample, recent_average):
        score = 0
        signals = self._get_signal_set(count, sample, recent_average, recent_growth)

        if signals["has_crowd_presence"]:
            score += 5

        if signals["has_density_pressure"]:
            score += 10

        if signals["has_concentration"]:
            score += 8

        if signals["has_compact_spread"]:
            score += 8

        if signals["has_sudden_formation"]:
            score += 25

        if signals["has_overcrowding"]:
            score += 30

        if spike >= self.spike_threshold:
            score += 8

        if recent_growth >= self.spike_threshold:
            score += 8

        if count >= self.overcrowding_count_threshold * 2:
            score += 5

        # Dense but stable scenes should not become stampede risk by score alone.
        if signals["has_overcrowding"] and signals["has_sudden_formation"]:
            score += 10

        return min(score, 100)

    def _risk_level_from_score(self, score):
        if score >= 70:
            return "CRITICAL"
        if score >= 45:
            return "HIGH"
        if score >= 20:
            return "MODERATE"
        return "LOW"

    def _evaluate_state(self):
        count = self.get_current_count()
        average = round(self.get_average(), 2)
        spike = round(self.get_spike(), 2)
        sample = self._get_current_sample()
        recent_average = round(self.get_recent_average(), 2)
        recent_growth = self._get_recent_growth()
        signals = self._get_signal_set(count, sample, recent_average, recent_growth)
        baseline_ready = len(self.history) >= self.min_frames_for_analysis

        sudden_crowd_formation = baseline_ready and signals["has_sudden_formation"]

        overcrowded = baseline_ready and signals["has_overcrowding"]

        unusual_gathering = baseline_ready and signals["has_concentration"] and signals["has_density_pressure"]
        stampede_risk_score = self._calculate_risk_score(count, spike, recent_growth, sample, recent_average)
        risk_level = self._risk_level_from_score(stampede_risk_score)
        stampede_risk = baseline_ready and overcrowded and sudden_crowd_formation and risk_level in {"HIGH", "CRITICAL"}

        # Alert only on sudden crowd formation detection.
        risky_signal = sudden_crowd_formation
        if risky_signal:
            self.risky_frame_count += 1
        else:
            self.risky_frame_count = 0

        alert_triggered = self.risky_frame_count >= self.frames_for_alert and baseline_ready
        status = "ALERT" if alert_triggered else "NORMAL"

        current_status = {
            "count": count,
            "average": average,
            "recent_average": recent_average,
            "spike": spike,
            "history": list(self.history),
            "density_index": round(sample["density_index"], 2),
            "occupancy_ratio": round(sample["occupancy_ratio"], 3),
            "concentration_ratio": round(sample["concentration_ratio"], 3),
            "spatial_spread_ratio": round(sample["spatial_spread_ratio"], 3),
            "spatial_cluster_ratio": round(sample["spatial_cluster_ratio"], 3),
            "recent_growth": recent_growth,
            "sudden_crowd_formation": sudden_crowd_formation,
            "crowd_detected": sudden_crowd_formation,
            "overcrowded": overcrowded,
            "stampede_risk": stampede_risk,
            "stampede_risk_score": stampede_risk_score,
            "unusual_gathering": unusual_gathering,
            "risk_level": risk_level,
            "status": status,
            "alert_triggered": alert_triggered,
            "baseline_ready": baseline_ready,
        }

        self._log_state_changes(current_status)
        self.previous_state = {
            "sudden_crowd_formation": sudden_crowd_formation,
            "overcrowded": overcrowded,
            "unusual_gathering": unusual_gathering,
            "stampede_risk": stampede_risk,
            "risk_level": risk_level,
        }

        self.latest_status = current_status
        return current_status

    def _log_event(self, event_type, data):
        """Log an event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        self.event_log.append(event)

    def _log_state_changes(self, current_status):
        if current_status["sudden_crowd_formation"] and not self.previous_state["sudden_crowd_formation"]:
            self._log_event(
                "SUDDEN_CROWD_FORMATION",
                {
                    "count": current_status["count"],
                    "average": current_status["average"],
                    "spike": current_status["spike"],
                    "risk_level": current_status["risk_level"],
                },
            )

        if current_status["overcrowded"] and not self.previous_state["overcrowded"]:
            self._log_event(
                "OVERCROWDING",
                {
                    "count": current_status["count"],
                    "density_index": current_status["density_index"],
                    "occupancy_ratio": current_status["occupancy_ratio"],
                },
            )

        if current_status["unusual_gathering"] and not self.previous_state["unusual_gathering"]:
            self._log_event(
                "UNUSUAL_GATHERING",
                {
                    "count": current_status["count"],
                    "concentration_ratio": current_status["concentration_ratio"],
                },
            )

        if current_status["stampede_risk"] and not self.previous_state["stampede_risk"]:
            self._log_event(
                "STAMPEDE_RISK",
                {
                    "count": current_status["count"],
                    "risk_score": current_status["stampede_risk_score"],
                    "risk_level": current_status["risk_level"],
                },
            )

        risk_rank = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
        previous_rank = risk_rank.get(self.previous_state["risk_level"], 0)
        current_rank = risk_rank.get(current_status["risk_level"], 0)
        if current_rank > previous_rank and current_status["risk_level"] in {"HIGH", "CRITICAL"}:
            self._log_event(
                "RISK_ESCALATED",
                {
                    "count": current_status["count"],
                    "risk_level": current_status["risk_level"],
                    "risk_score": current_status["stampede_risk_score"],
                },
            )

        if current_status["alert_triggered"] and (
            self.last_alert_time is None
            or (datetime.now() - self.last_alert_time).total_seconds() > 5
        ):
            self.last_alert_time = datetime.now()
            self._log_event(
                "CROWD_ALERT",
                {
                    "count": current_status["count"],
                    "average": current_status["average"],
                    "spike": current_status["spike"],
                    "risk_level": current_status["risk_level"],
                },
            )

    def check_alert(self):
        """
        Check the latest analysis state.

        Returns:
            Tuple of (is_alert, status)
        """
        return self.latest_status["alert_triggered"], self.latest_status["status"]

    def get_event_log(self):
        """Get the event log as a list."""
        return list(self.event_log)

    def get_status(self):
        """Get the latest analysis status."""
        return dict(self.latest_status)
