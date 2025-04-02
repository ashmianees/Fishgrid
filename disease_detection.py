import torch
import torchvision
from torchvision import transforms
from PIL import Image
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights
import numpy as np
from tensorflow.keras.applications.imagenet_utils import decode_predictions
import io

# Define the classes
CLASSES = [
    'Bacterial diseases - Aeromoniasis',
    'Bacterial gill disease',
    'Bacterial Red disease',
    'Fungal diseases Saprolegniasis',
    'Healthy Fish',
    'Parasitic diseases',
    'Viral diseases White tail disease'
]

# Define the ImageNet fish-related class indices more strictly
FISH_CLASS_INDICES = {
    389: 'barracouta',
    390: 'eel',
    391: 'coho salmon',
    392: 'rock beauty',
    393: 'anemone fish',
    394: 'sturgeon',
    395: 'gar',
    396: 'lionfish',
    397: 'puffer',
    398: 'angelfish',
    399: 'electric ray',
    400: 'stingray',
}

# Initialize FastAPI
app = FastAPI()

# Enhanced image preprocessing with data augmentation
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),  # Add color augmentation
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Fish detection model (using pre-trained ResNet50)
fish_detection_model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
fish_detection_model.eval()

def is_fish_image(image, confidence_threshold=0.6):
    """
    Strictly validate if the uploaded image contains a fish
    Returns: (bool, str) - (is_fish, message)
    """
    try:
        # Load the pre-trained model
        model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        model.eval()

        # Preprocess the image
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        input_tensor = preprocess(image).unsqueeze(0)
        
        with torch.no_grad():
            output = model(input_tensor)
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
        
        # Get the highest probability and its index
        max_prob, predicted_idx = torch.max(probabilities, 0)
        predicted_idx = predicted_idx.item()
        
        # Check if the predicted class is in our fish classes and has high confidence
        if predicted_idx in FISH_CLASS_INDICES and max_prob.item() > confidence_threshold:
            return True, "Valid fish image detected"
        else:
            # Check if any fish class has high probability
            fish_probs = {idx: probabilities[idx].item() for idx in FISH_CLASS_INDICES.keys()}
            max_fish_prob = max(fish_probs.values())
            
            if max_fish_prob > confidence_threshold:
                return True, "Valid fish image detected"
            else:
                return False, "The image does not appear to be a clear picture of a fish. Please upload a clear fish image."
                
    except Exception as e:
        return False, f"Error processing image: {str(e)}"

class EnhancedDiseaseDetectionModel(nn.Module):
    def __init__(self, num_classes=7):
        super().__init__()
        # Use a pre-trained ResNet50 with latest weights
        self.base_model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        
        # Add additional layers for better feature extraction
        self.features = nn.Sequential(
            *list(self.base_model.children())[:-2],
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Dropout(0.5)  # Add dropout for regularization
        )
        
        # Add a custom classifier
        self.classifier = nn.Sequential(
            nn.Linear(2048, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)

# Initialize the enhanced model
model = EnhancedDiseaseDetectionModel()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <body>
            <h1>Fish Disease Detection</h1>
            <form action="/predict" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept="image/*">
                <input type="submit">
            </form>
        </body>
    </html>
    """

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Read the image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert image to RGB if it's not
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Strictly validate if it's a fish image
        is_valid_fish, message = is_fish_image(image)
        
        if not is_valid_fish:
            return {
                "error": message,
                "status": "error"
            }
        
        # Continue with disease detection only if it's a valid fish image
        # Preprocess the image with augmentation
        image_tensor = transform(image).unsqueeze(0)
        
        # Get predictions
        model.eval()
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            
        # Get top prediction
        _, predicted = torch.max(outputs, 1)
        disease = CLASSES[predicted.item()]
        confidence = probabilities[predicted.item()].item() * 100
        
        # Determine if the fish is healthy
        is_healthy = disease == 'Healthy Fish'
        status_message = "Healthy fish detected" if is_healthy else "Disease detected"
        
        # Add confidence threshold
        if confidence < 50:  # You can adjust this threshold
            return {
                "warning": "Low confidence detection. Please upload a clearer image of the fish.",
                "disease": disease,
                "confidence": f"{confidence:.2f}%",
                "status": "warning",
                "is_healthy": is_healthy,
                "status_message": status_message
            }
        
        return {
            "disease": disease,
            "confidence": f"{confidence:.2f}%",
            "all_probabilities": {
                class_name: f"{prob.item()*100:.2f}%" 
                for class_name, prob in zip(CLASSES, probabilities)
            },
            "status": "success",
            "is_healthy": is_healthy,
            "status_message": status_message
        }
        
    except Exception as e:
        return {
            "error": f"Error processing image: {str(e)}",
            "status": "error"
        }
