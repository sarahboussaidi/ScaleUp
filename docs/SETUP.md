# Installation & Setup Guide

## Frontend Setup (Next.js)

Le frontend est déjà configuré et prêt ! Les dépendances sont installées.

### Vérifier que le serveur fonctionne

```bash
# Terminal 1 - Frontend Next.js
pnpm dev
```

Le frontend se lance sur `http://localhost:3000`

## Backend Setup (Flask - Pitch Analyzer)

### 1. Naviguer au dossier backend
```bash
cd backend
```

### 2. Créer un environnement virtuel
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Ajouter les modèles ML
Copier les fichiers modèles du dossier `pitch_analyzer` vers `backend/models/`:
- `emotion_model.h5`
- `best_final_stress_cnn_73.h5`
- `best_cnn2d_v2.keras`
- `pose_landmarker.task`

Commandes pour copier (depuis le dossier du projet):

**Windows (PowerShell):**
```powershell
Copy-Item "C:\Users\SOUFIEN\OneDrive\Documents\pitch_analyzer\emotion_model.h5" "backend\models\"
Copy-Item "C:\Users\SOUFIEN\OneDrive\Documents\pitch_analyzer\best_final_stress_cnn_73.h5" "backend\models\"
Copy-Item "C:\Users\SOUFIEN\OneDrive\Documents\pitch_analyzer\best_cnn2d_v2.keras" "backend\models\"
Copy-Item "C:\Users\SOUFIEN\OneDrive\Documents\pitch_analyzer\pose_landmarker.task" "backend\models\"
```

**Linux/macOS (bash):**
```bash
cp ~/OneDrive/Documents/pitch_analyzer/emotion_model.h5 backend/models/
cp ~/OneDrive/Documents/pitch_analyzer/best_final_stress_cnn_73.h5 backend/models/
cp ~/OneDrive/Documents/pitch_analyzer/best_cnn2d_v2.keras backend/models/
cp ~/OneDrive/Documents/pitch_analyzer/pose_landmarker.task backend/models/
```

### 5. Lancer le serveur Flask
```bash
# Terminal 2 - Backend Flask
python app.py
```

Le backend se lance sur `http://localhost:5000`

## Utilisation complète

Ouvrez **deux terminaux**:

**Terminal 1:**
```bash
# Frontend
pnpm dev
```

**Terminal 2:**
```bash
# Backend
cd backend
venv\Scripts\activate  # ou: source venv/bin/activate
python app.py
```

Puis ouvrez votre navigateur sur `http://localhost:3000` et naviguez vers la page `/presentation`

## Architecture

```
ScaleUp/
├── app/
│   ├── presentation/
│   │   └── page.tsx          # Page principale
│   └── ...
├── components/
│   ├── pitch-analyzer-section.tsx    # Composant d'analyse
│   └── ...
├── lib/
│   └── pitch-analyzer-config.ts      # Configuration API
├── backend/
│   ├── app.py                # API Flask
│   ├── requirements.txt       # Dépendances Python
│   ├── models/              # Dossier modèles ML
│   └── README.md            # Docs backend
└── .env.local               # Variables d'environnement
```

## Structure de la communication

1. **Frontend (Next.js)** → Capture vidéo/frame
2. → Envoie le frame en base64 vers le **Backend (Flask)**
3. **Backend** → Analyse avec les modèles ML
4. → Retourne les résultats (émotion, stress)
5. **Frontend** → Affiche les résultats en temps réel

## Variables d'environnement

### Frontend (.env.local)
```
NEXT_PUBLIC_PITCH_API_URL=http://localhost:5000
```

### Backend (app.py)
- Port: 5000 (modifiable ligne 272)
- Host: 0.0.0.0
- Debug: True

## Dépannage

### Le backend ne démarre pas
- Vérifier que Python 3.8+ est installé: `python --version`
- Vérifier l'activation de l'environnement virtuel
- Réinstaller les dépendances: `pip install -r requirements.txt --upgrade`

### Les modèles ne se chargent pas
- Vérifier que les fichiers .h5 sont dans `backend/models/`
- Vérifier les permissions de lecture
- Regarder les logs Flask pour les erreurs spécifiques

### Erreur CORS
- S'assurer que Flask démarre avec `CORS(app)`
- Vérifier que le URL frontend est `http://localhost:3000` (pas 127.0.0.1)

### La caméra ne fonctionne pas
- Donner les permissions à votre navigateur
- Récharger la page
- Essayer un autre navigateur

## Liens utiles

- [Documentation Next.js](https://nextjs.org/docs)
- [Documentation Flask](https://flask.palletsprojects.com/)
- [TensorFlow/Keras](https://www.tensorflow.org/)
- [MediaPipe](https://mediapipe.dev/)
