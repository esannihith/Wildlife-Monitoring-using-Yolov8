import os
import requests
import logging
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration for weapon detection
WEAPON_API_KEY = os.getenv("WEAPON_API_KEY", "YourWeaponAPIKey")
WEAPON_MODEL_ID = os.getenv("WEAPON_MODEL_ID", "weapon-detection-model")
WEAPON_MODEL_VERSION = os.getenv("WEAPON_MODEL_VERSION", "1")
WEAPON_API_URL = os.getenv("WEAPON_API_URL", "https://detect.roboflow.com")

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Weapon class mapping
WEAPON_CLASS_MAP = {
    '1': 'gun',
    'rifle': 'rifle',
    'gun': 'gun',
    'knife': 'knife'
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

def run_weapon_inference(image_path, confidence, overlap):
    endpoint = f"{WEAPON_API_URL}/{WEAPON_MODEL_ID}/{WEAPON_MODEL_VERSION}"
    params = {
        "api_key": WEAPON_API_KEY,
        "confidence": confidence,
        "overlap": overlap
    }

    try:
        logger.info(f"Sending weapon detection request to {endpoint}")
        # Get the appropriate MIME type for the image
        mime_type = get_mime_type(image_path)
        logger.info(f"Detected MIME type: {mime_type} for file: {image_path}")
        
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, mime_type)}
            response = requests.post(endpoint, params=params, files=files, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # Map class IDs to proper names
        for pred in result.get('predictions', []):
            class_id = pred['class']
            if class_id in WEAPON_CLASS_MAP:
                pred['class'] = WEAPON_CLASS_MAP[class_id]
                
        return result
    except Exception as e:
        logger.error(f"Weapon detection request failed: {str(e)}")
        raise
