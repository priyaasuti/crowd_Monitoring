"""
Weapon detection module using LSTM + MobileNetV2 feature extraction
GPU acceleration enabled - uses same device as other models
"""
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from PIL import Image
import torchvision.transforms as transforms
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2
import cv2


class LSTMWeaponModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(1280, 256, batch_first=True)
        self.fc = nn.Linear(256, 2)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out)


class WeaponDetector:
    """
    Weapon detection using pre-trained LSTM model
    GPU acceleration: Automatic via torch device detection
    """
    
    def __init__(self, model_path=None, confidence_threshold=0.5):
        """
        Initialize weapon detector
        
        Args:
            model_path: Path to trained LSTM model (violence_model.pth)
            confidence_threshold: Detection confidence threshold (0.0-1.0)
        """
        self.model_path = model_path or Path(__file__).resolve().parent / "models" / "violence_model.pth"
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_extractor = None
        self.transform = None
        
        print(f"WeaponDetector initialized on device: {self.device}", flush=True)
        print(f"Confidence threshold: {confidence_threshold}", flush=True)
    
    def _load_model(self):
        """Lazy load weapon detection model"""
        if self.model is None:
            print(f"Loading weapon detection model from {self.model_path}...", flush=True)
            
            self.model = LSTMWeaponModel().to(self.device)
            self.model.load_state_dict(
                torch.load(self.model_path, map_location=self.device, weights_only=False)
            )
            self.model.eval()
            print("✅ Weapon detection model loaded successfully", flush=True)
    
    def _load_feature_extractor(self):
        """Lazy load MobileNetV2 feature extractor"""
        if self.feature_extractor is None:
            print("Loading feature extractor (MobileNetV2)...", flush=True)
            
            feature_extractor = mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
            feature_extractor.classifier = nn.Identity()
            self.feature_extractor = feature_extractor.to(self.device)
            self.feature_extractor.eval()
            
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])
            print("✅ Feature extractor loaded", flush=True)
    
    def extract_features_from_frame(self, frame):
        """
        Extract features from a single frame using MobileNetV2
        
        Args:
            frame: Input video frame (numpy array BGR)
        
        Returns:
            Feature vector (1280-dim numpy array)
        """
        self._load_feature_extractor()
        
        # Convert BGR to RGB and to PIL Image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        # Transform and move to device
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            features = self.feature_extractor(tensor)
        
        return features.detach().cpu().numpy()[0]
    
    def detect_weapon_in_sequence(self, frame_sequence):
        """
        Detect weapons in a sequence of frames
        
        Args:
            frame_sequence: List of frames or list of feature vectors (20 frames expected)
        
        Returns:
            Dictionary with:
            - detected: Boolean indicating weapon detection
            - confidence: Confidence score (0.0-1.0)
            - threat_level: 'LOW', 'MEDIUM', 'HIGH'
        """
        self._load_model()
        self._load_feature_extractor()
        
        if len(frame_sequence) < 20:
            # Pad sequence to 20 frames
            pad_count = 20 - len(frame_sequence)
            if isinstance(frame_sequence[0], np.ndarray) and len(frame_sequence[0].shape) == 1:
                # Already features
                padding = np.repeat(frame_sequence[-1][np.newaxis, :], pad_count, axis=0)
                features_array = np.concatenate([np.array(frame_sequence), padding], axis=0)
            else:
                # Raw frames - extract features first
                features_list = []
                for frame in frame_sequence:
                    features_list.append(self.extract_features_from_frame(frame))
                padding = np.repeat(features_list[-1][np.newaxis, :], pad_count, axis=0)
                features_array = np.concatenate([np.array(features_list), padding], axis=0)
        else:
            if isinstance(frame_sequence[0], np.ndarray) and len(frame_sequence[0].shape) == 1:
                features_array = np.array(frame_sequence[:20])
            else:
                features_list = []
                for frame in frame_sequence[:20]:
                    features_list.append(self.extract_features_from_frame(frame))
                features_array = np.array(features_list)
        
        # Run model inference
        input_tensor = torch.tensor([features_array], dtype=torch.float32, device=self.device)
        
        with torch.no_grad():
            output = self.model(input_tensor)
            probabilities = torch.softmax(output, dim=1)
        
        confidence = float(probabilities[0][1].item())
        detected = confidence >= self.confidence_threshold
        
        # Determine threat level
        if confidence < 0.3:
            threat_level = "LOW"
        elif confidence < 0.7:
            threat_level = "MEDIUM"
        else:
            threat_level = "HIGH"
        
        return {
            "detected": detected,
            "confidence": confidence,
            "threat_level": threat_level,
            "threshold": self.confidence_threshold,
        }
    
    def detect_weapon_in_frame(self, frame):
        """
        Quick single-frame weapon detection (less reliable than sequence-based)
        
        Args:
            frame: Input video frame
        
        Returns:
            Dictionary with detection info
        """
        features = self.extract_features_from_frame(frame)
        # Create single-frame sequence by repeating
        single_sequence = [features] * 20
        return self.detect_weapon_in_sequence(single_sequence)
