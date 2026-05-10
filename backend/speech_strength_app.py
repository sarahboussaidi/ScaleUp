import os
from typing import Tuple, Dict, Any

try:
    import gradio as gr
except Exception:
    gr = None

try:
    import whisper
except Exception:
    whisper = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

from strength_predictor import hybrid_strength_predict


def transcribe_with_whisper(audio_path: str) -> str:
    model = whisper.load_model("small")
    result = model.transcribe(audio_path)
    return result.get("text", "")


def transcribe_with_speechrecognition(audio_path: str) -> str:
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception:
        return ""


def transcribe_audio(audio) -> str:
    # Gradio passes a dict with 'name' key path or a temp file path
    if isinstance(audio, dict) and "name" in audio:
        audio_path = audio["name"]
    else:
        audio_path = audio

    audio_path = str(audio_path)
    # prefer whisper
    if whisper is not None:
        try:
            return transcribe_with_whisper(audio_path)
        except Exception:
            pass

    if sr is not None:
        try:
            return transcribe_with_speechrecognition(audio_path)
        except Exception:
            pass

    return ""


def analyze(audio) -> Tuple[str, Dict[str, Any]]:
    transcript = transcribe_audio(audio)
    prediction = hybrid_strength_predict(transcript or "")
    return transcript, prediction


def launch_ui():
    if gr is None:
        raise ImportError("gradio not installed")

    with gr.Blocks() as demo:
        gr.Markdown("# Speech Strength Evaluator")
        with gr.Row():
            mic = gr.Audio(sources=["microphone"], type="filepath", label="Record (microphone)")
            upload = gr.Audio(sources=["upload"], type="filepath", label="Upload file (wav/mp3)")
        transcript_out = gr.Textbox(label="Transcription")
        label_out = gr.Label(num_top_classes=3, label="Prediction")

        def handle_submit(mic_file, upload_file):
            audio = mic_file or upload_file
            if not audio:
                return "", {"label": "", "confidence": 0.0}
            txt, pred = analyze(audio)
            # prepare label output for gradio label component
            label_display = {pred['label']: pred['final_score']}
            return txt, label_display

        btn = gr.Button("Analyze")
        btn.click(handle_submit, inputs=[mic, upload], outputs=[transcript_out, label_out])

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    launch_ui()
