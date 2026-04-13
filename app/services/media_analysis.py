from pathlib import Path
import os
import subprocess
import librosa
import numpy as np
import whisper

from app.config import settings
from app.models import TranscriptResult, VideoAnalysis


def run_command(command: list[str]) -> str:
    """
    Run a command and capture its output.

    The method runs the given command using subprocess.run and captures its output.
    The output is returned as a string.

    :param command: The command to run.
    :return: The output of the command as a string.
    """
    # Run the command and capture its output.
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    # Return the output of the command.
    return result.stdout


def probe_duration(video_path: Path) -> float | None:
    """
    Probe the duration of a video file and return it as a float.

    The method uses the FFprobe library to probe the duration of the video file.
    The duration is returned as a float with three decimal places.

    If the video file does not exist or cannot be probed, the method returns None.

    :param video_path: The path to the video file.
    :return: The duration of the video file as a float, or None if the video file does not exist or cannot be probed.
    """
    command = [
        # Run FFprobe in error mode
        "ffprobe",
        "-v", "error",
        # Show the duration of the video file
        "-show_entries", "format=duration",
        # Disable key printing and error handling
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    output = run_command(command).strip()
    if not output:
        return None
    # Return the duration as a float with three decimal places
    return round(float(output), 3)


def extract_audio_for_bpm(video_path: Path, wav_path: Path) -> None:
    """
    Extract the audio from the video file and save it to a WAV file.

    The method uses the FFmpeg library to extract the audio from the video file and save it to a WAV file.
    The audio is extracted with a single channel (mono), a sample rate of 44100 Hz, and a bit depth of 16 bits.

    :param video_path: The path to the video file.
    :param wav_path: The path to the output WAV file.
    :return: None
    """
    command = [
        # Force overwrite of the output file
        "ffmpeg",
        "-y",
        # Input file
        "-i", str(video_path),
        # Disable video
        "-vn",
        # Set the number of audio channels to 1 (mono)
        "-ac", "1",
        # Set the sample rate to 44100 Hz
        "-ar", "44100",
        # Output file
        str(wav_path),
    ]
    # Run the command and capture the output
    subprocess.run(command, capture_output=True, check=True)


def extract_audio_for_speech(video_path: Path, wav_path: Path) -> None:
    """
    Extract the audio from the video file and save it to a WAV file.

    The method uses the FFmpeg library to extract the audio from the video file and save it to a WAV file.
    The audio is extracted with a single channel (mono), a sample rate of 16000 Hz, and a bit depth of 16 bits.

    :param video_path: The path to the video file.
    :param wav_path: The path to the output WAV file.
    :return: None
    """
    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",  # Disable video
        "-ac", "1",  # Single channel (mono)
        "-ar", "16000",  # Sample rate
        "-b:a", "16k",  # Bit depth
        str(wav_path),
    ]
    subprocess.run(command, capture_output=True, check=True)


def detect_bpm(wav_path: Path) -> float | None:
    """
    Detect the BPM of the audio file using Librosa.

    The method uses the Librosa library to detect the BPM of the audio file.
    If the BPM is detected, it is returned with two decimal places.
    If the BPM is not detected, None is returned.

    :param wav_path: The path to the audio file.
    :return: The detected BPM or None if not detected.
    """
    y, sr = librosa.load(str(wav_path), sr=None, mono=True)

    # Try to detect the BPM using the beat_track method.
    try:
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

        if isinstance(tempo, np.ndarray):
            if tempo.size == 0:
                tempo_value = 0.0
            else:
                tempo_value = float(np.ravel(tempo)[0])
        else:
            tempo_value = float(tempo)

        if len(beats) > 0 and tempo_value > 0:
            return round(tempo_value, 2)
    except Exception:
        # If an exception occurs, try to detect the BPM using the onset_strength method.
        pass

    # Try to detect the BPM using the onset_strength method.
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempos = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)

        if tempos is not None and len(tempos) > 0:
            tempo_value = float(np.ravel(tempos)[0])
            if tempo_value > 0:
                return round(tempo_value, 2)
    except Exception:
        # If an exception occurs, return None.
        pass

    return None


def detect_voice(wav_path: Path) -> bool:
    """
    Detect if a voice is present in the audio file using RMS and zero crossing rate.

    :param wav_path: The path to the audio file.
    :return: If a voice is detected in the audio.
    """
    y, _ = librosa.load(str(wav_path), sr=16000, mono=True)
    rms = librosa.feature.rms(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]

    if len(rms) == 0 or len(zcr) == 0:
        # If the audio file is empty, return False
        return False

    energy = float(rms.mean())
    zero_crossing_rate = float(zcr.mean())

    # A voice is detected if the energy is above 0.01 and the zero crossing rate is between 0.02 and 0.25
    return energy > 0.01 and 0.02 < zero_crossing_rate < 0.25


def transcribe_if_voice(wav_path: Path, voice_detected: bool) -> TranscriptResult:
    """
    Transcribe the audio file using Whisper if a voice is detected.

    :param wav_path: The path to the audio file.
    :param voice_detected: If a voice is detected in the audio.
    :return: A TranscriptResult object containing the transcription result.
    """
    if not voice_detected:
        # If no voice is detected, return a TranscriptResult with no voice detected
        return TranscriptResult(
            voice_detected=False,
            transcript=None,
            language=None,
        )

    # Load the Whisper model
    model = whisper.load_model(settings.whisper_model)

    # Transcribe the audio file
    result = model.transcribe(str(wav_path), fp16=False)
    text = (result.get("text") or "").strip()

    # Return the transcription result
    return TranscriptResult(
        voice_detected=True,
        transcript=text or None,
        language=result.get("language"),
    )


def analyze_video(video_path: Path, working_dir: Path) -> VideoAnalysis:
    """
    Analyze a video and return its metadata.

    :param video_path: The path to the video file.
    :param working_dir: The path to the working directory.
    :return: A VideoAnalysis object containing the video metadata.
    """
    bpm_wav_path = working_dir / f"{video_path.stem}_bpm.wav"
    speech_wav_path = working_dir / f"{video_path.stem}_speech.wav"

    duration_seconds = probe_duration(video_path)

    # Extract the audio for BPM detection
    extract_audio_for_bpm(video_path, bpm_wav_path)

    # Extract the audio for speech detection
    extract_audio_for_speech(video_path, speech_wav_path)

    try:
        # Detect the BPM from the audio
        bpm = detect_bpm(bpm_wav_path)
    except Exception:
        # If an error occurs, set BPM to None
        bpm = None

    try:
        # Detect if there is a voice in the audio
        voice_detected = detect_voice(speech_wav_path)
    except Exception:
        # If an error occurs, set voice_detected to False
        voice_detected = False

    # Transcribe the audio if there is a voice
    transcript = transcribe_if_voice(speech_wav_path, voice_detected)

    # Clean up the temporary files
    for path in (bpm_wav_path, speech_wav_path):
        try:
            os.remove(path)
        except OSError:
            pass

    return VideoAnalysis(
        duration_seconds=duration_seconds,
        bpm=bpm,
        bpm_detected=bpm is not None,
        transcript=transcript,
    )
