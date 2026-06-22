"""
Violence Detector module.
Loads the pre-trained violence LSTM model and runs inference on feature sequences.
"""
import torch
import torch.nn as nn
from pathlib import Path

class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(1280, 256, batch_first=True)
        self.fc = nn.Linear(256, 2)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out)


class ViolenceDetector:
    def __init__(self, model_path=None):
        """
        Initialize Violence Detector, loading the pre-trained LSTM model weights.
        """
        if model_path is None:
            model_path = Path(__file__).resolve().parent / "models" / "violence_model.pth"
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = LSTMModel().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        self.threshold = 0.6  # Default threshold for violence detection

    def predict(self, sequence_features):
        """
        Run inference on sequence features (shape: 20x1280)
        
        Args:
            sequence_features: NumPy array or PyTorch tensor of shape (20, 1280)
            
        Returns:
            is_violence: True if violence is detected, False otherwise
            confidence: Float probability of violence
        """
        input_tensor = torch.tensor([sequence_features], dtype=torch.float32, device=self.device)
        with torch.no_grad():
            output = self.model(input_tensor)
            probabilities = torch.softmax(output, dim=1)
            
        confidence = float(probabilities[0][1].item())
        is_violence = confidence >= self.threshold
        return is_violence, confidence
