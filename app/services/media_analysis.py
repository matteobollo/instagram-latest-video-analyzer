from pathlib import Path
import os
import subprocess

from app.config import settings
from app.models import TranscriptResult, VideoAnalysis


def run_command(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout


def probe_duration(video_path: Path) -> float | None:
    output = run_command([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)
    ]).strip()
    return round(float(output), 3) if output else None


def extract_audio(video_path: Path, wav_path: Path) -> None:
    subprocess.run([
        'ffmpeg', '-y', '-i', str(video_path), '-ac', '1', '-ar', '16000', str(wav_path)
    ], capture_output=True, check=True)


def detect_bpm(wav_path: Path) -> float | None:
    import librosa
    y, sr = librosa.load(str(wav_path), sr=None, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(tempo)
    return round(bpm, 2) if bpm > 0 else None


def detect_voice(wav_path: Path) -> bool:
    import librosa
    y, _ = librosa.load(str(wav_path), sr=16000, mono=True)
    rms = librosa.feature.rms(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    if len(rms) == 0 or len(zcr) == 0:
        return False
    energy = float(rms.mean())
    zero_crossing_rate = float(zcr.mean())
    return energy > 0.01 and 0.02 < zero_crossing_rate < 0.25


def transcribe_if_voice(wav_path: Path, voice_detected: bool) -> TranscriptResult:
    if not voice_detected:
        return TranscriptResult(voice_detected=False, transcript=None, language=None)

    import whisper
    model = whisper.load_model(settings.whisper_model)
    result = model.transcribe(str(wav_path), fp16=False)
    text = (result.get('text') or '').strip()
    return TranscriptResult(
        voice_detected=True,
        transcript=text or None,
        language=result.get('language'),
    )


def analyze_video(video_path: Path, working_dir: Path) -> VideoAnalysis:
    wav_path = working_dir / f'{video_path.stem}.wav'
    duration_seconds = probe_duration(video_path)
    extract_audio(video_path, wav_path)

    try:
        bpm = detect_bpm(wav_path)
    except Exception:
        bpm = None

    try:
        voice_detected = detect_voice(wav_path)
    except Exception:
        voice_detected = False

    transcript = transcribe_if_voice(wav_path, voice_detected)

    try:
        os.remove(wav_path)
    except OSError:
        pass

    return VideoAnalysis(
        duration_seconds=duration_seconds,
        bpm=bpm,
        bpm_detected=bpm is not None,
        transcript=transcript,
    )
