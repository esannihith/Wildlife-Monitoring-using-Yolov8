import os
import logging
import cv2
import numpy as np
import sys
from pathlib import Path

# Setup logging with more details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to the PPE model - search in multiple locations
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPE_MODEL_PATHS = [
    os.path.join(SCRIPT_DIR, "models", "ppe.pt"),          # In a models subdirectory
    os.path.join(SCRIPT_DIR, "ppe.pt"),                    # In the root directory
    os.path.join(SCRIPT_DIR, "weights", "ppe.pt"),         # In a weights subdirectory
    os.path.join(SCRIPT_DIR, "static", "models", "ppe.pt") # In a static/models subdirectory
]

# PPE class mapping
PPE_CLASS_MAP = {
    'boots': 'boots',
    'gloves': 'gloves',
    'helmet': 'helmet',
    'person': 'person',
    'vest': 'vest'
}

# Load the model once when module is imported
ppe_model = None
model_loaded_properly = False

def find_ppe_model():
    """Search for the PPE model in various directories"""
    for model_path in PPE_MODEL_PATHS:
        if os.path.exists(model_path):
            logger.info(f"Found PPE model at: {model_path}")
            return model_path
    
    # If we didn't find it in predefined locations, do a broader search
    logger.warning("PPE model not found in expected locations, searching directory tree...")
    for root, dirs, files in os.walk(SCRIPT_DIR):
        if "ppe.pt" in files:
            model_path = os.path.join(root, "ppe.pt")
            logger.info(f"Found PPE model at: {model_path}")
            return model_path
    
    return None

def load_ppe_model():
    """Load the PPE YOLOv8 model"""
    global ppe_model, model_loaded_properly
    
    if model_loaded_properly and ppe_model is not None:
        return True
    
    # Find the model file
    model_path = find_ppe_model()
    if not model_path:
        logger.error("PPE model file 'ppe.pt' not found in any location.")
        return False
    
    try:
        # Try to import ultralytics for YOLOv8
        from ultralytics import YOLO
        logger.info(f"Loading YOLOv8 model from {model_path}")
        ppe_model = YOLO(model_path)
        logger.info(f"PPE model loaded successfully using YOLOv8")
        model_loaded_properly = True
        return True
    except ImportError:
        logger.error("Failed to import ultralytics. Please install with: pip install ultralytics")
        return False
    except Exception as e:
        logger.error(f"Failed to load YOLOv8 model: {str(e)}")
        return False

# Try to load the model at module initialization
load_ppe_model()

def read_image_safely(image_path):
    """
    Read an image file safely, handling different formats including JPEG.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Tuple of (image_array, width, height) or (None, None, None) if failed
    """
    # First try standard OpenCV approach
    image = cv2.imread(image_path)
    if image is not None:
        return image, image.shape[1], image.shape[0]
    
    # If that fails, try alternative approaches
    try:
        # Check if PIL is available
        try:
            from PIL import Image
            img = Image.open(image_path)
            img_array = np.array(img)
            # Convert RGB to BGR (OpenCV format)
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_array = img_array[:, :, ::-1]
            return img_array, img.width, img.height
        except ImportError:
            logger.warning("PIL not available for fallback image reading")
        
        # Try reading with OpenCV's imdecode
        with open(image_path, 'rb') as f:
            img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is not None:
                return img, img.shape[1], img.shape[0]
    
    except Exception as e:
        logger.error(f"All image reading methods failed: {str(e)}")
    
    return None, None, None

def run_ppe_inference(image_path, confidence, overlap):
    """
    Run inference for PPE detection using the YOLOv8 model.
    
    Args:
        image_path: Path to the image file
        confidence: Confidence threshold (0-1)
        overlap: Overlap threshold (0-1)
    
    Returns:
        JSON response with detection results in the same format as Roboflow API
    """
    try:
        # Get image dimensions using the safe reading function
        image, width, height = read_image_safely(image_path)
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Check if model is loaded and attempt to reload if not
        if not model_loaded_properly or ppe_model is None:
            logger.warning("PPE model not loaded properly, attempting to load now...")
            if not load_ppe_model():
                logger.error("Could not load PPE model. Please ensure 'ppe.pt' exists.")
                return {
                    "predictions": [],
                    "image": {"width": width, "height": height},
                    "model": "ppe-detection-model",
                    "version": "not-loaded",
                    "message": "PPE model could not be loaded. Please ensure 'ppe.pt' exists in project directory."
                }

        # Run inference with YOLOv8
        logger.info(f"Running PPE inference on {image_path}")
        try:
            # YOLOv8 uses a different method signature than YOLOv5
            results = ppe_model.predict(
                source=image_path,
                conf=confidence,
                iou=overlap,
                verbose=False
            )
            result = results[0]  # Get the first result
            logger.info(f"PPE inference completed")
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            # Return empty predictions on error
            return {
                "predictions": [],
                "image": {"width": width, "height": height},
                "model": "ppe-detection-model",
                "version": "error",
                "message": f"Error during inference: {str(e)}"
            }
        
        # Convert YOLOv8 results to Roboflow API format
        predictions = []
        try:
            # Extract detection boxes
            if hasattr(result, 'boxes') and len(result.boxes) > 0:
                boxes = result.boxes.cpu().numpy()
                
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0]  # Get box in (top, left, bottom, right) format
                    conf = box.conf[0]  # Confidence score
                    cls_id = int(box.cls[0])  # Class ID

                    # Map class ID to name
                    if hasattr(result, 'names') and cls_id in result.names:
                        class_name = result.names[cls_id]
                    else:
                        class_name = f"class_{cls_id}"
                    
                    # Apply the class mapping if available
                    if class_name in PPE_CLASS_MAP:
                        class_name = PPE_CLASS_MAP[class_name]
                    
                    # Calculate center point, width and height (Roboflow format)
                    x = (x1 + x2) / 2
                    y = (y1 + y2) / 2
                    w = x2 - x1
                    h = y2 - y1
                    
                    predictions.append({
                        "x": float(x),
                        "y": float(y),
                        "width": float(w),
                        "height": float(h),
                        "confidence": float(conf),
                        "class": class_name
                    })
                    
                logger.info(f"Processed {len(predictions)} PPE detections")
            else:
                logger.info("No PPE detections found")
                
        except Exception as e:
            logger.error(f"Error processing prediction results: {str(e)}")
            # Continue with any predictions we were able to process
        
        return {
            "predictions": predictions,
            "image": {
                "width": width,
                "height": height
            },
            "model": "ppe-detection-model-yolov8",
            "version": "1.0"
        }
    except Exception as e:
        logger.error(f"PPE detection failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return empty predictions but still include error message
        width = 0
        height = 0
        if 'width' in locals() and width is not None:
            width = width
        if 'height' in locals() and height is not None:
            height = height
            
        return {
            "predictions": [],
            "image": {"width": width, "height": height},
            "model": "ppe-detection-model",
            "version": "error",
            "error": str(e),
            "message": "Error occurred during PPE detection."
        }
