# Pitch Analyzer Backend

## Installation

### 1. Créer un environnement virtuel
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Copier les modèles ML
Copie les fichiers modèles suivants dans le dossier `backend/models/`:
- `emotion_model.h5`
- `best_final_stress_cnn_73.h5`
- `best_cnn2d_v2.keras`
- `pose_landmarker.task`

## Lancer le serveur

```bash
python app.py
```

Le serveur démarre sur `http://localhost:5000`

## Endpoints disponibles

### 1. Health Check
```
GET /api/health
```

Réponse:
```json
{
  "status": "ok",
  "models_loaded": {
    "emotion": true,
    "stress": true
  }
}
```

### 2. Analyser l'émotion
```
POST /api/analyze/emotion
```

Body:
```json
{
  "frame": "data:image/jpeg;base64,..."
}
```

Réponse:
```json
{
  "emotion": "happy",
  "confidence": 0.95,
  "scores": {
    "angry": 0.01,
    "disgust": 0.01,
    "fear": 0.01,
    "happy": 0.95,
    "neutral": 0.01,
    "sad": 0.01,
    "surprise": 0.01
  }
}
```

### 3. Analyser le stress
```
POST /api/analyze/stress
```

Body:
```json
{
  "frame": "data:image/jpeg;base64,..."
}
```

Réponse:
```json
{
  "stress": "calm",
  "confidence": 0.87
}
```

## Configuration CORS

Le serveur accepte les requêtes du frontend (localhost:3000) via CORS.

## Structure des fichiers

```
backend/
├── app.py                 # API Flask principale
├── requirements.txt       # Dépendances Python
├── models/               # Dossier pour les modèles ML
│   ├── emotion_model.h5
│   ├── best_final_stress_cnn_73.h5
│   ├── best_cnn2d_v2.keras
│   └── pose_landmarker.task
└── README.md            # Ce fichier
```

## Notes

- Les modèles doivent être en format TensorFlow/Keras (.h5 ou .keras)
- La détection de visages utilise Haar Cascade de OpenCV
- Le port par défaut est 5000 (configurable dans app.py)
