import cv2
import numpy as np
import logging
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Color mapping for different classes
COLOR_MAP = {
    # Animals
    'tiger': (0, 165, 255),    # Orange
    'bear': (0, 215, 255),     # Yellow
    'elephant': (47, 79, 79),  # Dark slate gray - better contrast for elephants
    'giraffe': (230, 216, 173), # Light blue
    'human': (255, 192, 203),  # Pink
    'zebra': (0, 0, 0),        # Black
    'horse': (139, 69, 19),    # Brown
    
    # PPE
    'boots': (255, 0, 0),      # Blue
    'gloves': (0, 255, 0),     # Green
    'helmet': (0, 0, 255),     # Red
    'person': (255, 192, 203), # Pink
    'vest': (255, 255, 0),     # Cyan
    
    # Weapons
    'gun': (0, 0, 255),        # Red
    'knife': (255, 0, 0),      # Blue
    'rifle': (128, 0, 128)     # Purple
}

# Color mapping for different detection types (for multi-model mode)
TYPE_COLOR_MAP = {
    'green': (0, 255, 0),     # Green for animals
    'blue': (255, 0, 0),      # Blue for humans
    'red': (0, 0, 255),       # Red for weapons
    'orange': (0, 165, 255)   # Orange for PPE
}

# Default color for unknown classes
DEFAULT_COLOR = (255, 255, 255)  # White

def draw_bounding_boxes(image_path, detection_result, output_path, use_custom_colors=False):
    """
    Draw bounding boxes on an image based on detection results with improved visibility.
    
    Args:
        image_path: Path to the original image
        detection_result: Detection results from the model in Roboflow API format
        output_path: Path to save the output image with bounding boxes
        use_custom_colors: If True, use the color specified in each prediction's 'color' field
    """
    try:
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Check if detection_result has predictions
        predictions = detection_result.get('predictions', [])
        logger.info(f"Drawing {len(predictions)} bounding boxes")
        
        # Draw each bounding box
        for pred in predictions:
            # Extract coordinates
            x = pred.get('x', 0)
            y = pred.get('y', 0)
            w = pred.get('width', 0)
            h = pred.get('height', 0)
            class_name = pred.get('class', 'unknown')
            confidence = pred.get('confidence', 0)
            
            # Calculate coordinates for the rectangle
            x1 = int(x - w/2)
            y1 = int(y - h/2)
            x2 = int(x + w/2)
            y2 = int(y + h/2)
            
            # Get color based on settings and available info
            if use_custom_colors and 'color' in pred:
                # Use the color specified in the prediction
                color_name = pred['color']
                color = TYPE_COLOR_MAP.get(color_name, DEFAULT_COLOR)
            else:
                # Use the default color mapping
                color = COLOR_MAP.get(class_name.lower(), DEFAULT_COLOR)
            
            # Draw thicker rectangle for better visibility
            box_thickness = 3
            cv2.rectangle(image, (x1, y1), (x2, y2), color, box_thickness)
            
            # Improve text visibility with larger font and better background
            text = f"{class_name.upper()}: {confidence:.2f}"
            
            # Larger font size and thickness
            font_size = 0.7
            font_thickness = 2
            
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_size, font_thickness)[0]
            
            # Create a better background for text visibility
            padding = 5
            
            # Ensure the text background doesn't go outside the image bounds
            text_y = max(y1 - padding, text_size[1] + padding * 2)
            
            # If the box is near the top of the image, put the label below the box
            if y1 < text_size[1] + padding * 3:
                text_y = min(y2 + text_size[1] + padding * 2, height - 5)
            
            # Draw background rectangle for text
            cv2.rectangle(image, 
                         (x1 - padding, text_y - text_size[1] - padding * 2), 
                         (x1 + text_size[0] + padding, text_y), 
                         color, -1)
            
            # Draw text with white color for better contrast
            cv2.putText(image, 
                       text, 
                       (x1, text_y - padding), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       font_size, 
                       (255, 255, 255), 
                       font_thickness)
        
        # Save the image with high quality
        cv2.imwrite(output_path, image, [cv2.IMWRITE_JPEG_QUALITY, 100])
        logger.info(f"Saved output image to {output_path}")
        
    except Exception as e:
        logger.error(f"Error drawing bounding boxes: {str(e)}")
        # In case of error, try to save the original image as is
        try:
            shutil.copy(image_path, output_path)
            logger.warning(f"Copied original image to {output_path} due to drawing error")
        except:
            logger.error(f"Failed to copy original image to {output_path}")

def combine_detection_results(animal_result, ppe_result, weapon_result):
    """
    Combine results from multiple detection models into a single result.
    
    Args:
        animal_result: Results from animal detection
        ppe_result: Results from PPE detection
        weapon_result: Results from weapon detection
    
    Returns:
        A combined detection result dictionary with all predictions
    """
    combined_result = {"predictions": []}
    
    # Add animal/human detections (with class-specific colors)
    for pred in animal_result.get('predictions', []):
        pred['color'] = 'green' if pred.get('class') != 'human' else 'blue'
        combined_result['predictions'].append(pred)
        
    # Add weapon detections (with different color)
    for pred in weapon_result.get('predictions', []):
        pred['color'] = 'red'
        combined_result['predictions'].append(pred)
        
    # Add PPE detections (with different color)
    if "error" not in ppe_result:
        for pred in ppe_result.get('predictions', []):
            pred['color'] = 'orange'
            combined_result['predictions'].append(pred)
    
    return combined_result
