from pathlib import Path
import os
import subprocess

from app.config import settings
from app.models import TranscriptResult, VideoAnalysis


def run_command(command: list[str]) -> str:
    """
    Run a command in a subprocess and return its output as a string.

    Args:
        command: A list of strings representing the command to run.

    Returns:
        The output of the command as a string.
    """
    # Run the command in a subprocess and capture its output
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    # Return the output of the command as a string
    return result.stdout


def probe_duration(video_path: Path) -> float | None:
    """
    Use ffprobe to get the duration of a video file.

    Args:
        video_path: The path to the video file.

    Returns:
        The duration of the video file as a float, or None if the video file does not exist or if ffprobe fails.
    """
    # Use ffprobe to get the duration of the video file
    command = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)
    ]
    output = run_command(command).strip()
    if not output:
        return None
    # Return the duration of the video file as a float
    return round(float(output), 3)


def extract_audio(video_path: Path, wav_path: Path) -> None:
    """
    Extract the audio from a video file using ffmpeg and save it to a WAV file.

    Args:
        video_path: The path to the video file.
        wav_path: The path to the WAV file to create.

    Returns:
        None
    """
    # Use ffmpeg to extract the audio from the video file
    # and save it to the WAV file
    command = [
        'ffmpeg', '-y', '-i', str(video_path), '-ac', '1', '-ar', '16000', str(wav_path)
    ]
    # Run the command in a subprocess and capture its output
    subprocess.run(command, capture_output=True, check=True)


def detect_bpm(wav_path: Path) -> float | None:
    """
    Detect the beats per minute (BPM) of an audio file using librosa.

    Args:
        wav_path: The path to the audio file.

    Returns:
        The BPM of the audio file as a float, or None if the BPM could not be detected.
    """
    import librosa
    # Load the audio file
    y, sr = librosa.load(str(wav_path), sr=None, mono=True)
    # Detect the BPM
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(tempo)
    # Return the BPM as a float, rounded to two decimal places
    return round(bpm, 2) if bpm > 0 else None


def detect_voice(wav_path: Path) -> bool:
    """
    Detect if an audio file contains voice or not.

    This function uses the RMS energy and zero crossing rate of the audio file to determine if it contains voice or not.
    A file is considered to contain voice if its RMS energy is greater than 0.01 and its zero crossing rate is between 0.02 and 0.25.

    Args:
        wav_path: The path to the audio file.

    Returns:
        True if the audio file contains voice, False otherwise.
    """
    import librosa
    # Load the audio file
    y, _ = librosa.load(str(wav_path), sr=16000, mono=True)
    # Compute the RMS energy of the audio file
    rms = librosa.feature.rms(y=y)[0]
    # Compute the zero crossing rate of the audio file
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    # Check if the RMS energy and zero crossing rate are valid
    if len(rms) == 0 or len(zcr) == 0:
        return False
    # Get the mean RMS energy and zero crossing rate
    energy = float(rms.mean())
    zero_crossing_rate = float(zcr.mean())
    # Return True if the audio file contains voice, False otherwise
    return energy > 0.01 and 0.02 < zero_crossing_rate < 0.25


def transcribe_if_voice(wav_path: Path, voice_detected: bool) -> TranscriptResult:
    """
    Transcribe an audio file using the Whisper AI model if it contains voice.

    Args:
        wav_path: The path to the audio file.
        voice_detected: Whether the audio file contains voice or not.

    Returns:
        A TranscriptResult object containing the transcription result, or None if the audio file does not contain voice.
    """
    if not voice_detected:
        # If the audio file does not contain voice, return a TranscriptResult object with voice_detected=False
        return TranscriptResult(voice_detected=False, transcript=None, language=None)

    # Load the Whisper AI model
    import whisper
    model = whisper.load_model(settings.whisper_model)

    # Transcribe the audio file using the Whisper AI model
    result = model.transcribe(str(wav_path), fp16=False)

    # Get the text from the transcription result, or None if it is empty
    text = (result.get('text') or '').strip()

    # Return a TranscriptResult object containing the transcription result
    return TranscriptResult(
        voice_detected=True,
        transcript=text or None,
        language=result.get('language'),
    )


def analyze_video(video_path: Path, working_dir: Path) -> VideoAnalysis:
    """
    Analyze a video file and extract its relevant features.

    Args:
        video_path: The path to the video file.
        working_dir: The path to a temporary directory where the audio file will be saved.

    Returns:
        A VideoAnalysis object containing the relevant features of the video file.

    Raises:
        OSError: If there is an error while removing the temporary audio file.
    """
    wav_path = working_dir / f'{video_path.stem}.wav'
    # Get the duration of the video file using ffprobe
    duration_seconds = probe_duration(video_path)
    # Extract the audio from the video file using ffmpeg
    extract_audio(video_path, wav_path)

    try:
        # Detect the BPM of the audio file using librosa
        bpm = detect_bpm(wav_path)
    except Exception:
        # If there is an error while detecting the BPM, set it to None
        bpm = None

    try:
        # Detect if the audio file contains voice or not
        voice_detected = detect_voice(wav_path)
    except Exception:
        # If there is an error while detecting voice, set it to False
        voice_detected = False

    # Transcribe the audio file if it contains voice
    transcript = transcribe_if_voice(wav_path, voice_detected)

    try:
        # Remove the temporary audio file
        os.remove(wav_path)
    except OSError:
        # If there is an error while removing the audio file, ignore it
        pass

    return VideoAnalysis(
        duration_seconds=duration_seconds,
        bpm=bpm,
        bpm_detected=bpm is not None,
        transcript=transcript,
    )
