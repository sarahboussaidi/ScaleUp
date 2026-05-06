# Visual Score Calculation Formula (Feature-Based)

## Overview

The visual score is **transparent and explainable** through a **weighted composite of 12 visual features**, not a black-box neural network.

---

## Score Calculation

```
visual_score_0_10 = sum(feature_scores[i] × feature_weights[i])
                   for i in [Content, ColorHarmony, Object, VividColor, Light, DoF, 
                            RuleOfThirds, BalancingElements, Repetition, MotionBlur, 
                            Symmetry, Contrast]

Clipped to [0.0, 10.0] range
```

### Example

Given a screenshot with features:
```
Content:           4.4/10 × 0.13 = 0.572
ColorHarmony:      5.73/10 × 0.12 = 0.688
Object:            2.57/10 × 0.10 = 0.257
VividColor:        5.99/10 × 0.09 = 0.539
Light:             9.92/10 × 0.09 = 0.893
DoF:               7.08/10 × 0.09 = 0.637
RuleOfThirds:      6.0/10 × 0.08 = 0.480
BalancingElements: 9.05/10 × 0.07 = 0.634
MotionBlur:        10.0/10 × 0.07 = 0.700
Contrast:          9.66/10 × 0.06 = 0.580
Repetition:        5.12/10 × 0.05 = 0.256
Symmetry:          7.82/10 × 0.05 = 0.391
                                    -------
VISUAL SCORE:                       6.63/10
```

---

## Feature Weights (Learned from AADB Dataset)

| Feature | Weight | How It's Calculated |
|---------|--------|---------------------|
| **Content** | 13% | Luminance entropy (0.55) + edge density target score (0.45) |
| **ColorHarmony** | 12% | Hue coherence (0.55) + RGB std deviation (0.45) |
| **Object** | 10% | Saliency mass in central region (normalized 0–1 to 0–10) |
| **VividColor** | 9% | Target score for saturation ≈ 0.45 (±0.22 tolerance) |
| **Light** | 9% | Target score for brightness ≈ 150 (±65 tolerance, 0–255 scale) |
| **DoF** | 9% | Center-to-border Laplacian variance ratio (depth-of-field proxy) |
| **RuleOfThirds** | 8% | Distance from saliency center to nearest thirds intersection |
| **BalancingElements** | 7% | 1 − (horizontal imbalance + vertical imbalance) / 2 |
| **Repetition** | 5% | Tile regularity: 1 − (tile luminance std / 64) |
| **MotionBlur** | 7% | Laplacian variance target score ≈ 100 (±80 tolerance) |
| **Symmetry** | 5% | 1 − (h-flip diff + v-flip diff) / 2 |
| **Contrast** | 6% | Target score for luminance std ≈ 55 (±25 tolerance) |

---

## Why Feature-Based?

**Problem:** Neural network scores could diverge from interpretable features
- Image A: NN gives 10/10, but features only support 6.6/10 → **confusing**

**Solution:** Visual score **is the weighted sum of features you see**
- ✓ Transparent: each feature contribution is visible
- ✓ Debuggable: understand why score is low (e.g., Object=2.57 drags down composite)
- ✓ Consistent: score always equals the features shown
- ✓ Accountable: if you improve one feature, the score goes up proportionally

---

## Implementation

**Source:** `visual_inference.py` → `detailed_feature_visual_score()` and `predict_aesthetic()` functions

**Outputs folder:**
- Model checkpoint (for reference): `outputs/visual_scorer_best.pth`
- Model config: `outputs/visual_model_config.json`
- Attribute stats: `outputs/attr_norm_stats.json`

**Class Label** (derived from composite score):
```
if score_0_10 < 3.33:
    class = "bad"
elif score_0_10 < 6.67:
    class = "average"
else:
    class = "good"
```
11. VividColor

These are **normalized** using pre-computed min/max stats before being fed to the model.

---

## Output Structure

```json
{
  "class_label": "good",           // Derived from score_0_10
  "class_id": 2,                   // 0=bad, 1=average, 2=good
  "score_0_10": 6.5,               // FINAL VISUAL SCORE (0-10 scale)
  "confidence": 0.95,              // Fixed confidence value
  "class_probs": {
    "bad": 0.025,
    "average": 0.025,
    "good": 0.95
  },
  "model_source": "trained_efficientnet_b2"
}
```

---

## Key Differences from Text Score

| Aspect | Text Score | Visual Score |
|--------|-----------|-------------|
| **Source** | Feature-based weighted sum | Neural network prediction |
| **Dimensions** | 3-4 interpretable dimensions (sentiment, structure, hashtags, etc.) | 11 AADB attributes (implicit, learned by model) |
| **Transparency** | **High** - Each dimension shows score & weight | **Low** - Black box neural network |
| **Formula** | Explicit weighted average | Implicit (learned by model during training) |
| **Penalty System** | Yes (applied but hidden in UI now) | None observed |

---

## No Penalties on Visual Score

Unlike the text score (which had a penalty system that collapsed scores based on underperformance), the visual score is **the direct output of the neural network** with no post-processing penalties applied.

What you see is what you get: `score_0_10` = final visual score.

---

## Where Is It Calculated?

**Flow in code:**
```
engagement_pipeline.py → visual_eval_inference.py
                       → predict_aesthetic(image_path, outputs_dir="outputs")
                       → AestheticFusionModel.forward(image_tensor, attrs_tensor)
                       → Returns score_0_10
```

**Then displayed in:**
- Web UI: `templates/results.html` as "Notebook-Trained Visual Score"
- JSON output: `results/[timestamp]_result.json` as `visual_overall_score`

---

## Summary

**The visual score formula is:**

$$\text{visual\_score\_0\_10} = 10 \times \sigma\left(\text{FusionModel}(\text{image}, \text{attributes})\right)$$

Where:
- $\sigma$ = Sigmoid activation function (output range 0-1)
- `FusionModel` = Trained EfficientNet-B2 with attribute fusion
- Image = Screenshot processed with optional test-time augmentation
- Attributes = 11 AADB aesthetic attributes (normalized)

**In plain English:**
A trained deep learning model processes the image and aesthetic attributes, outputs a score between 0 and 1 through a sigmoid function, then that's multiplied by 10 to get the final 0-10 visual quality score.
