import os
import edge_tts
from faster_whisper import WhisperModel

# Initialize Whisper model on your RTX 3050 GPU (small or base model)
stt_model = WhisperModel("base", device="cuda", compute_type="float16")

def transcribe_audio(file_path: str) -> str:
    """Transcribes input audio file to text using local GPU."""
    segments, _ = stt_model.transcribe(file_path, beam_size=5)
    return "".join([segment.text for segment in segments]).strip()

async def text_to_speech(text: str, output_path: str):
    """Converts AI response text into an MP3 voice file."""
    communicate = edge_tts.Communicate(text, voice="en-US-ChristopherNeural")
    await communicate.save(output_path)