import cv2
import os
import uuid
import logging
from detection.animal_detection import run_animal_inference
from detection.ppe_detection import run_ppe_inference
from detection.weapon_detection import run_weapon_inference
from utils.detection_utils import combine_detection_results, draw_bounding_boxes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_video_frame(frame, frame_path_for_inference, confidence=0.3, overlap=0.5):
    """
    Process a single video frame: run all three detections, combine results.
    The frame itself is passed for drawing, while its path is used for inference APIs.
    """
    try:
        # Run inferences
        animal_result = run_animal_inference(frame_path_for_inference, confidence, overlap)
        ppe_result = run_ppe_inference(frame_path_for_inference, confidence, overlap)
        weapon_result = run_weapon_inference(frame_path_for_inference, confidence, overlap)

        # Combine results
        combined_result = combine_detection_results(animal_result, ppe_result, weapon_result)
        return combined_result
    except Exception as e:
        logger.error(f"Error processing frame {frame_path_for_inference}: {e}")
        return {"predictions": []} # Return empty predictions on error

def process_video(video_path, output_folder, confidence=0.3, overlap=0.5):
    """
    Process a video: extract frames, run multi-model detection on each, and reassemble.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Error opening video file: {video_path}")
        return None

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Define the codec and create VideoWriter object
    output_filename = f"processed_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(output_folder, output_filename)
    # Ensure XVID is a safe bet, or use MP4V for .mp4
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    temp_frame_folder = os.path.join(output_folder, "temp_frames")
    os.makedirs(temp_frame_folder, exist_ok=True)
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_filename = f"frame_{frame_count:04d}.jpg"
        temp_frame_path = os.path.join(temp_frame_folder, frame_filename)
        
        # Save frame temporarily to pass to inference functions
        cv2.imwrite(temp_frame_path, frame)

        # Process the frame
        detection_result = process_video_frame(frame, temp_frame_path, confidence, overlap)

        # Draw bounding boxes on the original frame (not the temp file)
        # Create a unique path for the drawn frame to avoid conflicts if draw_bounding_boxes saves it
        drawn_frame_output_path = os.path.join(temp_frame_folder, f"drawn_{frame_filename}")
        draw_bounding_boxes(temp_frame_path, detection_result, drawn_frame_output_path, use_custom_colors=True)
        
        # Read the frame with drawn boxes to write to video
        processed_frame_img = cv2.imread(drawn_frame_output_path)
        if processed_frame_img is not None:
            out.write(processed_frame_img)
        else:
            # If drawing failed, write original frame
            out.write(frame)
            logger.warning(f"Could not read drawn frame {drawn_frame_output_path}, writing original frame to video.")

        # Clean up temporary frame files for this iteration
        if os.path.exists(temp_frame_path):
            os.remove(temp_frame_path)
        if os.path.exists(drawn_frame_output_path):
            os.remove(drawn_frame_output_path)
            
        frame_count += 1
        logger.info(f"Processed frame {frame_count}")

    cap.release()
    out.release()
    
    # Clean up temp_frames folder
    try:
        for f in os.listdir(temp_frame_folder):
            os.remove(os.path.join(temp_frame_folder, f))
        os.rmdir(temp_frame_folder)
    except Exception as e:
        logger.error(f"Error cleaning up temp_frames folder: {e}")

    logger.info(f"Video processing complete. Output saved to: {output_path}")
    return output_path
