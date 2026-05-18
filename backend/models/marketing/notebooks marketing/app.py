"""
Flask Web Application for Screenshot Engagement Evaluation
Provides UI for uploading screenshots and viewing complete evaluation results
"""

import os
import json
import base64
import traceback
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, render_template_string, request, jsonify, send_file
import io

# Import the evaluation pipeline
from engagement_pipeline import predict_engagement_from_screenshot

# ============================================================================
# Configuration
# ============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['RESULTS_FOLDER'] = './results'
app.config['TEMPLATES_AUTO_RELOAD'] = True

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
OUTPUT_DIR = './outputs/'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# ============================================================================
# Helper Functions
# ============================================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image_to_base64(image_path):
    """Encode image file to base64 for embedding in HTML."""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def format_evaluation_for_display(eval_result):
    """
    Convert evaluation pipeline output to web-friendly format.
    Handles all metric conversions and data formatting.
    """
    try:
        text_xai = eval_result.get('text_xai', {})
        full_ocr_text = text_xai.get('raw_text_full') or eval_result.get('text_features', {}).get('raw_text', '') or ''
        preview_ocr_text = text_xai.get('raw_text_preview') or full_ocr_text[:500]

        # Platform auto-detection removed; show selected platform (from metadata)
        selected_platform = eval_result.get('platform_used_for_text_evaluation') or eval_result.get('platform') or 'unknown'
        platform_display = (selected_platform or 'unknown').upper()

        # Helper to safely get and convert scores, handling None values
        def safe_score(val, default=0):
            if val is None:
                return float(default)
            return float(val)

        # Extract scores safely
        text_score = safe_score(eval_result.get('text_evaluation', {}).get('overall_score', 0))
        visual_features = eval_result.get('visual_features', {})
        visual_xai = eval_result.get('visual_xai', {})
        # Prefer the feature-composite score so the display matches the visible breakdown.
        visual_score = safe_score(
            visual_features.get('score_0_10',
                visual_xai.get('visual_prediction', {}).get('score_0_10', 0)
            )
        )
        overall_score = safe_score(eval_result.get('overall_evaluation', {}).get('overall_score_0_10', 0))

        if visual_score < 3.33:
            fallback_visual_class = 'bad'
        elif visual_score < 6.67:
            fallback_visual_class = 'average'
        else:
            fallback_visual_class = 'good'

        # Extract XAI data
        text_xai = eval_result.get('text_xai', {})
        visual_xai = eval_result.get('visual_xai', {})

        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'platform_selected': platform_display,
            'text_evaluation': {
                'overall_score': round(text_score, 1),
                'penalized_overall_score': round(text_xai.get('penalized_overall_score', text_score), 1),
                'dimensions': eval_result.get('text_evaluation', {}).get('dimension_scores', {}),
                'ocr_text': preview_ocr_text,
                'ocr_text_full': full_ocr_text,
                'text_length': len(full_ocr_text),
                'sentiment': eval_result.get('text_evaluation', {}).get('sentiment_detail', {}),
                'issues': eval_result.get('text_evaluation', {}).get('issues', {}),
            },
            'visual_evaluation': {
                'overall_score': round(visual_score, 1),
                'class_label': visual_features.get('class_label') or fallback_visual_class,
                'score_band': visual_features.get('class_label') or fallback_visual_class,
                'confidence': visual_features.get('confidence', 0.0),
                'class_probs': visual_features.get('class_probs', {}),
                'model_source': visual_features.get('model_source', '') or visual_xai.get('score_source', ''),
                'visual_features': visual_features.get('visual_features', {}),
                'xai_summary': eval_result.get('visual_xai', {}).get('interpretation', ''),
                'composition': eval_result.get('visual_xai', {}).get('image_composition', {}),
                'extracted_image': eval_result.get('extracted_image_b64', None),
            },
            'text_xai': {
                'interpretation': text_xai.get('interpretation', ''),
                'overall_score': text_xai.get('overall_score', 0.0),
                'penalized_overall_score': text_xai.get('penalized_overall_score', 0.0),
                'universal_score': text_xai.get('universal_score', 0.0),
                'penalty_applied': text_xai.get('penalty_applied', 0.0),
                'dimension_scores': text_xai.get('dimension_scores', {}),
                'ranked_dimensions': text_xai.get('ranked_dimensions', []),
                'top_features': text_xai.get('top_features', {}),
                'issues_detected': text_xai.get('issues_detected', {}),
                'feature_metrics': text_xai.get('feature_metrics', {}),
            },
            'visual_xai': {
                'interpretation': visual_xai.get('interpretation', ''),
                'grad_cam': visual_xai.get('grad_cam', {}),
                'attribute_importance': visual_xai.get('attribute_importance_inference', {}),
                'visual_prediction': visual_xai.get('visual_prediction', {}),
                'image_composition': visual_xai.get('image_composition', {}),
            },
            'overall_engagement': {
                'score': round(overall_score, 1),
                'verdict': eval_result.get('overall_evaluation', {}).get('verdict', 'Unknown'),
                'breakdown': eval_result.get('overall_evaluation', {}).get('breakdown', {}),
            },
        }
        return result
    except Exception as e:
        print(f"Error formatting evaluation: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def get_verdict_color(score):
    """Return CSS color class based on engagement score."""
    # Handle None values safely
    if score is None:
        score = 0.0
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0.0
    
    if score >= 8.0:
        return 'verdict-excellent'
    elif score >= 6.0:
        return 'verdict-good'
    elif score >= 4.0:
        return 'verdict-mid'
    elif score >= 2.0:
        return 'verdict-poor'
    else:
        return 'verdict-bad'

# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def index():
    """Upload form page."""
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    """
    Main evaluation endpoint.
    Accepts image upload, runs full pipeline, returns JSON results.
    """
    try:
        # Validate file
        if 'screenshot' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['screenshot']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file format. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        saved_filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)

        print(f"[{datetime.now()}] Processing: {saved_filename}")

        # Read user-selected platform (if any) and pass as metadata
        user_platform = (request.form.get('platform') or '').strip().lower()
        metadata = {'platform': user_platform} if user_platform else {}

        # Run evaluation pipeline (platform auto-detection disabled; uses metadata override)
        eval_result = predict_engagement_from_screenshot(filepath, OUTPUT_DIR, metadata=metadata)

        # Format for web display
        formatted_result = format_evaluation_for_display(eval_result)
        
        if not formatted_result.get('success'):
            os.remove(filepath)
            return jsonify({
                'success': False,
                'error': f"Evaluation failed: {formatted_result.get('error', 'Unknown error')}"
            }), 500

        # Add image data
        img_base64 = encode_image_to_base64(filepath)
        if img_base64:
            formatted_result['image_base64'] = img_base64

        # Save result using a stable base id so links and downloads resolve cleanly
        result_id = os.path.splitext(saved_filename)[0] + '_result'
        result_filename = result_id + '.json'
        result_filepath = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
        with open(result_filepath, 'w') as f:
            json.dump(eval_result, f, indent=2, default=str)

        formatted_result['result_id'] = result_id
        formatted_result['timestamp'] = datetime.now().isoformat()

        print(f"[{datetime.now()}] ✓ Completed: {saved_filename}")

        return jsonify(formatted_result), 200

    except Exception as e:
        print(f"[ERROR] {datetime.now()}: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/results/<result_id>')
def view_results(result_id):
    """Display formatted results page."""
    try:
        result_file = os.path.join(app.config['RESULTS_FOLDER'], result_id + '.json')
        if not os.path.exists(result_file):
            return "Results not found", 404

        with open(result_file, 'r') as f:
            eval_result = json.load(f)

        formatted = format_evaluation_for_display(eval_result)
        # Ensure the displayed visual overall score uses the feature-composite value
        # when available in the saved JSON (defensive override to avoid stale fields).
        try:
            raw_vs = eval_result.get('visual_features', {}).get('score_0_10')
            if raw_vs is not None:
                formatted['visual_evaluation']['overall_score'] = round(float(raw_vs), 1)
                # prefer explicit model_source from visual_features when present
                formatted['visual_evaluation']['model_source'] = eval_result.get('visual_features', {}).get('model_source', formatted['visual_evaluation'].get('model_source'))
        except Exception:
            pass
        
        # Get image if available
        uploads = os.listdir(app.config['UPLOAD_FOLDER'])
        matching_img = [f for f in uploads if result_id.split('_result')[0] in f]
        image_b64 = None
        if matching_img:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], matching_img[0])
            image_b64 = encode_image_to_base64(img_path)

        return render_template(
            'results.html',
            result=formatted,
            result_id=result_id,
            image_base64=image_b64,
            verdict_color=get_verdict_color(formatted['overall_engagement']['score'])
        )

    except Exception as e:
        print(f"Error viewing results: {e}")
        return f"Error loading results: {str(e)}", 500

@app.route('/download-report/<result_id>')
def download_report(result_id):
    """Download full evaluation as JSON."""
    try:
        result_base = result_id[:-5] if result_id.endswith('.json') else result_id
        result_file = os.path.join(app.config['RESULTS_FOLDER'], result_base + '.json')
        if not os.path.exists(result_file):
            return "Report not found", 404

        return send_file(
            result_file,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'{result_base}_report.json'
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/pipeline')
def pipeline():
    """Display the evaluation pipeline flowchart."""
    template_path = Path(app.root_path) / 'templates' / 'pipeline.html'
    template_content = template_path.read_text(encoding='utf-8')
    return render_template_string(template_content)

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'File too large (max 50MB)'}), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("""
    ============================================================
    Screenshot Engagement Evaluation Web Interface
    Starting Server...
    ============================================================
    
    [*] Upload Screenshots at: http://localhost:5000
    [*] Max file size: 50MB
    [*] Models loaded from: {0}
    [*] Uploads saved to: {1}
    [*] Results saved to: {2}
    
    """.format(OUTPUT_DIR, app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER']))
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )
