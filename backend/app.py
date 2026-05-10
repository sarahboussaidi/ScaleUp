"""
Pitch Analyzer API - Backend Service
Simplified for Next.js integration
"""

from flask import Flask, request, jsonify
from flask import send_file
from flask_cors import CORS
import cv2
import numpy as np
import os
import base64
import tensorflow as tf
from tensorflow.keras.models import load_model
import traceback
import pickle
import mediapipe as mp
import librosa
import io
import tempfile
from strength_predictor import hybrid_strength_predict
try:
    from speech_strength_app import transcribe_audio
except Exception:
    transcribe_audio = None

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Get the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Labels for predictions
EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
STRESS_LABELS = ["not_stress", "stress"]
VOICE_EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]  # Adjust based on model training

# Global models storage
models_loaded = {
    'emotion': None,
    'stress': None,
    'pose_detector': None,
    'confidence_model': None,
    'label_encoder': None,
    'scaler': None,
    'voice_emotion': None,
}


def find_model_path(*relative_paths):
    for relative_path in relative_paths:
        candidate_path = os.path.join(BASE_DIR, relative_path)
        if os.path.exists(candidate_path):
            return candidate_path
    return None

def load_models():
    """Load ML models"""
    try:
        emotion_path = find_model_path(
            "models/emotion_model.h5",
            "models/emotion/emotion_model.h5",
            "models/emotion/best_model_64.0pct.h5",
        )
        stress_path = find_model_path(
            "models/best_final_stress_cnn_73.h5",
            "models/stress/best_final_stress_cnn_73.h5",
        )
        
        if emotion_path:
            models_loaded['emotion'] = load_model(emotion_path)
            print("[OK] Emotion model loaded")
        else:
            print("[!] Emotion model not found in any expected location")
            
        if stress_path:
            models_loaded['stress'] = load_model(stress_path)
            print("[OK] Stress model loaded")
        else:
            print("[!] Stress model not found in any expected location")
        
        # Load pose detection model
        try:
            pose_task_path = find_model_path("models/posturedata/pose_landmarker.task")
            if pose_task_path:
                base_options = mp.tasks.BaseOptions(model_asset_path=pose_task_path)
                options = mp.tasks.vision.PoseLandmarkerOptions(base_options=base_options, output_segmentation_masks=False)
                models_loaded['pose_detector'] = mp.tasks.vision.PoseLandmarker.create_from_options(options)
                print("[OK] Pose detector loaded")
            else:
                print("[!] Pose landmarker task not found")
        except Exception as e:
            print(f"[!] Pose detector loading failed: {e}")
        
        # Load posture confidence model
        try:
            confidence_path = find_model_path("models/posturedata/confidence_model.pkl")
            if confidence_path:
                with open(confidence_path, 'rb') as f:
                    models_loaded['confidence_model'] = pickle.load(f)
                print("[OK] Confidence model loaded")
            else:
                print("[!] Confidence model not found - posture detection will use landmarks only")
        except Exception as e:
            print(f"[!] Confidence model loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load label encoder
        try:
            encoder_path = find_model_path("models/posturedata/label_encoder.pkl")
            if encoder_path:
                with open(encoder_path, 'rb') as f:
                    models_loaded['label_encoder'] = pickle.load(f)
                print("[OK] Label encoder loaded")
            else:
                print("[!] Label encoder not found")
        except Exception as e:
            print(f"[!] Label encoder loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load scaler
        try:
            scaler_path = find_model_path("models/posturedata/scaler.pkl")
            if scaler_path:
                with open(scaler_path, 'rb') as f:
                    models_loaded['scaler'] = pickle.load(f)
                print("[OK] Scaler loaded")
            else:
                print("[!] Scaler not found")
        except Exception as e:
            print(f"[!] Scaler loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load voice emotion model
        try:
            voice_emotion_path = find_model_path(
                "models/best_cnn2d_v2.keras",
                "best_cnn2d_v2.keras",
            )
            if voice_emotion_path:
                models_loaded['voice_emotion'] = load_model(voice_emotion_path)
                print("[OK] Voice emotion model loaded")
            else:
                print("[!] Voice emotion model not found")
        except Exception as e:
            print(f"[!] Voice emotion model loading failed: {e}")
            
    except Exception as e:
        print(f"[ERROR] Error loading models: {e}")
        traceback.print_exc()


# -----------------
# Pitch deck routes
# -----------------
@app.route('/api/pitch/generate', methods=['POST'])
def api_generate_pitch():
    try:
        data = request.json or {}
        company = data.get('company', 'Your Startup')
        industry = data.get('industry', 'your industry')
        description = data.get('description', 'a clear solution to a real problem')

        # Import here to avoid heavy import at startup
        from pitch_generator import generate_all_slides

        slides = generate_all_slides(company, industry, description)
        return jsonify({'slides': slides})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/pitch/download', methods=['POST'])
def api_download_pitch():
    try:
        data = request.json or {}
        company = data.get('company', 'Your Startup')
        industry = data.get('industry', 'your industry')
        description = data.get('description', 'a clear solution to a real problem')

        from pitch_generator import generate_all_slides, build_pptx

        slides = generate_all_slides(company, industry, description)
        # Save to temporary file
        fd, tmp_path = tempfile.mkstemp(suffix='.pptx')
        os.close(fd)
        build_pptx(company, industry, description, slides, tmp_path)
        return send_file(tmp_path, as_attachment=True, download_name=f"{company}_pitch_deck.pptx")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def preprocess_face(face_array):
    """Preprocess face image for model prediction"""
    try:
        face = cv2.resize(face_array, (48, 48))
        face = face.astype(np.float32) / 255.0
        face = np.expand_dims(face, axis=-1)
        face = np.expand_dims(face, axis=0)
        return face
    except Exception as e:
        print(f"[ERROR] Error preprocessing face: {e}")
        return None

def detect_emotion(frame_base64):
    """Detect emotion from frame"""
    try:
        if models_loaded['emotion'] is None:
            return {"error": "Emotion model not loaded"}
        
        # Decode base64 frame
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale for emotion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Simple face detection
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return {"emotion": "no_face", "confidence": 0.0}
        
        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_gray = gray[y:y+h, x:x+w]
        
        # Preprocess and predict
        preprocessed = preprocess_face(face_gray)
        if preprocessed is None:
            return {"error": "Preprocessing failed"}
        
        preds = models_loaded['emotion'].predict(preprocessed, verbose=0)[0]
        emotion_idx = int(np.argmax(preds))
        
        return {
            "emotion": EMOTION_LABELS[emotion_idx],
            "confidence": float(preds[emotion_idx]),
            "face_box": {
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
            },
            "scores": {
                EMOTION_LABELS[i]: float(preds[i])
                for i in range(len(EMOTION_LABELS))
            }
        }
    except Exception as e:
        print(f"[ERROR] Error detecting emotion: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def detect_stress(frame_base64):
    """Detect stress from frame"""
    try:
        if models_loaded['stress'] is None:
            return {"error": "Stress model not loaded"}
        
        # Decode base64 frame
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face detection
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return {"stress": "unknown", "confidence": 0.0}
        
        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_gray = gray[y:y+h, x:x+w]
        
        # Preprocess and predict
        preprocessed = preprocess_face(face_gray)
        if preprocessed is None:
            return {"error": "Preprocessing failed"}
        
        preds = models_loaded['stress'].predict(preprocessed, verbose=0)[0]
        
        if len(preds) == 1:
            stress_prob = float(preds[0])
            label = "stressed" if stress_prob >= 0.5 else "calm"
            confidence = stress_prob if label == "stressed" else 1 - stress_prob
        else:
            stress_idx = int(np.argmax(preds))
            label = STRESS_LABELS[stress_idx]
            confidence = float(preds[stress_idx])
        
        return {
            "stress": label,
            "confidence": confidence,
            "face_box": {
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
            },
        }
    except Exception as e:
        print(f"[ERROR] Error detecting stress: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def detect_posture(frame_base64):
    """Detect posture from frame"""
    try:
        if models_loaded['pose_detector'] is None:
            return {"error": "Pose detector not loaded"}
        
        if models_loaded['confidence_model'] is None:
            return {"error": "Confidence model not loaded"}
        
        # Decode base64 frame
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Detect pose
        detection_result = models_loaded['pose_detector'].detect(mp_image)
        
        if not detection_result.pose_landmarks:
            return {"posture": "unknown", "confidence": 0.0}
        
        # Extract landmarks
        landmarks = detection_result.pose_landmarks[0]
        
        # Extract key points for posture analysis
        # Using 33 landmarks from MediaPipe Pose
        keypoints = []
        for landmark in landmarks:
            keypoints.extend([landmark.x, landmark.y, landmark.z])
        
        keypoints = np.array(keypoints).reshape(1, -1)
        
        # Scale features
        if models_loaded['scaler'] is not None:
            keypoints = models_loaded['scaler'].transform(keypoints)
        
        # Predict posture
        if models_loaded['confidence_model'] is not None:
            prediction = models_loaded['confidence_model'].predict(keypoints)[0]
            
            # Decode label
            if models_loaded['label_encoder'] is not None:
                posture_label = models_loaded['label_encoder'].inverse_transform([prediction])[0]
            else:
                posture_label = str(prediction)
            
            confidence = float(np.max(models_loaded['confidence_model'].predict_proba(keypoints)[0])) if hasattr(models_loaded['confidence_model'], 'predict_proba') else 0.85
        else:
            posture_label = "unknown"
            confidence = 0.0
        
        return {
            "posture": posture_label,
            "confidence": confidence,
            "landmarks_count": len(landmarks)
        }
    except Exception as e:
        print(f"[ERROR] Error detecting posture: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def detect_voice_emotion(audio_base64):
    """Detect emotion from audio using CNN model"""
    try:
        if models_loaded['voice_emotion'] is None:
            return {"error": "Voice emotion model not loaded"}
        
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64.split(',')[1] if ',' in audio_base64 else audio_base64)
        
        # Load audio from bytes
        try:
            audio_stream = io.BytesIO(audio_data)
            y, sr = librosa.load(audio_stream, sr=16000)
        except Exception as e:
            print(f"[!] Librosa load failed: {e}, trying alternative")
            # If librosa fails, try alternative loading
            import soundfile as sf
            audio_stream = io.BytesIO(audio_data)
            y, sr = sf.read(audio_stream)
            y = np.array(y, dtype=np.float32)
        
        # Extract mel spectrogram
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, n_fft=2048, hop_length=512)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Normalize
        mel_spec_db = (mel_spec_db - np.mean(mel_spec_db)) / (np.std(mel_spec_db) + 1e-8)
        
        # Reshape to match model input (add channel and batch dimensions)
        mel_spec_input = np.expand_dims(np.expand_dims(mel_spec_db, axis=0), axis=-1)
        
        # Ensure correct input shape for model (adjust if needed)
        # Common shapes: (1, 128, time_steps, 1) or similar
        if mel_spec_input.shape[2] < 32:
            # Pad if too short
            pad_width = ((0, 0), (0, 0), (0, 32 - mel_spec_input.shape[2]), (0, 0))
            mel_spec_input = np.pad(mel_spec_input, pad_width, mode='constant')
        else:
            # Crop if too long
            mel_spec_input = mel_spec_input[:, :, :32, :]
        
        # Predict
        preds = models_loaded['voice_emotion'].predict(mel_spec_input, verbose=0)[0]
        emotion_idx = int(np.argmax(preds))
        
        return {
            "emotion": VOICE_EMOTION_LABELS[emotion_idx],
            "confidence": float(preds[emotion_idx]),
            "scores": {
                VOICE_EMOTION_LABELS[i]: float(preds[i])
                for i in range(len(VOICE_EMOTION_LABELS))
            }
        }
    except Exception as e:
        print(f"[ERROR] Error detecting voice emotion: {e}")
        traceback.print_exc()
        return {"error": str(e)}

# ========================
# API ENDPOINTS
# ========================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "models_loaded": {
            "emotion": models_loaded['emotion'] is not None,
            "stress": models_loaded['stress'] is not None,
            "posture": models_loaded['pose_detector'] is not None,
            "voice_emotion": models_loaded['voice_emotion'] is not None,
        }
    })

@app.route('/api/analyze/emotion', methods=['POST'])
def analyze_emotion():
    """Analyze emotion from image"""
    try:
        data = request.json
        frame_base64 = data.get('frame')
        
        if not frame_base64:
            return jsonify({"error": "No frame provided"}), 400
        
        result = detect_emotion(frame_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/stress', methods=['POST'])
def analyze_stress():
    """Analyze stress from image"""
    try:
        data = request.json
        frame_base64 = data.get('frame')
        
        if not frame_base64:
            return jsonify({"error": "No frame provided"}), 400
        
        result = detect_stress(frame_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/posture', methods=['POST'])
def analyze_posture():
    """Analyze posture from image"""
    try:
        data = request.json
        frame_base64 = data.get('frame')
        
        if not frame_base64:
            return jsonify({"error": "No frame provided"}), 400
        
        result = detect_posture(frame_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/voice-emotion', methods=['POST'])
def analyze_voice_emotion():
    """Analyze voice emotion from audio"""
    try:
        data = request.json
        audio_base64 = data.get('audio')
        
        if not audio_base64:
            return jsonify({"error": "No audio provided"}), 400
        
        result = detect_voice_emotion(audio_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze/speech-strength', methods=['POST'])
def analyze_speech_strength():
    """Analyze speech strength from audio (base64 or multipart file)"""
    try:
        # Accept JSON body with 'audio' (data URL) or multipart file
        if request.content_type and request.content_type.startswith('multipart'):
            # file upload
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            f = request.files['file']
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            f.save(tmp.name)
            audio_path = tmp.name
        else:
            data = request.get_json() or {}
            audio_b64 = data.get('audio')
            if not audio_b64:
                return jsonify({'error': 'No audio provided'}), 400
            # strip data URL prefix if present
            if ',' in audio_b64:
                audio_b64 = audio_b64.split(',', 1)[1]
            audio_bytes = base64.b64decode(audio_b64)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            tmp.write(audio_bytes)
            tmp.flush()
            audio_path = tmp.name

        # Transcribe
        transcript = ""
        if transcribe_audio is not None:
            try:
                transcript = transcribe_audio(audio_path)
            except Exception:
                transcript = ""

        # Predict strength
        prediction = hybrid_strength_predict(transcript or "")

        return jsonify({
            'transcript': transcript,
            'prediction': prediction
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Load models on startup
    load_models()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
