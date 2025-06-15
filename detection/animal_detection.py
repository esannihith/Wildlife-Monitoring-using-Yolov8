import os
import requests
import logging
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration for animal detection
ANIMAL_API_KEY = os.getenv("API_KEY", "GNuSepxkQmr920eHECFx")
ANIMAL_MODEL_ID = os.getenv("MODEL_ID", "animal-detection-kq9h0")
ANIMAL_MODEL_VERSION = os.getenv("MODEL_VERSION", "4")
ANIMAL_API_URL = os.getenv("ROBOFLOW_API_URL", "https://detect.roboflow.com")

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Animal class mapping
ANIMAL_CLASS_MAP = {
    '0': 'tiger',
    'bear': 'bear',
    'elephant': 'elephant',
    'giraffe': 'giraffe',
    'human': 'human',
    'zebra': 'zebra',
    'horse': 'horse'
}

def get_mime_type(file_path):
    """
    Determine the MIME type of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string (e.g., 'image/jpeg', 'image/png')
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('image/'):
        return mime_type
    
    # Default to jpeg if we can't determine the type
    ext = Path(file_path).suffix.lower()
    if ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext == '.png':
        return 'image/png'
    elif ext == '.webp':
        return 'image/webp'
    elif ext == '.gif':
        return 'image/gif'
    else:
        # Default fallback
        return 'image/jpeg'

def run_animal_inference(image_path, confidence, overlap):
    """
    Run inference for animal detection using the Roboflow API.
    
    Args:
        image_path: Path to the image file
        confidence: Confidence threshold (0-1)
        overlap: Overlap threshold (0-1)
    
    Returns:
        JSON response from the API with detection results
    """
    endpoint = f"{ANIMAL_API_URL}/{ANIMAL_MODEL_ID}/{ANIMAL_MODEL_VERSION}"
    params = {
        "api_key": ANIMAL_API_KEY,
        "confidence": confidence,
        "overlap": overlap
    }

    try:
        logger.info(f"Sending animal detection request to {endpoint}")
        # Get the appropriate MIME type for the image
        mime_type = get_mime_type(image_path)
        logger.info(f"Detected MIME type: {mime_type} for file: {image_path}")
        
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, mime_type)}
            response = requests.post(endpoint, params=params, files=files, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # Map class IDs to proper names using the defined mapping
        for pred in result.get('predictions', []):
            class_id = pred['class']
            if class_id in ANIMAL_CLASS_MAP:
                pred['class'] = ANIMAL_CLASS_MAP[class_id]
        
        return result
    except Exception as e:
        logger.error(f"Animal detection request failed: {str(e)}")
        raise
