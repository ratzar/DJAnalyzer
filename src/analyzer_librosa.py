import os
import numpy as np
import librosa

class AudioAnalyzer:
    """Logica per caricamento audio e calcolo BPM usando librosa."""

    def carica_audio(self, path: str) -> tuple[np.ndarray, int]:
        # librosa.load returns samples and sample rate
        samples, sr = librosa.load(path, sr=None, mono=True)
        return samples, sr

    def calcola_bpm(self, audio_data: tuple[np.ndarray, int]) -> float:
        samples, sr = audio_data
        # Use librosa.beat.beat_track
        tempo, _ = librosa.beat.beat_track(y=samples, sr=sr)
        return float(tempo)

    def quantizza(self, audio: np.ndarray, target_bpm: float) -> np.ndarray:
        # Placeholder per quantizzazione
        return audio
