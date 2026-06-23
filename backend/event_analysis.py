"""
Event analysis pipeline for accident and violence video detection.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import List, Sequence

import base64
import io
import os
import requests

# Load .env file to get API keys - must be before accessing os.getenv()
from dotenv import load_dotenv
env_file = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_file), override=True)

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
from torch import Tensor
from transformers import pipeline
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2

FRAME_SAMPLE_FPS = 8
SEQUENCE_LENGTH = 20
STEP_SIZE = 5
ACCIDENT_THRESHOLD = 0.5
VIOLENCE_THRESHOLD = 0.6
WEAPON_THRESHOLD = 0.6
MIN_POSITIVE_VOTES = 2

DEFAULT_SYSTEM_LOCATION = "Local monitoring workstation"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Google AI Studio API key from .env
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
GOOGLE_MODEL = "gemini-flash-latest"  # Google's fastest model

# Debug: Print Google API status on startup
print(f"[EVENT_ANALYSIS] Google API Key loaded: {bool(GOOGLE_API_KEY)}", flush=True)
if GOOGLE_API_KEY:
    print(f"[EVENT_ANALYSIS] API Key preview: {GOOGLE_API_KEY[:30]}...", flush=True)


def get_google_client():
    """Verify Google API configuration is available"""
    if not GOOGLE_API_KEY:
        print("[GEMINI] API key not found! Check .env file has: GOOGLE_API_KEY=...", flush=True)
        return False
    print("[GEMINI] Google Gemini API ready", flush=True)
    return True



class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(1280, 256, batch_first=True)
        self.fc = nn.Linear(256, 2)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out)


@dataclass
class SequencePrediction:
    sequence_index: int
    start_frame: int
    end_frame: int
    start_seconds: float
    end_seconds: float
    midpoint_seconds: float
    confidence: float
    detected: bool


@lru_cache(maxsize=1)
def get_feature_extractor():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
    model.classifier = nn.Identity()
    model = model.to(device)
    model.eval()

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    return model, transform, device


@lru_cache(maxsize=1)
def get_event_models():
    _, _, device = get_feature_extractor()

    model_root = Path(__file__).resolve().parent / "models"
    violence_path = model_root / "violence_model.pth"
    accident_path = model_root / "accident_model_run1.pth"

    violence_model = LSTMModel().to(device)
    accident_model = LSTMModel().to(device)

    violence_model.load_state_dict(torch.load(violence_path, map_location=device, weights_only=False))
    accident_model.load_state_dict(torch.load(accident_path, map_location=device, weights_only=False))

    violence_model.eval()
    accident_model.eval()

    return {
        "device": device,
        "violence_model": violence_model,
        "accident_model": accident_model,
    }


def _sample_frames(video_path: str, target_fps: int = FRAME_SAMPLE_FPS):
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError(f"Cannot open video source: {video_path}")

    source_fps = capture.get(cv2.CAP_PROP_FPS) or 0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if source_fps <= 0:
        source_fps = target_fps

    frame_interval = max(int(round(source_fps / target_fps)), 1)
    sampled_frames = []
    sampled_frame_indices = []
    raw_frames_read = 0

    while True:
        success, frame = capture.read()
        if not success:
            break

        if raw_frames_read % frame_interval == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            sampled_frames.append(Image.fromarray(rgb_frame))
            sampled_frame_indices.append(raw_frames_read)

        raw_frames_read += 1

    capture.release()

    if not sampled_frames:
        raise ValueError("No frames could be extracted from the uploaded video")

    duration_seconds = 0.0
    if source_fps > 0 and frame_count > 0:
        duration_seconds = frame_count / source_fps
    elif sampled_frame_indices:
        duration_seconds = sampled_frame_indices[-1] / float(target_fps)

    return sampled_frames, sampled_frame_indices, source_fps, duration_seconds, frame_count


def _extract_features(frames: Sequence[Image.Image]):
    feature_extractor, transform, device = get_feature_extractor()
    feature_batches = []

    batch_size = 16
    for start_index in range(0, len(frames), batch_size):
        batch_frames = frames[start_index : start_index + batch_size]
        tensors = [transform(frame) for frame in batch_frames]
        batch_tensor = torch.stack(tensors).to(device)

        with torch.no_grad():
            batch_features = feature_extractor(batch_tensor)

        feature_batches.append(batch_features.detach().cpu())

    return torch.cat(feature_batches, dim=0).numpy()


def _build_sequences(features: np.ndarray, sampled_frame_indices: Sequence[int], source_fps: float):
    sequence_features = []
    sequence_metadata = []

    frame_count = len(features)
    if frame_count < SEQUENCE_LENGTH:
        pad_count = SEQUENCE_LENGTH - frame_count
        padding = np.repeat(features[-1][None, :], pad_count, axis=0)
        features = np.concatenate([features, padding], axis=0)
        sampled_frame_indices = list(sampled_frame_indices) + [sampled_frame_indices[-1]] * pad_count
        frame_count = len(features)

    for sequence_index, start_index in enumerate(range(0, frame_count - SEQUENCE_LENGTH + 1, STEP_SIZE)):
        end_index = start_index + SEQUENCE_LENGTH
        sequence_features.append(features[start_index:end_index])

        start_frame = sampled_frame_indices[start_index]
        end_frame = sampled_frame_indices[end_index - 1]
        start_seconds = start_frame / float(source_fps)
        end_seconds = end_frame / float(source_fps)
        midpoint_seconds = (start_seconds + end_seconds) / 2.0

        sequence_metadata.append(
            {
                "sequence_index": sequence_index,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "midpoint_seconds": midpoint_seconds,
            }
        )

    return sequence_features, sequence_metadata


def _score_model(model: nn.Module, sequences: Sequence[np.ndarray], metadata: Sequence[dict], threshold: float):
    if not sequences:
        return []

    device = next(model.parameters()).device
    predictions: List[SequencePrediction] = []

    for sequence_index, sequence in enumerate(sequences):
        input_tensor = torch.tensor([sequence], dtype=torch.float32, device=device)
        with torch.no_grad():
            output = model(input_tensor)
            probabilities = torch.softmax(output, dim=1)

        confidence = float(probabilities[0][1].item())
        sequence_info = metadata[sequence_index]
        predictions.append(
            SequencePrediction(
                sequence_index=sequence_index,
                start_frame=sequence_info["start_frame"],
                end_frame=sequence_info["end_frame"],
                start_seconds=sequence_info["start_seconds"],
                end_seconds=sequence_info["end_seconds"],
                midpoint_seconds=sequence_info["midpoint_seconds"],
                confidence=confidence,
                detected=confidence >= threshold,
            )
        )

    return predictions


def _format_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _summarize_model_predictions(predictions: Sequence[SequencePrediction], threshold: float, fallback_label: str):
    if not predictions:
        return {
            "detected": False,
            "confidence": 0.0,
            "timestamp": None,
            "timestamp_seconds": None,
            "votes": 0,
            "best_sequence": None,
            "label": fallback_label,
        }

    positive_predictions = [prediction for prediction in predictions if prediction.detected]
    best_prediction = max(predictions, key=lambda prediction: prediction.confidence)
    best_positive_prediction = max(positive_predictions, key=lambda prediction: prediction.confidence) if positive_predictions else None

    selected_prediction = best_positive_prediction or best_prediction
    votes = len(positive_predictions)

    return {
        "detected": votes >= MIN_POSITIVE_VOTES if fallback_label == "accident" else votes > 0,
        "confidence": round(selected_prediction.confidence, 4),
        "timestamp": _format_timestamp(selected_prediction.midpoint_seconds),
        "timestamp_seconds": round(selected_prediction.midpoint_seconds, 2),
        "votes": votes,
        "best_sequence": {
            "sequence_index": selected_prediction.sequence_index,
            "start_frame": selected_prediction.start_frame,
            "end_frame": selected_prediction.end_frame,
            "start_seconds": round(selected_prediction.start_seconds, 2),
            "end_seconds": round(selected_prediction.end_seconds, 2),
        },
        "label": fallback_label,
    }


def generate_scene_description(
    image: Image.Image,
    incident_type: str,
) -> str:
    """Generate scene description using Google Gemini API"""
    
    if not get_google_client():
        return f"Incident Type: {incident_type}. Scene description unavailable (API not configured)."
    
    try:
        # Create detailed prompt - simple and clear
        prompt = f"""INCIDENT ALERT: {incident_type.upper()} DETECTED

Describe the scene in simple, clear language that anyone can understand:

WHERE - What type of location is this? (street, store, office, etc.)
WHO - How many people are there? Where are they?
WHAT - What are they doing? What's happening?
DANGER - What is dangerous or concerning about this?
DETAILS - Lighting? Crowded? Any exits visible?
ACTION - Is this Low/Medium/High risk? What should security do?

Keep it SHORT and SIMPLE - 1-2 sentences each. No technical jargon."""
        
        # Call Google Gemini API with correct format
        url = f"{GOOGLE_API_URL}?key={GOOGLE_API_KEY}"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ]
        }
        
        print(f"[GEMINI] Requesting scene description for {incident_type}...", flush=True)
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Debug: Print response for errors
        if response.status_code != 200:
            print(f"[GEMINI] Status: {response.status_code}", flush=True)
            print(f"[GEMINI] Response: {response.text[:300]}", flush=True)
        
        response.raise_for_status()
        
        result = response.json()
        
        # Extract text from Google Gemini response
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                if len(candidate["content"]["parts"]) > 0:
                    description = candidate["content"]["parts"][0].get("text", "").strip()
                    if description:
                        print("[GEMINI] Scene description generated successfully", flush=True)
                        return description
        
        print(f"[GEMINI] Response format: {list(result.keys())}", flush=True)
        return f"Scene analysis for {incident_type} incident completed."
            
    except requests.exceptions.Timeout:
        print("[GEMINI] API request timed out (>30s)", flush=True)
        return f"Scene description generation timed out."
    except requests.exceptions.HTTPError as e:
        error_msg = str(e)
        print(f"[GEMINI] HTTP Error: {error_msg[:150]}", flush=True)
        try:
            error_detail = response.text
            print(f"[GEMINI] Error detail: {error_detail[:200]}", flush=True)
        except:
            pass
        return f"Scene description error for {incident_type}: API error"
    except requests.exceptions.RequestException as e:
        print(f"[GEMINI] Request failed: {str(e)[:150]}", flush=True)
        return f"Failed to generate description: connection error"
    except Exception as e:
        print(f"[GEMINI] Unexpected error: {str(e)[:150]}", flush=True)
        return f"Scene description unavailable: {str(e)[:60]}"


def _image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _analyze_event_video_core(video_path: str, system_location: str | None = None):
    resolved_location = system_location or DEFAULT_SYSTEM_LOCATION
    models = get_event_models()
    violence_model = models["violence_model"]
    accident_model = models["accident_model"]

    frames, sampled_frame_indices, source_fps, duration_seconds, total_frame_count = _sample_frames(video_path)
    features = _extract_features(frames)
    sequences, sequence_metadata = _build_sequences(features, sampled_frame_indices, source_fps)

    if not sequences:
        raise ValueError("Not enough frames were available to build analysis sequences")

    with ThreadPoolExecutor(max_workers=2) as executor:
        violence_future = executor.submit(_score_model, violence_model, sequences, sequence_metadata, VIOLENCE_THRESHOLD)
        accident_future = executor.submit(_score_model, accident_model, sequences, sequence_metadata, ACCIDENT_THRESHOLD)
        violence_predictions = violence_future.result()
        accident_predictions = accident_future.result()

    violence_summary = _summarize_model_predictions(violence_predictions, VIOLENCE_THRESHOLD, "violence")
    accident_summary = _summarize_model_predictions(accident_predictions, ACCIDENT_THRESHOLD, "accident")

    overall_candidates = [
        ("violence", violence_summary),
        ("accident", accident_summary),
    ]
    positive_candidates = [candidate for candidate in overall_candidates if candidate[1]["detected"]]

    if positive_candidates:
        incident_type, incident_summary = max(positive_candidates, key=lambda candidate: candidate[1]["confidence"])
        overall_incident = incident_type.capitalize()
        overall_confidence = incident_summary["confidence"]
        overall_timestamp = incident_summary["timestamp"]
        selected_sequence = incident_summary["best_sequence"]
        sequence_start = selected_sequence["sequence_index"] * STEP_SIZE
        frame_index = min(sequence_start + SEQUENCE_LENGTH // 2, len(frames) - 1)
        scene_frame_image = frames[frame_index]
        scene_frame_base64 = _image_to_base64(scene_frame_image)
        scene_description = None
    else:
        overall_incident = "No Incident"
        overall_confidence = max(violence_summary["confidence"], accident_summary["confidence"])
        overall_timestamp = violence_summary["timestamp"] or accident_summary["timestamp"]
        scene_description = None
        scene_frame_base64 = None
        scene_frame_image = None

    analysis_timestamp = datetime.now().isoformat(timespec="seconds")

    return {
        "scene_description": scene_description,
        "scene_frame": scene_frame_base64,
        "message": "Event analysis completed successfully",
        "analysis_timestamp": analysis_timestamp,
        "video": {
            "path": video_path,
            "source": "uploaded video",
            "camera_captured": False,
            "system_location": resolved_location,
            "video_capture_note": "Analyzed from uploaded footage using a local monitoring workstation.",
            "source_fps": round(source_fps, 2),
            "frame_count": total_frame_count,
            "duration_seconds": round(duration_seconds, 2),
            "sampled_frames": len(frames),
            "sequence_length": SEQUENCE_LENGTH,
            "step_size": STEP_SIZE,
        },
        "incident_type": overall_incident,
        "confidence_score": round(overall_confidence, 4),
        "timestamp": overall_timestamp,
        "location": resolved_location,
        "models": {
            "violence": {
                **violence_summary,
                "threshold": VIOLENCE_THRESHOLD,
            },
            "accident": {
                **accident_summary,
                "threshold": ACCIDENT_THRESHOLD,
            },
        },
        "summary": {
            "violence_detected": violence_summary["detected"],
            "accident_detected": accident_summary["detected"],
            "feature_extraction": "Shared MobileNetV2 features reused for all models (GPU-accelerated).",
            "parallel_inference": True,
        },
    }


def analyze_event_video(video_path: str, system_location: str | None = None):
    analysis_result = _analyze_event_video_core(video_path, system_location=system_location)

    if analysis_result.get("scene_frame") and analysis_result.get("incident_type") != "No Incident":
        try:
            image_data = base64.b64decode(analysis_result["scene_frame"])
            scene_image = Image.open(io.BytesIO(image_data)).convert("RGB")
            analysis_result["scene_description"] = generate_scene_description(
                scene_image,
                analysis_result["incident_type"],
            )
        except Exception as e:
            analysis_result["scene_description"] = f"Scene description unavailable: {e}"

    return analysis_result
