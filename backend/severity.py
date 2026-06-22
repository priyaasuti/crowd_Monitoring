"""
Severity Module.
Calculates a 0-100 severity risk score for violent incidents based on:
1. People Count (max 35)
2. Motion Intensity / Speed (max 35)
3. Incident Duration (max 30)
"""

def calculate_severity(tracked_objects, violence_duration_frames, fps=8):
    """
    Calculate overall violence severity score (0 to 100).
    
    Args:
        tracked_objects: List of tracked objects in the conflict.
        violence_duration_frames: Number of consecutive frames violence has been active.
        fps: FPS at which video frames are analyzed (default is 8).
        
    Returns:
        A dictionary with "score" (0-100), "risk_level" (Low/Medium/High Risk), and a breakdown of scores.
    """
    # 1. People count score (max 35)
    people_count = len(tracked_objects)
    # 5 points per person, capped at 35 (7 people)
    people_count_score = min(35, people_count * 5)
    
    # 2. Motion score (max 35)
    # Average speed (velocity magnitude) across all tracked people
    speeds = []
    for obj in tracked_objects:
        vx, vy = obj["velocity"]
        speed = (vx**2 + vy**2)**0.5
        speeds.append(speed)
        
    avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
    # Map average velocity to a score: 1.5 points per px/frame, capped at 35 (approx 23 px/frame speed)
    motion_score = min(35, avg_speed * 1.5)
    
    # 3. Duration score (max 30)
    # Duration in seconds of the ongoing violent sequence
    duration_seconds = violence_duration_frames / float(fps)
    # 5 points per second of sustained conflict, capped at 30 (6 seconds)
    duration_score = min(30, duration_seconds * 5.0)
    
    # Calculate sum
    severity_score = int(round(people_count_score + motion_score + duration_score))
    severity_score = min(100, max(0, severity_score))
    
    # Map to Risk Level
    if severity_score >= 70:
        risk_level = "High Risk"
    elif severity_score >= 35:
        risk_level = "Medium Risk"
    else:
        risk_level = "Low Risk"
        
    return {
        "score": severity_score,
        "risk_level": risk_level,
        "details": {
            "people_count_score": round(people_count_score, 2),
            "motion_score": round(motion_score, 2),
            "duration_score": round(duration_score, 2),
            "people_count": people_count,
            "avg_speed": round(avg_speed, 2),
            "duration_seconds": round(duration_seconds, 2)
        }
    }
