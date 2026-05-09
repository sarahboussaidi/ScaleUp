# 🎤 Pitch Analyzer Pro - Guide Complet

Bienvenue dans **Pitch Analyzer Pro**, un système complet d'analyse de présentations avec IA en temps réel !

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Installation rapide](#installation-rapide)
3. [Utilisation](#utilisation)
4. [Architecture](#architecture)
5. [Dépannage](#dépannage)

## 🎯 Vue d'ensemble

**Pitch Analyzer Pro** combine votre frontend Next.js avec un backend Flask pour offrir :

- **Analyse d'émotion en temps réel** → Détecte les émotions faciales (happy, sad, angry, etc.)
- **Détection de stress** → Identifie le niveau de stress basé sur les expressions faciales
- **Historique d'analyse** → Garde une trace de toutes les analyses
- **Interface moderne** → Intégrée dans le design ScaleUp avec des gradients glassmorphisme

## ⚡ Installation rapide

### 1️⃣ Frontend (déjà prêt!)

Le frontend est installé. Vérifiez que le serveur fonctionne:

```bash
# Terminal 1
cd c:\Users\SOUFIEN\OneDrive\Documents\GitHub\ScaleUp
pnpm dev
```

✅ Frontend sur `http://localhost:3000`

### 2️⃣ Backend (à configurer)

**Étape 1: Configurer l'environnement Python**

```bash
# Terminal 2
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Étape 2: Copier les modèles ML**

Copie ces fichiers de `C:\Users\SOUFIEN\OneDrive\Documents\pitch_analyzer` vers `backend/models/`:

```bash
# PowerShell
Copy-Item "..\pitch_analyzer\emotion_model.h5" "backend\models\"
Copy-Item "..\pitch_analyzer\best_final_stress_cnn_73.h5" "backend\models\"
Copy-Item "..\pitch_analyzer\best_cnn2d_v2.keras" "backend\models\"
Copy-Item "..\pitch_analyzer\pose_landmarker.task" "backend\models\"
```

**Étape 3: Lancer le backend**

```bash
# Terminal 2 (toujours)
python app.py
```

✅ Backend sur `http://localhost:5000`

### 3️⃣ Accéder à l'application

1. Ouvrir `http://localhost:3000` dans votre navigateur
2. Naviguer vers **Presentation** → **Live Analysis**
3. Cliquer sur **Start Camera**
4. Cliquer sur **Analyze All** pour commencer !

## 🎮 Utilisation

### Interface principale

```
┌─────────────────────────────────────────────┐
│  🎤 Pitch Analyzer Pro                       │
│  Real-time emotion & stress detection       │
├─────────────────────────────────────────────┤
│ ┌─ Video Feed ──────────────────────────┐   │
│ │ (Votre caméra en direct)              │   │
│ │ [Start Camera] [Stop Camera]           │   │
│ └───────────────────────────────────────┘   │
│ ┌─ Real-time Analysis ──────────────────┐   │
│ │ [Analyze Emotion] [Analyze Stress]    │   │
│ │ [Analyze All]                         │   │
│ └───────────────────────────────────────┘   │
│ ┌─ Emotion Results ──────────────────────┐  │
│ │ Happy (95%)                           │   │
│ │ ▐▌▐▌▐▌ angry      ▐▌ happy          │   │
│ └───────────────────────────────────────┘   │
│ ┌─ Stress Results ──────────────────────┐   │
│ │ ✓ Calm (87%)                         │   │
│ │ ▐▌▐▌▐▌▐▌▐ Stress Level              │   │
│ └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Étapes d'utilisation

1. **Activer la caméra**
   - Cliquer sur "Start Camera"
   - Accorder les permissions au navigateur

2. **Analyser une émotion**
   - Faire une expression faciale
   - Cliquer "Analyze Emotion"
   - Attendre le résultat

3. **Analyser le stress**
   - Faire différentes expressions
   - Cliquer "Analyze Stress"
   - Voir le niveau de stress détecté

4. **Voir l'historique**
   - Cliquer sur l'onglet "History"
   - Voir tous les résultats précédents

## 🏗️ Architecture

### Structure des dossiers

```
ScaleUp/
├── app/
│   └── presentation/
│       └── page.tsx                    # Page principale
├── components/
│   └── pitch-analyzer-section.tsx      # Composant d'analyse
├── lib/
│   └── pitch-analyzer-config.ts        # Config API centralisée
├── backend/                            # 🆕 Backend Flask
│   ├── app.py                          # API principal
│   ├── requirements.txt                # Dépendances Python
│   ├── models/                         # 🆕 Modèles ML
│   │   ├── emotion_model.h5
│   │   ├── best_final_stress_cnn_73.h5
│   │   ├── best_cnn2d_v2.keras
│   │   └── pose_landmarker.task
│   └── README.md
├── .env.local                          # 🆕 Variables d'env
└── SETUP.md                            # 🆕 Guide d'installation
```

### Flux de données

```
┌─────────────────┐
│  Navigation     │
│  avec caméra    │
└────────┬────────┘
         │ Capture frame
         ▼
┌─────────────────────────────┐
│  React Component             │
│  (pitch-analyzer-section)    │
├─────────────────────────────┤
│ - Capture vidéo             │
│ - Envoie frame en base64    │
└────────┬────────────────────┘
         │ HTTP POST
         ▼
┌─────────────────────────────┐
│  Flask Backend (Python)      │
│  (backend/app.py)           │
├─────────────────────────────┤
│ - Détection visage (Haar)   │
│ - Analyse émotion (TF)      │
│ - Analyse stress (TF)       │
└────────┬────────────────────┘
         │ JSON Response
         ▼
┌─────────────────────────────┐
│  React affiche les résultats │
│ - Graphiques                 │
│ - Scores de confiance       │
│ - Historique                │
└─────────────────────────────┘
```

### Modèles ML utilisés

| Modèle | Tâche | Entrée | Sortie |
|--------|-------|--------|--------|
| `emotion_model.h5` | Classification d'émotions | Image 48x48 grayscale | 7 classes (angry, happy, sad, etc.) |
| `best_final_stress_cnn_73.h5` | Détection de stress | Image 48x48 grayscale | 2 classes (stressed/calm) |
| `best_cnn2d_v2.keras` | Analyse vocale | Spectrogramme audio | 8 classes d'émotions |
| `pose_landmarker.task` | Détection de posture | Vidéo en temps réel | 33 landmarks du corps |

## 🐛 Dépannage

### ❌ "Backend Not Connected"

**Cause:** Le serveur Flask n'est pas en cours d'exécution

**Solution:**
```bash
cd backend
venv\Scripts\activate
python app.py
```

Vérifier: `http://localhost:5000/api/health` → `{"status": "ok"}`

### ❌ "Failed to analyze emotion"

**Cause 1:** Pas de visage détecté
- Solution: S'assurer que votre visage est bien visible et éclairé

**Cause 2:** Les modèles ne sont pas chargés
- Solution: Vérifier que les fichiers `.h5` sont dans `backend/models/`
- Regarder les logs Flask pour les erreurs spécifiques

### ❌ La caméra ne s'active pas

**Solution:**
1. Donner les permissions au navigateur
2. Essayer un autre navigateur
3. Vérifier: `Chrome/Firefox > Settings > Privacy > Camera`

### ❌ CORS Error

**Cause:** Le backend CORS n'est pas configuré correctement

**Solution:** S'assurer que `Flask-CORS` est installé:
```bash
pip install flask-cors --upgrade
```

## 📊 Variables d'environnement

### `.env.local`
```
NEXT_PUBLIC_PITCH_API_URL=http://localhost:5000
```

### `backend/app.py` (modifiable)
```python
app.run(
    host='0.0.0.0',      # Tous les interfaces
    port=5000,            # Port Flask
    debug=True            # Mode debug
)
```

## 🚀 Prochaines étapes

1. **Entraîner des modèles personnalisés**
   - Utiliser votre propre dataset d'émotions
   - Exporter en format `.h5` ou `.keras`

2. **Ajouter l'analyse vocale**
   - Intégrer `speech_module.py` du pitch_analyzer original
   - Analyser le ton et les émotions vocales

3. **Générer des rapports**
   - Exporter l'historique en PDF
   - Créer des graphiques d'évolution

4. **Intégration cloud**
   - Déployer le backend sur AWS/Heroku
   - Utiliser le frontend sur Vercel

## 📞 Support

Besoin d'aide ?

1. Vérifier les logs:
   - Frontend: Console du navigateur (F12)
   - Backend: Terminal avec les logs Flask

2. Vérifier la health:
   ```bash
   curl http://localhost:5000/api/health
   ```

3. Consulter les fichiers README:
   - `SETUP.md` - Installation complète
   - `backend/README.md` - Guide backend
   - `lib/pitch-analyzer-config.ts` - Config API

---

**Bonne analyse ! 🎤✨**
