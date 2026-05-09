# 🚀 ScaleUp - Pitch Analyzer Pro Edition

> **AI-Powered Presentation Analysis Platform**  
> Analyse en temps réel des émotions et du stress pendant vos présentations

---

## 🎯 À propos

**ScaleUp** est une plateforme de coaching de présentation alimentée par l'IA. Elle combine un **frontend React moderne** avec un **backend Python ML** pour offrir une analyse en temps réel de vos compétences de présentation.

### Fonctionnalités principales

✅ **Analyse d'émotion en direct** - Détecte les émotions faciales (happy, sad, angry, etc.)  
✅ **Détection de stress** - Identifie le niveau de stress basé sur les expressions  
✅ **Historique d'analyse** - Garde une trace de tous les enregistrements  
✅ **Interface moderne** - Design glassmorphisme avec animations fluides  
✅ **API REST** - Backend scalable et extensible

---

## 🛠️ Stack technologique

### Frontend
- **Next.js 14** - Framework React moderne
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide Icons** - Icônes modernes
- **Framer Motion** - Animations

### Backend
- **Flask** - Framework web Python
- **TensorFlow/Keras** - ML models
- **OpenCV** - Vision par ordinateur
- **MediaPipe** - Détection de poses
- **NumPy** - Calculs numériques

### Infrastructure
- **pnpm** - Package manager (frontend)
- **pip** - Package manager (backend)
- **CORS** - Cross-origin requests
- **REST API** - Communication

---

## ⚡ Démarrage rapide

### Option 1: Script automatique (recommandé)

**Windows:**
```bash
START.bat
```

**macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manuel

**Terminal 1 - Frontend:**
```bash
pnpm dev
```

**Terminal 2 - Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # ou: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Puis ouvrir: **http://localhost:3000/presentation**

---

## 📖 Documentation complète

| Document | Description |
|----------|-------------|
| [`SETUP.md`](./SETUP.md) | 🔧 Installation et configuration détaillées |
| [`PITCH_ANALYZER_GUIDE.md`](./PITCH_ANALYZER_GUIDE.md) | 📖 Guide complet d'utilisation |
| [`INTEGRATION_SUMMARY.md`](./INTEGRATION_SUMMARY.md) | 📋 Résumé de l'intégration |
| [`backend/README.md`](./backend/README.md) | 🎯 Documentation API backend |

---

## 🎮 Utilisation

### 1. Démarrer la caméra
Cliquer sur **"Start Camera"** pour activer votre webcam

### 2. Analyser les émotions
Cliquer sur **"Analyze Emotion"** pour détecter les émotions faciales

### 3. Analyser le stress
Cliquer sur **"Analyze Stress"** pour évaluer le niveau de stress

### 4. Voir l'historique
L'onglet **"History"** garde la trace de toutes les analyses

---

## 🏗️ Architecture

```
┌────────────────────────────────┐
│    Frontend (localhost:3000)    │
│  - React Components            │
│  - Video capture               │
│  - Real-time UI                │
└───────────────┬────────────────┘
                │ HTTP POST (JSON)
                │ base64 frames
                ▼
┌────────────────────────────────┐
│    Backend (localhost:5000)     │
│  - Flask API                   │
│  - Face detection              │
│  - ML inference                │
│  - Response JSON               │
└────────────────────────────────┘
```

---

## 📁 Structure du projet

```
ScaleUp/
├── START.bat                       # Quick start Windows
├── start.sh                        # Quick start macOS/Linux
├── SETUP.md                        # Installation guide
├── PITCH_ANALYZER_GUIDE.md         # User guide
├── INTEGRATION_SUMMARY.md          # Integration summary
│
├── app/
│   ├── presentation/
│   │   └── page.tsx               # Presentation page (+ analyzer)
│   └── ...
│
├── components/
│   ├── pitch-analyzer-section.tsx  # Analyzer UI component
│   └── ...
│
├── lib/
│   ├── pitch-analyzer-config.ts    # API config
│   └── utils.ts
│
├── backend/
│   ├── app.py                      # Flask API
│   ├── requirements.txt            # Python dependencies
│   ├── README.md                   # Backend docs
│   └── models/                     # ML models folder
│       ├── emotion_model.h5        # (à ajouter)
│       ├── best_final_stress_cnn_73.h5
│       ├── best_cnn2d_v2.keras
│       └── pose_landmarker.task
│
└── .env.local                      # Environment variables
```

---

## 🔧 Configuration

### Frontend (.env.local)
```env
NEXT_PUBLIC_PITCH_API_URL=http://localhost:5000
```

### Backend (backend/app.py)
```python
app.run(
    host='0.0.0.0',
    port=5000,
    debug=True
)
```

---

## 📊 API Endpoints

### Health Check
```
GET /api/health
Response: {"status": "ok", "models_loaded": {...}}
```

### Analyze Emotion
```
POST /api/analyze/emotion
Body: {"frame": "data:image/jpeg;base64,..."}
Response: {"emotion": "happy", "confidence": 0.95, "scores": {...}}
```

### Analyze Stress
```
POST /api/analyze/stress
Body: {"frame": "data:image/jpeg;base64,..."}
Response: {"stress": "calm", "confidence": 0.87}
```

---

## 🐛 Dépannage

### ❌ "Backend Not Connected"
```bash
# S'assurer que Flask fonctionne
cd backend
python app.py
```

### ❌ Modèles ML manquants
```bash
# Copier les modèles depuis pitch_analyzer
Copy-Item "..\pitch_analyzer\*.h5" "backend\models\"
Copy-Item "..\pitch_analyzer\*.keras" "backend\models\"
```

### ❌ Erreur CORS
```bash
# Vérifier que flask-cors est installé
pip install flask-cors --upgrade
```

### ❌ Pas de détection de visage
- Assurer un éclairage adéquat
- Positionner le visage au centre
- Vérifier que la caméra fonctionne

---

## 🚀 Prochaines étapes

### Court terme
- [ ] Intégrer l'analyse vocale
- [ ] Ajouter la détection de posture
- [ ] Créer un dashboard de statistiques
- [ ] Exporter les résultats en PDF/CSV

### Moyen terme
- [ ] Entraîner des modèles personnalisés
- [ ] Ajouter l'authentification
- [ ] Créer une base de données
- [ ] Implémenter le stockage cloud

### Long terme
- [ ] Déployer sur cloud (Vercel + Heroku)
- [ ] Ajouter des webhooks
- [ ] Créer une API publique
- [ ] Développer une app mobile

---

## 📞 Support et documentation

- 📚 **Docs:** Consulter les fichiers markdown (SETUP.md, PITCH_ANALYZER_GUIDE.md)
- 🐛 **Debug:** Vérifier les logs du navigateur (F12) et du terminal
- ✅ **Health:** Vérifier `http://localhost:5000/api/health`

---

## 📝 License

Projet ScaleUp - Tous droits réservés

---

## 👨‍💻 Développé avec ❤️

**Intégration Pitch Analyzer Pro**
- Frontend: React 19 + Next.js 14
- Backend: Flask + TensorFlow
- Architecture: Microservices avec REST API
- Design: Glassmorphism + Animations

---

**Prêt à démarrer ?** 🚀

```bash
# Windows
START.bat

# macOS/Linux
./start.sh
```

**Puis accédez à:** http://localhost:3000/presentation

---

**Bon coding ! ✨**
