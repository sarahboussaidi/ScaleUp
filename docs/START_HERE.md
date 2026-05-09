# 🎯 COMMENCEZ ICI

> **Bienvenue dans Pitch Analyzer Pro!** 🚀  
> Voici comment démarrer en 3 étapes simples.

---

## 📍 Vous êtes ici

Vous avez juste cloné/téléchargé le projet **ScaleUp** avec l'intégration **Pitch Analyzer Pro**.

---

## ⚡ Démarrage ultra-rapide (3 minutes)

### Prérequis (vérifier rapidement)

```bash
# Terminal quelconque
node --version     # ✓ Doit afficher v18.0.0 ou plus
python --version   # ✓ Doit afficher 3.8 ou plus
pnpm --version     # ✓ Doit afficher 8.0.0 ou plus
```

Si quelque chose manque: voir la section **Dépannage** ci-bas.

### 1️⃣ Copier les modèles ML (1 minute)

**Copier ces 4 fichiers** de `C:\Users\SOUFIEN\OneDrive\Documents\pitch_analyzer` vers `backend/models/`:

```
emotion_model.h5
best_final_stress_cnn_73.h5
best_cnn2d_v2.keras
pose_landmarker.task
```

**Windows (PowerShell):**
```powershell
cd ScaleUp
Copy-Item "..\pitch_analyzer\emotion_model.h5" "backend\models\"
Copy-Item "..\pitch_analyzer\best_final_stress_cnn_73.h5" "backend\models\"
Copy-Item "..\pitch_analyzer\best_cnn2d_v2.keras" "backend\models\"
Copy-Item "..\pitch_analyzer\pose_landmarker.task" "backend\models\"
```

**macOS/Linux (bash):**
```bash
cd ScaleUp
cp ../pitch_analyzer/emotion_model.h5 backend/models/
cp ../pitch_analyzer/best_final_stress_cnn_73.h5 backend/models/
cp ../pitch_analyzer/best_cnn2d_v2.keras backend/models/
cp ../pitch_analyzer/pose_landmarker.task backend/models/
```

✓ Fichiers copiés? Continuez!

### 2️⃣ Lancer les services (1 minute)

**Windows:**
```bash
START.bat
```

**macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

Deux terminaux vont s'ouvrir automatiquement:
- ✓ Frontend: `http://localhost:3000`
- ✓ Backend: `http://localhost:5000`

Puis le navigateur ouvre automatiquement la page.

### 3️⃣ Utiliser l'app (1 minute)

Vous êtes sur `http://localhost:3000/presentation`

1. Cliquer **"Start Camera"** → autoriser la caméra
2. Cliquer **"Analyze All"** → voir les résultats
3. Voir l'historique dans l'onglet **"History"**

---

## 🎉 C'est prêt!

Vous devriez voir:
- ✅ Une vidéo en direct de votre caméra
- ✅ Un bouton "Analyze Emotion"
- ✅ Un bouton "Analyze Stress"
- ✅ Un indicateur "Backend Connected" (vert)

---

## 📚 Voir la documentation

| Si vous voulez... | Lire |
|------------------|------|
| Installation détaillée | [`SETUP.md`](SETUP.md) |
| Comment utiliser | [`PITCH_ANALYZER_GUIDE.md`](PITCH_ANALYZER_GUIDE.md) |
| Résumé technique | [`INTEGRATION_SUMMARY.md`](INTEGRATION_SUMMARY.md) |
| Checklist complète | [`CHECKLIST.md`](CHECKLIST.md) |
| API Backend | [`backend/README.md`](backend/README.md) |

---

## 🆘 Dépannage rapide

### ❌ "Backend Not Connected" (rouge)

**Le serveur Flask n'a pas démarré**

```bash
cd backend
python app.py
```

Attendez: `Running on http://0.0.0.0:5000`

### ❌ Caméra "Could not capture frame"

**Autoriser la caméra:**
1. Chrome/Firefox → Settings → Privacy → Camera → Allow
2. Recharger la page
3. Essayer un autre navigateur

### ❌ "python not found"

**Installer Python:**
1. Télécharger: https://www.python.org/downloads/
2. Pendant l'installation: ☑️ Cocher "Add Python to PATH"
3. Redémarrer le terminal

### ❌ "pnpm not found"

```bash
npm install -g pnpm
```

### ❌ Les modèles ne se chargent pas

```bash
# Vérifier que les fichiers sont présents
dir backend\models

# Doit afficher:
# - emotion_model.h5
# - best_final_stress_cnn_73.h5
# - best_cnn2d_v2.keras
# - pose_landmarker.task
```

Si manquants → les copier (voir Étape 1)

---

## 🚀 Ce qui fonctionne maintenant

✅ Détection d'émotion en temps réel  
✅ Détection de stress en temps réel  
✅ Historique des analyses  
✅ Interface moderne et responsive  
✅ API REST backend scalable  

---

## 💡 Astuces

- **Performance:** Si lent, vérifier l'éclairage
- **Meilleure détection:** S'assurer que le visage est bien centré
- **Debug:** Ouvrir la console (F12) pour voir les erreurs
- **Santé:** Vérifier `http://localhost:5000/api/health`

---

## 🎓 Ensuite ?

Une fois fonctionnel, vous pouvez:

1. **Intégrer l'analyse vocale** → Décommenter le code speech_module.py
2. **Entraîner des modèles personnalisés** → Utiliser vos données
3. **Ajouter une base de données** → Sauvegarder les résultats
4. **Déployer sur cloud** → Heroku (backend) + Vercel (frontend)
5. **Créer une app mobile** → React Native

---

## 📞 Questions ?

Consulter les fichiers markdown:
- `SETUP.md` - Installation complète
- `PITCH_ANALYZER_GUIDE.md` - Guide utilisateur
- `INTEGRATION_SUMMARY.md` - Vue d'ensemble technique

---

## 🎯 Votre prochaine action

### Maintenant:

```bash
# Windows
START.bat

# macOS/Linux
./start.sh
```

### Puis:

Ouvrir: **http://localhost:3000/presentation**

---

**C'est bon ? Prêt à analyser vos présentations ! 🎤✨**

---

*Note: Si quelque chose ne fonctionne pas, consulter `CHECKLIST.md` pour chaque étape.*
