"""
Aggressor Detector module.
Identifies the aggressor among tracked individuals by analyzing velocity magnitudes, 
approaching speeds, and relative motion directions.
"""
import numpy as np

def find_aggressor(tracked_objects, speed_threshold=8.0, distance_threshold=250.0):
    """
    Identify the aggressor among tracked individuals.
    
    Args:
        tracked_objects: List of tracked objects from Tracker.track().
                         Each object is: {"id": ID, "box": [x1, y1, x2, y2], "velocity": (vx, vy), "history": [(cx, cy), ...]}
        speed_threshold: Velocity magnitude threshold for fast action.
        distance_threshold: Bounding distance below which interaction is considered close.
        
    Returns:
        The integer ID of the identified aggressor, or None if no aggressor is identified.
    """
    if len(tracked_objects) < 2:
        return None

    aggressor_scores = {}  # ID -> Score

    # Compare all pairs of active tracks
    for i in range(len(tracked_objects)):
        for j in range(i + 1, len(tracked_objects)):
            obj1 = tracked_objects[i]
            obj2 = tracked_objects[j]
            
            id1, id2 = obj1["id"], obj2["id"]
            hist1, hist2 = obj1["history"], obj2["history"]
            
            # Extract velocities
            v1_x, v1_y = obj1["velocity"]
            v2_x, v2_y = obj2["velocity"]
            
            speed1 = (v1_x**2 + v1_y**2)**0.5
            speed2 = (v2_x**2 + v2_y**2)**0.5
            
            if len(hist1) < 2 or len(hist2) < 2:
                # If short history, fallback to general velocity magnitude
                if max(speed1, speed2) > speed_threshold:
                    agg_id = id1 if speed1 > speed2 else id2
                    aggressor_scores[agg_id] = aggressor_scores.get(agg_id, 0) + 1
                continue
            
            # Current centroids
            c1 = np.array(hist1[-1])
            c2 = np.array(hist2[-1])
            
            # Previous centroids
            p1 = np.array(hist1[-2])
            p2 = np.array(hist2[-2])
            
            # Distance
            d_curr = np.linalg.norm(c1 - c2)
            d_prev = np.linalg.norm(p1 - p2)
            delta_d = d_curr - d_prev
            
            # Direction vector pointing from obj1 to obj2
            v_12 = c2 - c1
            dist_12 = np.linalg.norm(v_12)
            if dist_12 < 1e-5:
                continue
            u_12 = v_12 / dist_12
            
            # Velocity vectors
            vel1 = c1 - p1
            vel2 = c2 - p2
            
            # Projection of velocity vectors onto line connecting them
            # proj1 > 0 means obj1 is moving towards obj2
            # proj2 > 0 means obj2 is moving towards obj1
            proj1 = np.dot(vel1, u_12)
            proj2 = np.dot(vel2, -u_12)
            
            # Logic: If distance between ID1 and ID2 suddenly decreases
            if delta_d < -4.0:
                # Approaching rapidly: who is moving faster towards the other?
                if proj1 > proj2 and proj1 > speed_threshold:
                    aggressor_scores[id1] = aggressor_scores.get(id1, 0) + 3
                elif proj2 > proj1 and proj2 > speed_threshold:
                    aggressor_scores[id2] = aggressor_scores.get(id2, 0) + 3
                else:
                    # General speed fallback
                    if speed1 > speed2 and speed1 > speed_threshold:
                        aggressor_scores[id1] = aggressor_scores.get(id1, 0) + 2
                    elif speed2 > speed1 and speed2 > speed_threshold:
                        aggressor_scores[id2] = aggressor_scores.get(id2, 0) + 2
            
            # Logic: If close and speed is very high towards the other
            elif d_curr < distance_threshold:
                if proj1 > speed_threshold * 1.5 and proj1 > proj2:
                    aggressor_scores[id1] = aggressor_scores.get(id1, 0) + 2
                elif proj2 > speed_threshold * 1.5 and proj2 > proj1:
                    aggressor_scores[id2] = aggressor_scores.get(id2, 0) + 2

    if not aggressor_scores:
        # Default fallback to fastest moving person in scene
        speeds = []
        for obj in tracked_objects:
            vx, vy = obj["velocity"]
            s = (vx**2 + vy**2)**0.5
            speeds.append((obj["id"], s))
        speeds.sort(key=lambda x: x[1], reverse=True)
        if speeds and speeds[0][1] > speed_threshold:
            return speeds[0][0]
        return None

    # Get track ID with the maximum aggressor score
    best_aggressor = max(aggressor_scores, key=aggressor_scores.get)
    return best_aggressor
