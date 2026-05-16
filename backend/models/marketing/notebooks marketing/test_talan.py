import json
import sys

sys.path.append('.')

from engagement_pipeline import predict_engagement_from_screenshot


image_path = r'outputs\talan.png'
print('=' * 80)
print('TALAN.PNG - FULL SCREENSHOT EVALUATION')
print('=' * 80)

result = predict_engagement_from_screenshot(
    screenshot_path=image_path,
    outputs_dir='outputs',
    metadata={'platform': 'auto'},
)


def print_section(title):
    print('\n' + '=' * 80)
    print(title)
    print('=' * 80)


def print_dict(title, data):
    print_section(title)
    print(json.dumps(data, indent=2, ensure_ascii=False))

print_section('OCR TEXT')
print(result.get('extracted_text', '') or '[no text found]')

print_section('PLATFORM DETECTION')
print(json.dumps(result.get('platform_detection', {}), indent=2, ensure_ascii=False))

print_dict('TEXT EVALUATION', result['text_evaluation'])

text_xai = result.get('text_xai', {})
if text_xai:
    print_dict('TEXT XAI REPORT', {
        'raw_text_full': text_xai.get('raw_text_full', ''),
        'raw_text_preview': text_xai.get('raw_text_preview', ''),
        'text_length': text_xai.get('text_length', 0),
        'overall_score': text_xai.get('overall_score', 0.0),
        'overall_label': text_xai.get('overall_label', 'unknown'),
        'dimension_scores': text_xai.get('dimension_scores', {}),
        'dimension_contribution': text_xai.get('dimension_contribution', {}),
        'feature_metrics': text_xai.get('feature_metrics', {}),
        'top_features': text_xai.get('top_features', {}),
        'issues_detected': text_xai.get('issues_detected', {}),
        'interpretation': text_xai.get('interpretation', ''),
        'report_save_path': text_xai.get('report_save_path', ''),
    })

visual_features = result['visual_features']
ordered_visual_features = {
    'score_0_10': visual_features.get('score_0_10', 0.0),
    'class_label': visual_features.get('class_label', 'unknown'),
    'feature_scores': visual_features.get('feature_scores', {}),
    'feature_weights': visual_features.get('feature_weights', {}),
    'top_contributions': visual_features.get('top_contributions', []),
    'bottom_features': visual_features.get('bottom_features', []),
    'debug_metrics': visual_features.get('debug_metrics', {}),
}
print_dict('DETAILED VISUAL EVALUATION', ordered_visual_features)

print_dict('VISUAL XAI REPORT', result.get('visual_xai', {}))

print_section('FINAL SUMMARY')
print(f"Platform  : {result.get('platform_used_for_text_evaluation', 'instagram')}")
print(f"Text Score   : {result['text_evaluation']['overall_score']:.2f}/10 ({result['text_evaluation']['overall_label']})")
print(f"Visual Score : {result['visual_features']['score_0_10']:.2f}/10 ({result['visual_features']['class_label']})")
print(f"Overall Score: {result['overall_evaluation']['overall_score_0_10']:.2f}/10 ({result['overall_evaluation']['engagement_label']})")
print(f"Confidence   : {result['overall_evaluation']['engagement_confidence']:.3f}")
