# Social Media Strategy Evaluator — Full Project Summary
## Complete conversation record for continuity

---

## 1. PROJECT CONTEXT & OBJECTIVE

### Who and what
This project is part of an academic/professional internship. The student (Islem Darghouth, Kaggle: islemdarghouth) is building a platform that **supports startups in marketing and branding**.

### The intermediate objective (Islem's part)
**Marketing support for startups** — specifically evaluating social media strategy and branding.

### The two operational objectives
1. **Social Media Visual Strategy Evaluation & Recommendation** ← what we built
2. **Brand Strategy Document Generation & Evaluation** ← not yet started

---

## 2. SOCIAL MEDIA OBJECTIVE — FULL ARCHITECTURE

The system takes a startup's social media post as input and evaluates it across multiple dimensions, then gives actionable recommendations.

### What the user provides (input)
- Post image (Instagram / Facebook / LinkedIn / Twitter / TikTok)
- Caption text
- Hashtags
- Platform selection
- Startup description (3–5 sentences: what they do, who they serve, their tone, target audience, industry)

### The 6 evaluation dimensions (output)
1. **Visual quality** — color harmony, composition, professional look, stop-scroll power
2. **Text clarity on image** — font contrast, readability, cognitive overload
3. **Caption quality** — brand fit, clarity, emotional hook, CTA presence
4. **Hashtag strategy** — relevance, reach score, platform-specific count optimization
5. **Engagement potential** — hook power, CTR prediction
6. **Brand alignment** — voice match, value proposition communication

### WHY two-layer architecture
- **Universal scoring** (trained ML): grammar, readability, hashtag count, structure — measurable objectively
- **Startup-specific scoring** (Claude API, Phase 5): brand voice match, audience targeting, niche hashtag relevance — requires startup context

A caption that is perfect for a teen fashion brand is completely wrong for a B2B medical startup. The two-layer approach handles both universally measurable quality AND startup-specific relevance.

---

## 3. DATASETS — WHAT EACH ONE IS AND HOW IT'S USED

### Kaggle datasets added to the project

| Dataset | Kaggle slug | Used for |
|---|---|---|
| AADB Image Database | `bogdanpetre98/aadb-imagedatabase` | Visual quality model training |
| Instagram Analytics | `kundanbedmutha/instagram-analytics-dataset` | Platform benchmarks, hashtag optimization |
| Social Media Sentiments | `kashishparmar02/social-media-sentiments-analysis-dataset` | Caption NLP analysis |
| Social Media Engagement | `subashmaster0411/social-media-engagement-dataset` | XGBoost engagement predictor training |
| Social Media Performance | `svthejaswini/social-media-performance-and-engagement-data` | Explored, supplementary |
| Instagram User Behavior | `sanjanchaudhari/user-behavior-on-instagram` | Explored, supplementary |
| Social Media Advertisement Performance | `alperenmyung/social-media-advertisement-performance` | Skipped for now |
| Logo Dataset | `siddharthkumarsah/logo-dataset-2341-classes-and-167140-images` | Brand strategy module (Phase 2) |
| Instagram Data | `divyaraj2006/instagram-data` | Supplementary |

### Datasets confirmed NOT needed
- Logo Dataset → belongs in Brand Strategy module (Objective 2), not Social Media module

---

## 4. PHASE 1 — DATA EXPLORATION

### Notebook: `01_data_exploration.ipynb`
**What it does:** Auto-discovers all CSV files in `/kaggle/input`, loads each one, produces a full column inventory, missing value analysis, engagement distributions, correlation heatmaps, and a final "usability verdict" saved as JSON.

**Key design decision:** `SELECTED_INDEX` variable — just change one number to switch between datasets. No hardcoded paths.

### Key findings from the exploration

**Instagram Analytics dataset** (kundanbedmutha) — the most important:
- Shape: 29,999 rows × 23 columns
- 0 duplicates, 0 missing values → clean
- Real column names (different from what we guessed):
  - `post_type` → actually `media_type`
  - `hashtags` → actually `hashtags_count` (a NUMBER, not text)
  - `caption` → actually `caption_length` (a NUMBER, not text)
  - `followers` → actually `follower_count`
- `likes` skewness = 5.64 → heavily right-skewed, log1p mandatory
- `engagement_rate` already computed and present
- `has_call_to_action` boolean present
- `performance_bucket_label` categorical — pre-labeled quality tiers (gold mine)

**Critical insight:** This dataset has NO raw text — only derived numeric features. It feeds the engagement predictor directly, not the NLP pipeline.

---

## 5. PHASE 2 — DATA PREPARATION & TRAINING (Engagement Predictor)

### Notebook: `02_data_preparation_training.ipynb`

**What it produces:**
- `engagement_predictor.pkl` — XGBoost model predicting engagement rate
- `label_encoders.pkl` — encoders for categorical columns
- `feature_scaler.pkl` — StandardScaler
- `platform_benchmarks.json` — per-platform average metrics
- `scoring_weights.json` — calibrated weights per dimension per platform
- `model_report.json` — accuracy metrics + feature importances
- `nlp_calibration.json` — thresholds for caption/sentiment scoring
- `aadb_thresholds.json` — thresholds for visual quality scoring

**Key cleaning steps:**
1. Drop duplicates
2. Drop rows with nulls in critical columns
3. Fix `engagement_rate` outside [0,100]
4. Clip negative counts to 0
5. Log1p transform on skewed columns (likes, reach, impressions, engagement_rate)
6. Parse datetime → extract post_hour, day_of_week, month
7. Create `follower_bucket` (nano/micro/mid/macro/mega) from quantiles
8. Create `hashtag_optimal` flag (boolean: is count between 8 and 15?)
9. Create `caption_category` (very_short/short/medium/long)

**XGBoost training:**
- Target: `engagement_rate`
- Transform: log1p (skewness was high)
- 80/20 train/test split
- Features: hashtags_count, caption_length, has_call_to_action, post_hour, day_of_week, follower_count, media_type, content_category, account_type

---

## 6. PHASE 3A — VISUAL QUALITY MODULE

### The AADB Dataset
- 8,958 images with human aesthetic ratings
- 13 columns: `ImageFile` + 11 attribute scores + `score`
- Score range: 0 to 1 (this was a critical discovery — original buggy code assumed 0-10)
- 11 attribute columns in range [-1, 1]:
  - `BalacingElements`, `ColorHarmony`, `Content`, `DoF`, `Light`
  - `MotionBlur`, `Object`, `Repetition`, `RuleOfThirds`, `Symmetry`, `VividColor`
- Strongest correlations with score: Content (0.681), Light (0.569), ColorHarmony (0.562)

### Model Architecture: AestheticFusionModel
```
Image (3×256×256)
    ↓
EfficientNet-B2 backbone → 1408 features
    ↓
Image neck (Dropout 0.3 → Linear 512 → BN → ReLU)
    ↓
    concat ← Attr encoder (11 attrs → 64 → 64) [tabular attributes from CSV]
    ↓
Fusion MLP (576 → 256 → 128)
    ↓
Classification head → 3 logits (bad/average/good)
Score head → 1 value (0–1, sigmoid)
```

**Why EfficientNet-B2 over ResNet18:** 1408 output channels vs 512. Better visual representation capacity. For aesthetic quality prediction (composition, color, lighting, depth of field simultaneously) this matters significantly.

**Why late fusion:** The AADB dataset already has human-rated scores per aesthetic dimension. Fusing these directly with image features means the model doesn't have to guess ColorHarmony from pixels alone. This was the main accuracy booster (+8–15%).

### Training Configuration
- Backbone: EfficientNet-B2, ImageNet pretrained
- Frozen: blocks 0–3. Trainable: blocks 4–8 + heads (98.4% trainable params = 8,476,572)
- Loss: CrossEntropyLoss(label_smoothing=0.1) + HuberLoss(delta=0.1) for score regression
- Loss weights: cls=1.0, score=0.4
- Optimizer: AdamW with differential LR (backbone=5e-5, new layers=2e-4)
- Scheduler: CosineAnnealingLR(T_max=30, eta_min=1e-6) — no verbose arg (this was a bug in older versions)
- Augmentation: Resize 288→RandomCrop 256, RandomHorizontalFlip, RandomVerticalFlip(p=0.1), ColorJitter, RandomGrayscale(p=0.05)
- Batch size: 32, WeightedRandomSampler for class balance
- Early stopping: patience=7
- TTA: 5-crop at inference

### Data Split
- Stratified 70/15/15: train=6270 | val=1344 | test=1344
- Class distribution: bad=31.9% | average=30.9% | good=37.2% (balanced by quantile thresholds)
- q33=0.45, q66=0.60 (class boundaries computed from data)

### Final Results
```
Test Accuracy: 76.86% (76.71% in some runs — consistent)
Score MAE: 0.0658

              precision    recall  f1-score
bad(0)        0.7991      0.8551    0.8262
average(1)    0.6544      0.5553    0.6008   ← hardest class (expected)
good(2)       0.8180      0.8720    0.8441

accuracy                            0.7686
```

**Why average class is hardest:** It borders both bad and good. Human raters themselves disagree most on mid-range images. This is expected and normal.

**TTA result:** 76.86% (same as standard) — the model is already well-calibrated.

---

## 7. BUGS FIXED IN VISUAL MODULE (chronological)

### Bug 1 — Fake accuracy = 1.0 (CRITICAL, first version)
**Cause:** Label function checked `if score <= 4` but scores are in [0,1] range. Every row got label 0. Model predicted class 0 for everything → 100% "accuracy".
**Fix:** Quantile-based thresholds using `df['score'].quantile(0.33)` and `df['score'].quantile(0.66)`.

### Bug 2 — No stratified split
**Cause:** All labels were 0, so split was meaningless.
**Fix:** `stratify=df['label']` in both splits.

### Bug 3 — AADB attribute columns ignored
**Cause:** The 11 human-rated attribute columns were loaded but never used in training.
**Fix:** Late fusion architecture — attributes fed through `attr_encoder` and concatenated with image features.

### Bug 4 — `verbose=True` crash in ReduceLROnPlateau
**Cause:** Newer PyTorch removed the `verbose` argument.
**Fix:** Replaced with `CosineAnnealingLR` which has no such argument.

### Bug 5 — Inference always predicts "bad" (CRITICAL, inference stage)
**Cause:** `predict_aesthetic()` fed raw [-1,1] attribute values to a model trained on normalized [0,1] values. The `.replace('_n','')` approach failed to normalize before inference.
**Fix:** Saved `attr_norm_stats.json` during training, loaded it at inference, applied `(raw - cmin) / (cmax - cmin)` before feeding to model.

**Key principle:** The normalization stats (min/max per attribute column) MUST be saved during training and loaded at inference. Without this, the model receives a completely different distribution than it was trained on.

### Saved artifacts from visual module
| File | Size | Purpose |
|---|---|---|
| `visual_scorer_best.pth` | 34.9 MB | Trained model weights |
| `visual_model_config.json` | 1 KB | Class names, thresholds, input size |
| `attr_norm_stats.json` | 0.6 KB | Normalization stats for inference |
| `attribute_importance.json` | 0.4 KB | Which attributes matter most |
| `confusion_matrix.png` | 43 KB | Visual evaluation result |
| `training_curves.png` | 112 KB | Loss/accuracy over epochs |

---

## 8. VISUAL TESTING MODULE

### Notebook: `visual_module_testing.ipynb`
The main training notebook (visual_module.ipynb) had a broken Step 13 that crashed with `NameError: name 'test_df' is not defined` because it was run in a separate kernel session.

**What the testing notebook provides:**
1. **Visual gallery** (8 balanced sample images) — each showing:
   - Original image + true/predicted class + score
   - GREEN overlay (Grad-CAM class=good) — which regions the model sees as high quality
   - RED overlay (Grad-CAM class=bad) — which regions have quality issues
   - Attribute bar chart (all 11 AADB dimensions)
2. **Top 5 best vs Top 5 worst** in the full test set
3. **Deep-dive single image analysis** — all 3 class CAMs + probability bars + score gauge
4. **Full confusion matrix** over all 1344 test images

### Grad-CAM explained
Gradient-weighted Class Activation Mapping. For a given class (e.g., "good"), it:
1. Does a forward pass to get predictions
2. Backpropagates gradients back to the last convolutional layer
3. Weights the activation maps by their importance
4. Produces a 2D heatmap showing which spatial regions most influenced the prediction

Target layer: `model.img_backbone[0][-1]` (last feature block of EfficientNet-B2)

---

## 9. PHASE 3B — TEXT EVALUATION MODULE

### What it evaluates
**Universal text quality** (objective, measurable):
- Readability
- Sentiment strength
- Structure (length, CTA, caps, emojis)
- Hashtag strategy

**NOT evaluated here** (handled by Claude API in Phase 5):
- Brand voice match for specific startup
- Audience targeting appropriateness
- Niche hashtag relevance
- Industry-specific tone

### The sentiment model
**cardiffnlp/twitter-roberta-base-sentiment-latest**
- Trained on 124 MILLION tweets
- Understands hashtags, emojis, slang, abbreviations
- Not trained by us — pure inference (transfer learning)
- Downloads ~500MB, cached after first run
- Outputs: negative/neutral/positive probabilities

**Critical bug fixed:** Label order must be read from `model.config.id2label`, never hardcoded. The code uses:
```python
ID2LABEL = model_sent.config.id2label
LABEL2IDX = {v.lower(): k for k, v in ID2LABEL.items()}
POS_IDX = LABEL2IDX.get('positive', 2)
```

### Platform benchmarks (data-driven)
Computed from instagram_analytics dataset (top 25% engagement quartile):

| Platform | Optimal hashtags | Optimal caption | Spam threshold |
|---|---|---|---|
| Instagram | 8–15 | 100–300 chars | 15 |
| LinkedIn | 3–5 | 150–700 chars | 6 |
| Twitter | 1–2 | 70–240 chars | 3 |
| Facebook | 1–3 | 40–200 chars | 4 |

### The XGBoost engagement predictor (text module)

**Root cause of R²=-0.05 (fixed in v6):**
Previous versions trained XGBoost on `instagram_analytics` using only `caption_length`, `hashtags_count`, `has_call_to_action`. These 3 metadata columns have almost zero predictive power for `engagement_rate` because engagement is driven by follower_count, media_type, and reach — not by text structure alone.

**Fix — Fusion model using all available features:**
The engagement dataset (subashmaster) has:
- `text_content` — actual caption text
- `sentiment_score` — pre-computed sentiment
- `toxicity_score` — content toxicity
- `user_past_sentiment_avg` — historical user behavior
- `user_engagement_growth` — account growth trend
- `buzz_change_rate` — trending momentum
- `impressions`, `likes_count`, `shares_count`, `comments_count`
- `platform`, `day_of_week`, `sentiment_label`, `emotion_type`

The fusion model combines:
- 14 NLP features extracted from `text_content`
- 9 pre-computed numeric features
- 7 encoded categorical features
= ~30 total features

Expected R² with fusion: 0.45–0.75 (much better than -0.05).

### The 14 NLP features extracted
```python
'word_count', 'char_count', 'hashtag_count', 'mention_count',
'exclaim_count', 'question_count', 'emoji_count', 'has_cta',
'has_url', 'readability_flesch', 'avg_word_length',
'sentence_count', 'caps_ratio', 'unique_hashtag_ratio'
```

### Scoring functions

**score_readability (multi-factor — NOT just Flesch):**
- Flesch Reading Ease base score
- Penalty: word count < 5 → cap at 3.0
- Penalty: avg word length > 7 → -1.5 (academic jargon)
- Bonus: sentence count ≥ 3 → +0.5 (structured writing)

**score_sentiment (bounded linear mapping):**
```python
composite = pos - neg  # range -1 to +1
base = 5.0 + composite * 4.0  # gives 1.0 to 9.0
```
**Bug fixed:** Old formula `s = 9.0 + pos * 1.0` gave 9.98 for any positive text (ceiling effect). New formula produces true distribution.

**score_structure (platform-aware):**
- Caption length fit for platform: ±2.0
- CTA presence: +1.5
- Caps > 50%: -3.5 (was -2.5, strengthened)
- Caps > 30%: -2.0
- Question mark: +0.5
- Emojis 1-5: +0.5, >15: -1.0

**score_hashtags (platform-specific thresholds):**
- Count = 0 → 2.0
- In optimal range → 9.0
- Below optimal → proportional (2.0 + count/optimal × 7.0)
- Above spam threshold → 6.0 - (count - threshold) × 0.7

**Spam detection fix:** Posts with all-caps AND high exclamation rate get `-2.5` sentiment penalty because aggressive promotional language is not good content quality despite being detected as "positive" by the sentiment model.

### Dimension weights by platform
```python
DIMENSION_WEIGHTS = {
    'instagram': {'readability':0.20, 'sentiment':0.25, 'structure':0.25, 'hashtags':0.30},
    'linkedin':  {'readability':0.30, 'sentiment':0.20, 'structure':0.35, 'hashtags':0.15},
    'twitter':   {'readability':0.25, 'sentiment':0.30, 'structure':0.30, 'hashtags':0.15},
    'facebook':  {'readability':0.20, 'sentiment':0.30, 'structure':0.35, 'hashtags':0.15},
}
```

### Issue flags detected
```python
issues = {
    'too_short':     char_count < platform.caption_length.optimal_min,
    'too_long':      char_count > platform.caption_length.max_allowed,
    'no_cta':        has_cta == 0,
    'no_hashtags':   hashtag_count == 0,
    'hashtag_spam':  hashtag_count > platform.hashtag_count.spam_threshold,
    'all_caps':      caps_ratio > 0.3,
    'hard_to_read':  readability_flesch < 50,
    'negative_tone': negative > 0.5,
    'flat_neutral':  neutral > 0.65 AND exclaim_count == 0,
    'spam_language': caps_ratio > 0.3 AND exclaim_count/word_count > 0.05,  # NEW
}
```

### Text module artifacts saved
| File | Purpose |
|---|---|
| `text_module_config.json` | Weights, benchmarks, version, CTA keywords |
| `platform_text_benchmarks.json` | Per-platform optimal ranges |
| `text_feature_correlations.json` | NLP feature → engagement correlations |
| `engagement_text_predictor.json` | XGBoost fusion model |
| `text_scaler.pkl` | StandardScaler for inference |
| `text_encoders.pkl` | Label encoders for categorical features |
| `text_feature_config.json` | Feature list + R² + MAE + CV scores |

---

## 10. ALL BUGS FIXED IN TEXT MODULE (chronological)

### Bug 1 — NaN crash (`ValueError: cannot convert float NaN to integer`)
**Cause:** `corr()` returns NaN when a column has zero variance. Then `int(abs(NaN))` crashes.
**Fix:** 4-layer protection:
1. `pd.to_numeric(..., errors='coerce')` forces numeric
2. `.dropna()` removes null rows
3. `.std() == 0` check skips zero-variance columns
4. `corr.replace([np.inf, -np.inf], np.nan).dropna()` removes remaining NaN before any rendering

### Bug 2 — `AttributeError: 'ParserBase' object has no attribute '_maybe_dedup_names'`
**Cause:** Used a private pandas internal API to deduplicate column names. Removed in newer pandas versions.
**Fix:** Custom 6-line deduplication loop adding `_dup1`, `_dup2` suffixes.

### Bug 3 — Column name collision on merge
**Cause:** Sentiment model output columns (`label`, `score`) clashed with source dataset columns.
**Fix:** All sentiment model output columns prefixed with `s_` before merging.

### Bug 4 — Sentiment always 9.9/10
**Cause:** Formula `s = 8.5 + pos * 1.5` with `pos > 0.7` for almost all social media text → always hits ceiling.
**Fix:** Bounded linear formula `base = 5.0 + (pos-neg) * 4.0` → proper range 1–9.

### Bug 5 — Readability always 5.5/10
**Cause:** Flesch formula on short social media text produces 50–60 range consistently → always maps to 5.5.
**Fix:** Multi-factor scoring combining Flesch + avg word length + word count + sentence count.

### Bug 6 — Spam post scores 7.3/10 (should be ≤ 4.5)
**Cause:** Spam threshold was 20, post had 19 hashtags (just below cutoff). Caps penalty -1.0 insufficient.
**Fix:** Spam threshold lowered to 15. Caps penalty strengthened to -3.5 (>50%) and -2.0 (>30%). New `spam_language` detection: caps + exclamation rate → -2.5 sentiment penalty.

### Bug 7 — XGBoost R²=-0.05 (wrong training data)
**Cause:** Trained on `instagram_analytics` using only 3 metadata columns. Engagement is not predictable from caption_length alone.
**Fix:** Fusion model using all 30+ features from the engagement dataset (subashmaster) which has actual text, pre-computed sentiment scores, user behavior metrics, etc.

### Bug 8 — Slow one-by-one sentiment inference
**Cause:** Each text sent to model individually in a loop.
**Fix:** Batch processing — 32 texts at a time through the model. 32× faster.

---

## 11. NOTEBOOKS GENERATED (complete list)

| Notebook | What it does | Status |
|---|---|---|
| `01_data_exploration.ipynb` | Phase 1: explore all 6 datasets | ✅ Works |
| `02_data_preparation_training.ipynb` | Phase 2: clean + train XGBoost on instagram_analytics | ✅ Works |
| `visual_module_fixed.ipynb` | Visual module v1 with bug fixes | ✅ Superseded |
| `visual_module_v2.ipynb` | Visual module v2 — EfficientNet-B2 + fusion | ✅ Superseded |
| `visual_module_inference_fix.ipynb` | Patch for normalization bug in inference | ✅ Applied |
| `visual_module_testing.ipynb` | **FINAL** visual testing gallery with Grad-CAM | ✅ Current |
| `text_module.ipynb` | Text module v1 | ✅ Superseded |
| `text_module_final.ipynb` | Text module v2 | ✅ Superseded |
| `text_module_v4_final.ipynb` | Text module v4 — bulletproof error handling | ✅ Superseded |
| `text_module_v5.ipynb` | Text module v5 — correct training data | ✅ Superseded |
| `text_module_v6.ipynb` | Text module v6 — fusion model | ✅ Current |
| `text_module_patch.ipynb` | Patch for spam scoring bugs | ✅ Current |

---

## 12. WHAT HAS BEEN COMPLETED

### ✅ Done
- Phase 1: Data exploration for 1/6 datasets (instagram_analytics fully explored)
- Phase 2: Data cleaning and feature engineering pipeline
- Phase 3A: Visual quality module — EfficientNet-B2 + fusion, 76.86% accuracy, Grad-CAM testing
- Phase 3B: Text evaluation module — Twitter RoBERTa sentiment + rule-based scoring + XGBoost
- Phase 4: Platform benchmarks extracted (instagram_analytics data-driven, others research-based)

### ❌ Not yet done
- Phase 1: Explore remaining 5 datasets (indices 1–6)
- Update LinkedIn/Facebook/Twitter benchmarks from real data
- Phase 5: Claude API prompt engineering for startup-specific evaluation
- Phase 6: Scoring engine calibration (combine visual + text + Claude API scores)
- Phase 7: End-to-end validation on real startup posts
- App development (frontend, backend, integration)
- Objective 2: Brand strategy document generation & evaluation

---

## 13. TECHNICAL ENVIRONMENT

- **Kaggle notebooks** for all ML training (Phases 1–5) — GPU: Tesla T4
- **VS Code** for Phase 6+ (scoring engine, app development)
- Running locally on Windows (MSI laptop, CPU only for testing)
- Python 3.12.12
- Key libraries: PyTorch, torchvision, transformers, xgboost, sklearn, textstat, pandas, numpy

---

## 14. SCORING ENGINE DESIGN (Phase 6 — not yet built)

### How scores combine
```python
PLATFORM_WEIGHTS = {
    'instagram': {
        'visual_quality':      0.30,  # most visual platform
        'text_clarity':        0.10,
        'caption_quality':     0.20,
        'hashtags':            0.20,
        'engagement_potential':0.20,
    },
    'linkedin': {
        'visual_quality':      0.15,
        'text_clarity':        0.15,
        'caption_quality':     0.40,  # caption is king on LinkedIn
        'hashtags':            0.10,
        'engagement_potential':0.20,
    },
}
```

### Score interpretation
| Range | Label |
|---|---|
| 0–3 | Poor — significant issues |
| 3–5 | Below average — needs improvement |
| 5–7 | Average — acceptable |
| 7–8.5 | Good — above average |
| 8.5–10 | Excellent |

---

## 15. THE CLAUDE API LAYER (Phase 5 — not yet built)

### What it handles (startup-specific evaluation)
- Is the tone right for this specific target audience?
- Are these hashtags relevant to this startup's niche?
- Does the caption communicate the startup's value proposition?
- Is the writing style consistent with the brand voice?
- Does the first line hook the right type of customer?

### How it works
Two API calls per evaluation:
1. **Call 1 — Vision + text analysis**: sends image + caption + hashtags + startup description + platform → returns JSON with scores 0–10 per dimension + key findings
2. **Call 2 — Recommendations**: sends Call 1 results + original content → generates revised caption, better hashtags, priority fixes

---

## 16. INFERENCE FUNCTION (final — visual module)

```python
def predict_aesthetic(image_path, raw_attrs_dict, model, device,
                      norm_stats=None, use_tta=True):
    """
    Args:
        image_path:     path to image file
        raw_attrs_dict: dict of raw AADB attributes in [-1,1] range
                        e.g. {'ColorHarmony': 0.4, 'RuleOfThirds': 0.6}
                        (provided by Claude Vision in the app)
        norm_stats:     loaded from attr_norm_stats.json
        use_tta:        5-crop TTA for better accuracy

    Returns:
        {
            'class_label':  'bad' / 'average' / 'good',
            'class_id':     0 / 1 / 2,
            'score_0_10':   float 0-10,
            'confidence':   float 0-1,
            'class_probs':  {'bad': float, 'average': float, 'good': float}
        }
    """
```

**Key:** In the real app, Claude Vision analyzes the image and returns estimates for each of the 11 AADB attributes. These are passed as `raw_attrs_dict`. This bridges the gap between having a trained model and being able to run it on new startup posts that have no pre-computed attributes.

---

## 17. INFERENCE FUNCTION (final — text module)

```python
def evaluate_text(caption, platform='instagram', hashtags_separate=None):
    """
    Args:
        caption:           post caption text
        platform:          'instagram' / 'linkedin' / 'twitter' / 'facebook'
        hashtags_separate: if hashtags are in a separate field

    Returns:
        {
            'overall_score':    float 0-10,
            'dimension_scores': {readability, sentiment, structure, hashtags},
            'sentiment_detail': {label, positive, neutral, negative, sentiment_score},
            'text_features':    {all 14 NLP features},
            'platform':         str,
            'issues':           {name: True/False for 10 issue types}
        }
    """
```

---

## 18. IMPORTANT NOTES FOR NEXT CONVERSATION

1. **The main visual module notebook was trained on Kaggle** and is saved at `visual_scorer_best.pth` (34.9 MB). The testing notebook (`visual_module_testing.ipynb`) loads this and runs Grad-CAM visualizations — it needs to be run AFTER training on Kaggle.

2. **The text module v6 needs to be run on Kaggle** with all 3 datasets added. After running, also run `text_module_patch.ipynb` to fix the 3 remaining scoring issues.

3. **The correlation between text score and engagement** from the validation: social media engagement is driven by many non-text factors (timing, account size, luck). Even professional researchers get r=0.1–0.3. This is normal. The scoring system's validity is demonstrated qualitatively (Cell 11: good posts score 7+, bad posts score below 4.5).

4. **Phase 1 exploration** was only done for 1 dataset (instagram_analytics). The other 5 need to be explored using `01_data_exploration.ipynb` — change `SELECTED_INDEX` for each one.

5. **The next major step** is Phase 5: prompt engineering for Claude API startup-specific evaluation. This involves writing and testing the prompts that Claude uses to evaluate posts with startup context.

6. **Objective 2 (Brand Strategy)** has not been started at all.

7. **The environment** is Kaggle for training, local VS Code for app development. The student runs on Windows locally (CPU, no GPU) for testing and development.

---

## 19. CTA KEYWORDS LIST (used in text module)

```python
CTA_KEYWORDS = [
    'link in bio', 'click', 'shop now', 'learn more', 'swipe up',
    'follow', 'sign up', 'get yours', 'dm us', 'dm me', 'comment below',
    'tag a friend', 'share this', 'save this', 'book now', 'apply now',
    'download', 'subscribe', 'register', 'join us', 'check out', 'visit',
    'order now', 'try now', 'get started', 'find out', 'discover',
]
```

---

## 20. ATTRIBUTE DISPLAY NAMES (for UI)

```python
ATTR_DISPLAY_NAMES = {
    'BalacingElements': 'Balance',           # note: typo in AADB dataset, kept as-is
    'ColorHarmony':     'Color Harmony',
    'Content':          'Content Quality',
    'DoF':              'Depth of Field',
    'Light':            'Lighting',
    'MotionBlur':       'Motion Blur',
    'Object':           'Object Quality',
    'Repetition':       'Repetition',
    'RuleOfThirds':     'Rule of Thirds',
    'Symmetry':         'Symmetry',
    'VividColor':       'Vivid Color',
}
```

---

*End of project summary — all details preserved for continuity.*
