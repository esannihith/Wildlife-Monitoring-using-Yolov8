import os
import shutil
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import sys
import platform
import uuid

# Import our detection scripts
from detection.animal_detection import run_animal_inference
from detection.weapon_detection import run_weapon_inference
from detection.ppe_detection import run_ppe_inference, load_ppe_model, find_ppe_model
from utils.detection_utils import draw_bounding_boxes, combine_detection_results
from detection.video_processing import process_video # Corrected import

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    # Home page
    return render_template('home.html')

@app.route('/features')
def features():
    # Route for features page
    return render_template('features.html')

@app.route('/detect')
def detect():
    # Route for the detection page
    return render_template('detect.html')

@app.route('/debug')
def debug_info():
    """Debug route to check model loading and environment"""
    info = {
        "python_version": platform.python_version(),
        "system_info": platform.platform(),
        "torch_available": "torch" in sys.modules,
        "cv2_available": "cv2" in sys.modules,
        "numpy_available": "numpy" in sys.modules,
        "ppe_model_path": find_ppe_model(),
        "ppe_model_loaded": load_ppe_model(),
        "project_dir": os.path.abspath(os.path.dirname(__file__)),
        "files_in_project": os.listdir(os.path.abspath(os.path.dirname(__file__)))
    }
    return jsonify(info)

# New endpoint for animal/human detection only
@app.route('/detect/animal', methods=['POST'])
def detect_animal():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400

    # Generate unique filename to avoid overwriting
    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    uploaded_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(uploaded_path)

    try:
        # Run animal detection
        result = run_animal_inference(uploaded_path, confidence=0.3, overlap=0.6)
        result_path = os.path.join(app.config['RESULT_FOLDER'], f'animal_{unique_filename}')
        draw_bounding_boxes(uploaded_path, result, result_path)

        # Count humans and animals
        humans_count = len([p for p in result['predictions'] if p['class'] == 'human'])
        animals_count = len([p for p in result['predictions'] if p['class'] != 'human'])
        
        return jsonify({
            "detection_result": f"/static/results/animal_{unique_filename}",
            "summary": {
                "humans_detected": humans_count,
                "animals_detected": animals_count
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# New endpoint for PPE detection only
@app.route('/detect/ppe', methods=['POST'])
def detect_ppe():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400

    # Generate unique filename to avoid overwriting
    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    uploaded_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(uploaded_path)

    try:
        # Run PPE detection
        result = run_ppe_inference(uploaded_path, confidence=0.3, overlap=0.6)
        result_path = os.path.join(app.config['RESULT_FOLDER'], f'ppe_{unique_filename}')
        
        # Check if there was an error in PPE detection
        if "error" in result:
            # Just copy the original image if there was an error
            shutil.copy(uploaded_path, result_path)
        else:
            draw_bounding_boxes(uploaded_path, result, result_path)

        # Count PPE items by type (if available)
        ppe_count = len(result.get('predictions', []))
        ppe_items = {}
        for pred in result.get('predictions', []):
            item_type = pred.get('class', 'unknown')
            ppe_items[item_type] = ppe_items.get(item_type, 0) + 1
        
        return jsonify({
            "detection_result": f"/static/results/ppe_{unique_filename}",
            "summary": {
                "ppe_detected": ppe_count,
                "ppe_items": ppe_items
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# New endpoint for weapon detection only
@app.route('/detect/weapon', methods=['POST'])
def detect_weapon():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400

    # Generate unique filename to avoid overwriting
    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    uploaded_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(uploaded_path)

    try:
        # Run weapon detection
        result = run_weapon_inference(uploaded_path, confidence=0.25, overlap=0.7)
        result_path = os.path.join(app.config['RESULT_FOLDER'], f'weapon_{unique_filename}')
        draw_bounding_boxes(uploaded_path, result, result_path)

        # Count weapons by type (if available)
        weapons_count = len(result.get('predictions', []))
        weapon_types = {}
        for pred in result.get('predictions', []):
            weapon_type = pred.get('class', 'unknown')
            weapon_types[weapon_type] = weapon_types.get(weapon_type, 0) + 1
        
        return jsonify({
            "detection_result": f"/static/results/weapon_{unique_filename}",
            "summary": {
                "weapons_detected": weapons_count,
                "weapon_types": weapon_types
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# New endpoint for multi-model detection
@app.route('/detect/multi', methods=['POST'])
def detect_multi():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400

    # Generate unique filename to avoid overwriting
    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    uploaded_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(uploaded_path)

    try:
        # Run all detection models
        animal_result = run_animal_inference(uploaded_path, confidence=0.3, overlap=0.6)
        weapon_result = run_weapon_inference(uploaded_path, confidence=0.25, overlap=0.6)
        ppe_result = run_ppe_inference(uploaded_path, confidence=0.3, overlap=0.6)
        ppe_result['predictions'] = [pred for pred in ppe_result.get('predictions', []) if pred.get('class') != 'person']
        
        # Combine all results into one image
        combined_result = {
            "predictions": []
        }
        
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
        
        # Draw combined results
        result_path = os.path.join(app.config['RESULT_FOLDER'], f'multi_{unique_filename}')
        draw_bounding_boxes(uploaded_path, combined_result, result_path, use_custom_colors=True)
        
        # Prepare summary counts
        humans_count = len([p for p in animal_result.get('predictions', []) if p.get('class') == 'human'])
        animals_count = len([p for p in animal_result.get('predictions', []) if p.get('class') != 'human'])
        weapons_count = len(weapon_result.get('predictions', []))
        ppe_count = len(ppe_result.get('predictions', [])) if "error" not in ppe_result else 0
        
        return jsonify({
            "detection_result": f"/static/results/multi_{unique_filename}",
            "summary": {
                "humans_detected": humans_count,
                "animals_detected": animals_count,
                "weapons_detected": weapons_count,
                "ppe_detected": ppe_count
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# New endpoint for multi-model video detection
@app.route('/detect/video-multi', methods=['POST'])
def detect_video_multi():
    if 'video' not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No video selected"}), 400

    # Generate unique filename to avoid overwriting
    unique_suffix = uuid.uuid4().hex
    original_filename = secure_filename(file.filename)
    uploaded_filename = f"{unique_suffix}_{original_filename}"
    uploaded_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_filename)
    
    try:
        file.save(uploaded_path)

        # The output_folder for process_video should be app.config['RESULT_FOLDER']
        # The process_video function will create its own uniquely named output file inside this folder.
        processed_video_path = process_video(uploaded_path, app.config['RESULT_FOLDER'])

        if processed_video_path is None:
            # This might happen if process_video encounters an error like failing to open the video
            return jsonify({"error": "Video processing failed. Check server logs."}), 500

        # Construct the web-accessible path for the client
        processed_video_filename = os.path.basename(processed_video_path)
        
        return jsonify({
            "detection_result_video": f"/static/results/{processed_video_filename}",
            "summary": {
                "message": "Video processing complete. Detections are embedded in the video."
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Clean up uploaded file if processing fails
        if os.path.exists(uploaded_path):
            os.remove(uploaded_path)
        # Note: process_video is responsible for its own output cleanup on error if needed.
        return jsonify({"error": f"Error processing video: {str(e)}"}), 500

# Legacy endpoint for backward compatibility
@app.route('/analyze', methods=['POST'])
def analyze():
    # Simply redirect to multi-model detection
    return detect_multi()

# Create a route to serve result files
@app.route('/static/results/<filename>')
def serve_result_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)