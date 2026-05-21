# styling_model_v2

Pitch-day clothing recommendation bundle.

## Artifacts

- `styling_model_v2.pkl`: trained multi-output scikit-learn model
- `input_encoders.pkl`: label encoders for the 6 input attributes
- `target_encoders.pkl`: label encoders for the 4 recommendation outputs
- `color_semantics.pkl`: palette and color-family lookup table
- `metadata_v2.json`: input/output schema and model notes

## Inputs

- Hair Color
- Eye Color
- Skin Tone
- Under Tone
- Torso length
- Body Proportion

## Outputs

- Recommended Clothing Colors
- Avoid Clothing Colors
- Recommended Fitting Style
- Recommended Materials

## Usage

```python
from styling_model_v2 import predict_styling_recommendation

profile = {
    "Hair Color": "Brown",
    "Eye Color": "Hazel",
    "Skin Tone": "Medium",
    "Under Tone": "Warm",
    "Torso length": "Balanced",
    "Body Proportion": "Hourglass",
}

result = predict_styling_recommendation(profile)
print(result["pitch_day_summary"])
```

The returned payload includes decoded wardrobe advice plus confidence values for each recommendation field.