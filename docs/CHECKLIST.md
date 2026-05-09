# ✅ Checklist d'installation - Pitch Analyzer Pro

## 📋 Avant de commencer

- [ ] Vérifier que Node.js 18+ est installé: `node --version`
- [ ] Vérifier que Python 3.8+ est installé: `python --version`
- [ ] Vérifier que pnpm est installé: `pnpm --version` (sinon: `npm install -g pnpm`)

---

## 🎬 Étape 1: Configuration du Backend

### Créer l'environnement Python

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

- [ ] Environnement virtuel créé
- [ ] Environnement virtuel activé

### Installer les dépendances Python

```bash
pip install -r requirements.txt
```

- [ ] Dépendances installées avec succès

### Copier les modèles ML

**Depuis votre dossier pitch_analyzer vers backend/models/:**

```bash
# Windows PowerShell
Copy-Item "..\pitch_analyzer\emotion_model.h5" "models\"
Copy-Item "..\pitch_analyzer\best_final_stress_cnn_73.h5" "models\"
Copy-Item "..\pitch_analyzer\best_cnn2d_v2.keras" "models\"
Copy-Item "..\pitch_analyzer\pose_landmarker.task" "models\"

# macOS/Linux bash
cp ../pitch_analyzer/emotion_model.h5 models/
cp ../pitch_analyzer/best_final_stress_cnn_73.h5 models/
cp ../pitch_analyzer/best_cnn2d_v2.keras models/
cp ../pitch_analyzer/pose_landmarker.task models/
```

**Vérifier que les fichiers sont présents:**

```bash
ls -la models/
# ou
dir models
```

- [ ] `emotion_model.h5` ✓
- [ ] `best_final_stress_cnn_73.h5` ✓
- [ ] `best_cnn2d_v2.keras` ✓
- [ ] `pose_landmarker.task` ✓

---

## 🚀 Étape 2: Lancer les services

### Option A: Script automatique (recommandé)

**Windows:**
```bash
START.bat
```

**macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

- [ ] Script lancé avec succès
- [ ] Deux nouveaux terminaux se sont ouverts

### Option B: Manuel

**Terminal 1 - Frontend:**
```bash
pnpm dev
```

- [ ] Serveur Next.js démarré sur `http://localhost:3000`
- [ ] Message: "✓ Ready in Xs"

**Terminal 2 - Backend:**
```bash
cd backend
venv\Scripts\activate  # ou: source venv/bin/activate
python app.py
```

- [ ] Serveur Flask démarré sur `http://localhost:5000`
- [ ] Modèles chargés avec succès
- [ ] Message: "Running on http://0.0.0.0:5000"

---

## ✔️ Étape 3: Vérifications

### Vérifier la santé du backend

Ouvrir dans le navigateur:
```
http://localhost:5000/api/health
```

Réponse attendue:
```json
{"status": "ok", "models_loaded": {"emotion": true, "stress": true}}
```

- [ ] Réponse reçue
- [ ] Les deux modèles sont chargés

### Accéder à l'application

Ouvrir dans le navigateur:
```
http://localhost:3000/presentation
```

Vérifications:
- [ ] Page charge sans erreur
- [ ] Section "Pitch Analyzer Pro" visible
- [ ] Indicateur "Backend Connected" en vert

---

## 🎮 Étape 4: Test initial

### Vérifier la caméra

1. Cliquer sur **"Start Camera"**
2. Accorder les permissions au navigateur
3. Voir le flux vidéo en direct

- [ ] Caméra fonctionne ✓
- [ ] Vidéo affichée en direct ✓

### Tester l'analyse d'émotion

1. Faire une expression faciale
2. Cliquer sur **"Analyze Emotion"**
3. Attendre le résultat

- [ ] Émotion détectée ✓
- [ ] Score de confiance affiché ✓
- [ ] Graphique des scores visible ✓

### Tester l'analyse de stress

1. Faire une autre expression
2. Cliquer sur **"Analyze Stress"**
3. Voir le résultat

- [ ] Stress détecté ✓
- [ ] Niveau de stress affiché ✓

### Vérifier l'historique

1. Cliquer sur l'onglet **"History"**
2. Voir les analyses précédentes

- [ ] Historique affichées ✓

---

## 🐛 Dépannage rapide

### ❌ "Backend Not Connected"

**Cause:** Flask n'est pas en cours d'exécution

**Solution:**
```bash
cd backend
python app.py
```

- [ ] Backend redémarré

### ❌ Modèles non chargés

**Cause:** Fichiers .h5 manquants

**Solution:**
```bash
# Vérifier que les fichiers sont présents
ls backend/models/
```

- [ ] Tous les fichiers présents

### ❌ Erreur CORS

**Cause:** Flask CORS non configuré

**Solution:**
```bash
pip install flask-cors --upgrade
cd backend
python app.py
```

- [ ] Erreur CORS résolue

### ❌ Caméra ne fonctionne pas

**Cause:** Permissions navigateur

**Solution:**
1. Chrome/Firefox: Settings > Privacy > Camera > Allow
2. Recharger la page
3. Essayer un autre navigateur

- [ ] Caméra autorisée

### ❌ Python/pnpm non trouvé

**Cause:** Pas dans PATH

**Solution:**
1. Redémarrer le terminal
2. Vérifier installation: `python --version`
3. Réinstaller si nécessaire

- [ ] Python/pnpm trouvé

---

## 📚 Documentation

- [ ] **SETUP.md** - Lire pour plus de détails
- [ ] **PITCH_ANALYZER_GUIDE.md** - Guide complet d'utilisation
- [ ] **backend/README.md** - Documentation API
- [ ] **INTEGRATION_SUMMARY.md** - Résumé technique

---

## 🎉 Succès !

Si tous les points sont cochés, le système est opérationnel !

```
✅ Backend en cours d'exécution
✅ Frontend en cours d'exécution
✅ Modèles ML chargés
✅ Caméra fonctionne
✅ Analyse fonctionne
✅ Historique fonctionne
```

---

## 🚀 Prochaines étapes

1. Tester l'interface avec différentes expressions
2. Lire la documentation complète
3. Intégrer de nouvelles fonctionnalités
4. Entraîner des modèles personnalisés
5. Déployer sur cloud

---

## 💡 Astuces

- **Optimiser les performances:** Réduire la résolution vidéo
- **Améliorer la détection:** Augmenter l'éclairage
- **Déboguer:** Utiliser `http://localhost:5000/api/health` pour vérifier l'état
- **Logs:** Vérifier la console du navigateur (F12) et le terminal Flask

---

## 📞 Besoin d'aide ?

1. Vérifier la checklist ci-dessus
2. Consulter `SETUP.md` ou `PITCH_ANALYZER_GUIDE.md`
3. Vérifier les logs du terminal
4. Vérifier la console du navigateur (F12)

---

**Merci d'avoir choisi Pitch Analyzer Pro! 🎤✨**
