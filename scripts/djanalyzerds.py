"""
DJANALYZER ULTIMATE GUI - Versione 13.0
Con analisi armonica completa e codice Camelot
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json
import pandas as pd
import librosa
import numpy as np
import sys

class HarmonicAnalyzer:
    """Analisi armonica avanzata con rilevamento chiave e codice Camelot"""
    
    CAMELOT_WHEEL = {
        ('C', 'Major'): '8B', ('A', 'Minor'): '8A',
        ('G', 'Major'): '9B', ('E', 'Minor'): '9A',
        ('D', 'Major'): '10B', ('B', 'Minor'): '10A',
        ('A', 'Major'): '11B', ('F#', 'Minor'): '11A',
        ('E', 'Major'): '12B', ('C#', 'Minor'): '12A',
        ('B', 'Major'): '1B', ('G#', 'Minor'): '1A',
        ('F#', 'Major'): '2B', ('D#', 'Minor'): '2A',
        ('D', 'Major'): '3B', ('B', 'Minor'): '3A',
        ('A', 'Major'): '4B', ('F#', 'Minor'): '4A',
        ('E', 'Major'): '5B', ('C#', 'Minor'): '5A',
        ('B', 'Major'): '6B', ('G#', 'Minor'): '6A',
        ('F#', 'Major'): '7B', ('D#', 'Minor'): '7A'
    }

    def detect_key(self, y: np.ndarray, sr: int) -> dict:
        """Rileva chiave musicale e codice Camelot"""
        try:
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Trova la tonalità principale
            key_index = np.argmax(chroma_mean)
            keys = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
            key = keys[key_index]
            
            # Determina modalità (Maggiore/Minore)
            major_profile = librosa.feature.chroma_cqt(y=y, sr=sr, tuning=0)
            minor_profile = librosa.feature.chroma_cqt(y=y, sr=sr, tuning=-3)
            mode = "Major" if np.sum(major_profile) > np.sum(minor_profile) else "Minor"
            
            # Ottieni codice Camelot
            camelot = self.CAMELOT_WHEEL.get((key, mode), "?")
            
            return {
                "key": key,
                "mode": mode,
                "camelot": camelot,
                "confidence": float(chroma_mean[key_index])
            }
            
        except Exception as e:
            return {
                "key": "Unknown",
                "mode": "Unknown",
                "camelot": "?",
                "error": str(e)
            }

class DJAnalyzerGUI:
    def __init__(self, root):
        # ... (resto dell'inizializzazione come prima)
        self.harmonic_analyzer = HarmonicAnalyzer()

    def analyze_file(self, file_path):
        try:
            y, sr = librosa.load(file_path, sr=44100)
            
            # Analisi ritmica
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            if isinstance(tempo, np.ndarray):
                tempo = tempo[0] if tempo.size > 0 else 0.0
            
            # Analisi armonica
            harmonic_data = self.harmonic_analyzer.detect_key(y, sr)
            
            return {
                "file": file_path.name,
                "bpm": round(float(tempo), 1) if tempo else 0,
                "key": f"{harmonic_data['key']} {harmonic_data['mode']}",
                "camelot": harmonic_data['camelot'],
                "duration": round(librosa.get_duration(y=y, sr=sr), 2),
                "status": "OK"
            }
        
        except Exception as e:
            return {
                "file": file_path.name,
                "bpm": 0,
                "key": "Unknown",
                "camelot": "?",
                "duration": 0,
                "status": f"ERRORE: {str(e)}"
            }

    def save_results(self, data, output_path):
        # Modifica le colonne per includere i nuovi dati
        df = pd.DataFrame(data)
        df = df[['file', 'bpm', 'key', 'camelot', 'duration', 'status']]
        df.to_csv(output_path / "analisi.csv", index=False)
        
        with open(output_path / "analisi.json", "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_progress(self, current, total, filename):
        # Aggiungi informazioni armoniche al display
        entry = next((item for item in self.results if item["file"] == filename), {})
        progress = (
            f"Processato {current}/{total}: {filename}\n"
            f"   BPM: {entry.get('bpm', 0)} | "
            f"Chiave: {entry.get('key', 'Unknown')} | "
            f"Camelot: {entry.get('camelot', '?')}\n"
        )
        self.results_text.insert(tk.END, progress)
        self.results_text.see(tk.END)
        self.root.update_idletasks()

# ... (resto del codice rimane invariato)