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
import traceback
import importlib
import joblib
import mediapipe as mp
import librosa
import io
import tempfile
from strength_predictor import detect_bad_words, hybrid_strength_predict
try:
    from speech_strength_app import transcribe_audio
except Exception:
    transcribe_audio = None

load_model = tf.keras.models.load_model

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Get the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
VOICE_EMOTION_MODEL_PATH = os.path.join(MODELS_DIR, "best_cnn2d_v2.keras")

# Labels for predictions
EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
STRESS_LABELS = ["not_stress", "stress"]
VOICE_EMOTION_LABELS = ["angry", "calm", "disgust", "fear", "happy", "neutral", "sad", "surprise"]  # 8-class audio emotion model

NUMERIC_POSTURE_COLS = [
    "eye_shoulder_y_ratio",
    "shoulder_y_diff",
    "wrist_distance_x",
    "wrist_shoulder_ratio",
    "nose_eye_center_offset_x",
    "shoulder_span",
    "hip_shoulder_y_diff",
    "body_lean_x",
    "shoulder_center_x",
    "hip_center_x",
    "spine_angle",
    "eye_distance",
    "head_tilt_angle",
    "eye_distance_ratio",
    "shoulder_slope",
]

HEAD_CLASSES = ["Center", "Looking Left", "Looking Right", "Looking Straight"]
ARM_CLASSES = ["Closed Arms", "Open Arms", "Partially Open"]
POSTURE_CLASSES = ["Leaning", "Stiff", "Upright"]

# MediaPipe landmark indices
NOSE = 0
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24

FACE_CASCADE_DEFAULT = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
FACE_CASCADE_ALT2 = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
FACE_DETECTOR = None

try:
    FACE_DETECTOR = mp.solutions.face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.35,
    )
except Exception as e:
    print(f"[WARN] MediaPipe face detector unavailable: {e}")

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


def dist(a, b):
    try:
        result = np.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
        if np.isnan(result) or np.isinf(result):
            return 0.0
        return result
    except Exception:
        return 0.0


def safe_angle(y, x):
    try:
        result = np.degrees(np.arctan2(y, x + 1e-6))
        if np.isnan(result) or np.isinf(result):
            return 0.0
        return result
    except Exception:
        return 0.0


def one_hot(value, classes):
    return [1.0 if value == c else 0.0 for c in classes]


def find_best_face(gray):
    """Find the best face candidate using multiple cascade passes."""
    try:
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        if FACE_DETECTOR is not None:
            try:
                mp_result = FACE_DETECTOR.process(rgb)
                detections = getattr(mp_result, "detections", None) or []
                if detections:
                    h, w = gray.shape[:2]
                    best_detection = max(
                        detections,
                        key=lambda detection: detection.location_data.relative_bounding_box.width
                        * detection.location_data.relative_bounding_box.height,
                    )
                    bbox = best_detection.location_data.relative_bounding_box
                    x = max(0, int(bbox.xmin * w))
                    y = max(0, int(bbox.ymin * h))
                    bw = max(1, int(bbox.width * w))
                    bh = max(1, int(bbox.height * h))
                    return x, y, bw, bh
            except Exception as e:
                print(f"[WARN] MediaPipe face detection fallback failed: {e}")

        variants = [
            (gray, 1.08, 4, 24),
            (cv2.equalizeHist(gray), 1.05, 3, 22),
        ]

        if gray.shape[1] >= 320 and gray.shape[0] >= 240:
            enlarged = cv2.resize(gray, None, fx=1.25, fy=1.25, interpolation=cv2.INTER_LINEAR)
            variants.append((cv2.equalizeHist(enlarged), 1.03, 3, 20))

        best_face = None
        best_area = 0

        for source, scale_factor, min_neighbors, min_size in variants:
            for cascade in (FACE_CASCADE_DEFAULT, FACE_CASCADE_ALT2):
                if cascade.empty():
                    continue

                faces = cascade.detectMultiScale(
                    source,
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=(min_size, min_size),
                )

                if len(faces) == 0:
                    continue

                scale_x = gray.shape[1] / source.shape[1]
                scale_y = gray.shape[0] / source.shape[0]

                for x, y, w, h in faces:
                    area = w * h
                    if area <= best_area:
                        continue

                    best_area = area
                    best_face = (
                        int(x * scale_x),
                        int(y * scale_y),
                        int(w * scale_x),
                        int(h * scale_y),
                    )

        return best_face
    except Exception as e:
        print(f"[WARN] find_best_face failed: {e}")
        return None


def compute_posture_features(landmarks):
    try:
        if not landmarks or len(landmarks) < 33:
            return None

        LS = landmarks[LEFT_SHOULDER]
        RS = landmarks[RIGHT_SHOULDER]
        LH = landmarks[LEFT_HIP]
        RH = landmarks[RIGHT_HIP]
        LW = landmarks[LEFT_WRIST]
        RW = landmarks[RIGHT_WRIST]
        LE = landmarks[LEFT_EAR]
        RE = landmarks[RIGHT_EAR]
        nose_lm = landmarks[NOSE]

        shoulder_center_x = (LS.x + RS.x) / 2
        shoulder_center_y = (LS.y + RS.y) / 2
        hip_center_x = (LH.x + RH.x) / 2
        hip_center_y = (LH.y + RH.y) / 2
        eye_center_x = (LE.x + RE.x) / 2
        eye_center_y = (LE.y + RE.y) / 2

        shoulder_span = dist(LS, RS)
        eye_distance = dist(LE, RE)
        wrist_distance_x = abs(LW.x - RW.x)

        shoulder_y_diff = abs(LS.y - RS.y)
        shoulder_slope = shoulder_y_diff / (abs(LS.x - RS.x) + 1e-6)
        hip_shoulder_y_diff = abs(hip_center_y - shoulder_center_y)
        body_lean_x = shoulder_center_x - hip_center_x

        spine_angle = safe_angle(hip_center_y - shoulder_center_y, shoulder_center_x - hip_center_x)
        head_tilt_angle = safe_angle(nose_lm.y - eye_center_y, nose_lm.x - eye_center_x)

        eye_shoulder_y_ratio = (eye_center_y - shoulder_center_y) / (shoulder_span + 1e-6)
        wrist_shoulder_ratio = wrist_distance_x / (shoulder_span + 1e-6)
        nose_eye_center_offset_x = nose_lm.x - eye_center_x
        eye_distance_ratio = eye_distance / (shoulder_span + 1e-6)

        if abs(nose_eye_center_offset_x) < 0.025:
            head_direction = "Looking Straight"
        elif nose_eye_center_offset_x > 0:
            head_direction = "Looking Right"
        else:
            head_direction = "Looking Left"

        if wrist_shoulder_ratio > 1.35:
            arm_position = "Open Arms"
        elif wrist_shoulder_ratio < 0.75:
            arm_position = "Closed Arms"
        else:
            arm_position = "Partially Open"

        if abs(body_lean_x) > 0.05:
            posture = "Leaning"
        elif shoulder_y_diff > 0.03:
            posture = "Stiff"
        else:
            posture = "Upright"

        return {
            "eye_shoulder_y_ratio": eye_shoulder_y_ratio,
            "shoulder_y_diff": shoulder_y_diff,
            "wrist_distance_x": wrist_distance_x,
            "wrist_shoulder_ratio": wrist_shoulder_ratio,
            "nose_eye_center_offset_x": nose_eye_center_offset_x,
            "shoulder_span": shoulder_span,
            "hip_shoulder_y_diff": hip_shoulder_y_diff,
            "body_lean_x": body_lean_x,
            "shoulder_center_x": shoulder_center_x,
            "hip_center_x": hip_center_x,
            "spine_angle": spine_angle,
            "eye_distance": eye_distance,
            "head_tilt_angle": head_tilt_angle,
            "eye_distance_ratio": eye_distance_ratio,
            "shoulder_slope": shoulder_slope,
            "head_direction": head_direction,
            "arm_position": arm_position,
            "posture": posture,
        }
    except Exception as e:
        print(f"[ERROR] compute_posture_features failed: {e}")
        traceback.print_exc()
        return None


def preprocess_posture_features(raw_feat):
    numeric = np.array([raw_feat[col] for col in NUMERIC_POSTURE_COLS], dtype=np.float32).reshape(1, -1)
    head_oh = np.array(one_hot(raw_feat["head_direction"], HEAD_CLASSES), dtype=np.float32).reshape(1, -1)
    arm_oh = np.array(one_hot(raw_feat["arm_position"], ARM_CLASSES), dtype=np.float32).reshape(1, -1)
    posture_oh = np.array(one_hot(raw_feat["posture"], POSTURE_CLASSES), dtype=np.float32).reshape(1, -1)

    if hasattr(models_loaded.get("scaler"), "n_features_in_") and models_loaded["scaler"].n_features_in_ == 15:
        numeric_scaled = models_loaded["scaler"].transform(numeric)
        final_vec = np.concatenate([numeric_scaled, head_oh, arm_oh, posture_oh], axis=1)
    else:
        full_vec = np.concatenate([numeric, head_oh, arm_oh, posture_oh], axis=1)
        if models_loaded.get("scaler") is not None:
            final_vec = models_loaded["scaler"].transform(full_vec)
        else:
            final_vec = full_vec

    return final_vec.astype(np.float32)


def convert_audio_to_wav(source_path, wav_path):
    """Convert an uploaded audio file to a mono WAV file."""
    audio_segment_module = importlib.import_module("pydub")
    audio = audio_segment_module.AudioSegment.from_file(source_path)
    audio = audio.set_channels(1).set_frame_rate(22050)
    audio.export(wav_path, format="wav")
    return wav_path

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
                models_loaded['confidence_model'] = joblib.load(confidence_path)
                print("[OK] Confidence model loaded")
            else:
                print("[!] Confidence model not found - posture detection will use landmarks only")
        except Exception as e:
            print(f"[!] Confidence model loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load label encoder
        try:
            encoder_path = find_model_path("models/posturedata/label_encoder.pkl")
            if encoder_path:
                models_loaded['label_encoder'] = joblib.load(encoder_path)
                print("[OK] Label encoder loaded")
            else:
                print("[!] Label encoder not found")
        except Exception as e:
            print(f"[!] Label encoder loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load scaler
        try:
            scaler_path = find_model_path("models/posturedata/scaler.pkl")
            if scaler_path:
                models_loaded['scaler'] = joblib.load(scaler_path)
                print("[OK] Scaler loaded")
            else:
                print("[!] Scaler not found")
        except Exception as e:
            print(f"[!] Scaler loading skipped (corrupted or missing): {str(e)[:50]}")
        
        # Load voice emotion model
        try:
            if os.path.exists(VOICE_EMOTION_MODEL_PATH):
                models_loaded['voice_emotion'] = load_model(VOICE_EMOTION_MODEL_PATH)
                print(f"[OK] Voice emotion model loaded from {VOICE_EMOTION_MODEL_PATH}")
            else:
                print(f"[!] Voice emotion model not found at {VOICE_EMOTION_MODEL_PATH}")
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

        import subprocess, json, sys
        script = os.path.join(BASE_DIR, "pitch_generator.py")
        result = subprocess.run(
            [sys.executable, script, company, industry, description],
            capture_output=True, text=True, timeout=600,
            cwd=BASE_DIR
        )
        
        print("[PitchGen stderr]", result.stderr[-1000:])
        print("[PitchGen stdout]", result.stdout[:500])
        
        if result.returncode != 0:
            return jsonify({'error': result.stderr[-500:]}), 500

        # Trouve le JSON dans stdout (ignore les warnings avant)
        stdout = result.stdout.strip()
        json_start = stdout.rfind('{')
        json_end = stdout.rfind('}') + 1
        if json_start == -1:
            return jsonify({'error': 'No JSON in output', 'raw': stdout[:300]}), 500
        
        slides = json.loads(stdout[json_start:json_end])
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
        
        face = find_best_face(gray)

        if face is None:
            return {"emotion": "no_face", "confidence": 0.0, "face_detected": False}
        
        # Get largest face candidate
        x, y, w, h = face
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
            "face_detected": True,
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
        
        face = find_best_face(gray)

        if face is None:
            return {"stress": "unknown", "confidence": 0.0}
        
        # Get largest face candidate
        x, y, w, h = face
        face_gray = gray[y:y+h, x:x+w]
        
        # Preprocess and predict
        preprocessed = preprocess_face(face_gray)
        if preprocessed is None:
            return {"error": "Preprocessing failed"}
        
        preds = models_loaded['stress'].predict(preprocessed, verbose=0)[0]
        
        if len(preds) == 1:
            stress_prob = float(preds[0])
            label = "stressed" if stress_prob >= 0.5 else "not stressed"
            confidence = stress_prob if label == "stressed" else 1 - stress_prob
        else:
            stress_idx = int(np.argmax(preds))
            label = "stressed" if STRESS_LABELS[stress_idx] == "stress" else "not stressed"
            confidence = float(preds[stress_idx])
        
        return {
            "stress": label,
            "confidence": confidence,
            "face_detected": True,
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
            return {"posture": "unknown", "confidence": 0.0, "arm_position": "unknown", "head_direction": "unknown"}
        
        # Extract landmarks
        landmarks = detection_result.pose_landmarks[0]

        raw_feat = compute_posture_features(landmarks)
        if raw_feat is None:
            return {"posture": "unknown", "confidence": 0.0, "arm_position": "unknown", "head_direction": "unknown", "landmarks_count": len(landmarks)}

        confidence = 0.0
        posture_label = raw_feat["posture"]

        if models_loaded['confidence_model'] is not None:
            try:
                feat_vec = preprocess_posture_features(raw_feat)
                if hasattr(models_loaded['confidence_model'], 'predict_proba'):
                    probs = models_loaded['confidence_model'].predict_proba(feat_vec)[0]
                    prediction = int(np.argmax(probs))
                    confidence = float(np.max(probs))
                else:
                    prediction = int(models_loaded['confidence_model'].predict(feat_vec)[0])
                    confidence = 0.85

                if models_loaded['label_encoder'] is not None:
                    posture_label = models_loaded['label_encoder'].inverse_transform([prediction])[0]
                else:
                    posture_label = str(prediction)
            except Exception as model_error:
                print(f"[WARN] Posture classifier fallback used: {model_error}")
                confidence = 0.0

        return {
            "posture": posture_label,
            "confidence": confidence,
            "arm_position": raw_feat["arm_position"],
            "head_direction": raw_feat["head_direction"],
            "landmarks_count": len(landmarks),
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
        
        # Build a 3-channel spectrogram image that matches the model input shape (128x128x3)
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, n_fft=2048, hop_length=512)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # Normalize and create 3 channels: base mel, delta, delta-delta
        mel_norm = (mel_spec_db - np.mean(mel_spec_db)) / (np.std(mel_spec_db) + 1e-8)
        delta = librosa.feature.delta(mel_norm)
        delta2 = librosa.feature.delta(mel_norm, order=2)

        spectrogram = np.stack([mel_norm, delta, delta2], axis=-1)
        spectrogram = cv2.resize(spectrogram.astype(np.float32), (128, 128), interpolation=cv2.INTER_AREA)
        mel_spec_input = np.expand_dims(spectrogram, axis=0)

        expected_shape = models_loaded['voice_emotion'].input_shape
        print(f"[VoiceEmotion] input shape={mel_spec_input.shape}, model expects={expected_shape}")
        
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
        if request.content_type and request.content_type.startswith('multipart'):
            if 'file' not in request.files:
                return jsonify({"error": "No audio received"}), 400

            uploaded_file = request.files['file']
            raw_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
            wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            uploaded_file.save(raw_tmp.name)

            convert_audio_to_wav(raw_tmp.name, wav_tmp.name)

            if os.path.getsize(wav_tmp.name) < 1000:
                return jsonify({
                    "emotion": "no audio",
                    "confidence": 0,
                    "scores": {}
                })

            with open(wav_tmp.name, 'rb') as f:
                audio_payload = base64.b64encode(f.read()).decode('utf-8')
            result = detect_voice_emotion(audio_payload)
        else:
            data = request.json or {}
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
            raw_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
            wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            f.save(raw_tmp.name)

            convert_audio_to_wav(raw_tmp.name, wav_tmp.name)
            audio_path = wav_tmp.name
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
        bad_words = detect_bad_words(transcript or "")

        return jsonify({
            'transcript': transcript,
            'prediction': prediction,
            'bad_words': bad_words,
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
