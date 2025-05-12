# DJAnalyzer - Programma completo (Analisi BPM, Chiave, Energia, Spettro)

import os
import threading
import io
import librosa
import librosa.display
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt

# --- Modulo: Key Analyzer ---
CAMELT_MAP = {
    "G#m": "1A", "D#m": "2A", "A#m": "3A", "Fm": "4A", "Cm": "5A", "Gm": "6A", "Dm": "7A", "Am": "8A",
    "Em": "9A", "Bm": "10A", "F#m": "11A", "C#m": "12A", "G#": "1B", "D#": "2B", "A#": "3B", "F": "4B",
    "C": "5B", "G": "6B", "D": "7B", "A": "8B", "E": "9B", "B": "10B", "F#": "11B", "C#": "12B"
}

PITCH_MAP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def analyze_key(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        pitch_class = chroma_mean.argmax()
        key_raw = PITCH_MAP[pitch_class]
        is_minor = chroma_mean[(pitch_class + 3) % 12] > chroma_mean[(pitch_class + 4) % 12]
        key_label = key_raw + ('m' if is_minor else '')
        camelot = CAMELT_MAP.get(key_label, '')
        return key_label, camelot
    except Exception as e:
        print(f"Errore nella rilevazione della chiave: {e}")
        return 'C', '5B'

# --- Modulo: BPM Analyzer ---
def analyze_bpm(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        tempo = librosa.beat.tempo(y=y, sr=sr)
        bpm = int(round(tempo[0])) if tempo.size else 0
        return bpm
    except Exception as e:
        print(f"Errore durante l'analisi BPM: {e}")
        return 0

# --- Modulo: Energy Analyzer ---
def analyze_energy(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        rms = librosa.feature.rms(y=y)
        energy = float(np.mean(rms)) if rms.size else 0
        scaled = min(10, max(1, int(np.ceil(energy * 20))))
        color = energy_to_color(scaled)
        return scaled, color
    except Exception as e:
        print(f"Errore nel calcolo dell'energia: {e}")
        return 1, "Gray"

def energy_to_color(value):
    palette = {
        1: "Gray", 2: "Blue", 3: "Cyan", 4: "Green", 5: "Lime",
        6: "Yellow", 7: "Orange", 8: "Red", 9: "Magenta", 10: "White"
    }
    return palette.get(value, "Gray")

# --- Modulo: Compatibility Checker ---
def find_compatible_keys(camelot):
    if not camelot:
        return []
    try:
        num = int(camelot[:-1])
        letter = camelot[-1]
        return [
            f"{num}{letter}",
            f"{(num % 12) + 1}{letter}",
            f"{(num - 2) % 12 + 1}{letter}",
            f"{num}{'A' if letter == 'B' else 'B'}"
        ]
    except:
        return []

# --- Interfaccia Grafica ---
class DJAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJAnalyzer")
        self.geometry("1000x800")
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.paused = False
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(frame, text="Cartella Input:").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.input_folder, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Sfoglia", command=self.browse_input).pack(side=tk.LEFT)
        ttk.Label(frame, text="Cartella Output:").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Entry(frame, textvariable=self.output_folder, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Sfoglia", command=self.browse_output).pack(side=tk.LEFT)
        ttk.Button(self, text="Avvia Analisi", command=self.run_analysis).pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("File", "BPM", "Key", "Compatibili", "Energia", "Colore"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Spettro
        self.spectrum_frame = ttk.LabelFrame(self, text="Spettro Audio")
        self.spectrum_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        self.pause_button = ttk.Button(self.spectrum_frame, text="Pausa", command=self.toggle_pause)
        self.pause_button.pack(anchor="e", padx=10, pady=5)
        self.canvas = tk.Canvas(self.spectrum_frame, bg="black", height=300)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def browse_input(self):
        self.input_folder.set(filedialog.askdirectory())

    def browse_output(self):
        self.output_folder.set(filedialog.askdirectory())

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.config(text="Riprendi" if self.paused else "Pausa")

    def run_analysis(self):
        try:
            files = [f for f in os.listdir(self.input_folder.get()) if f.lower().endswith((".mp3", ".wav", ".flac"))]
            results = []
            self.tree.delete(*self.tree.get_children())
            for fname in files:
                path = os.path.join(self.input_folder.get(), fname)
                bpm = analyze_bpm(path)
                key, camelot = analyze_key(path)
                energy, color = analyze_energy(path)
                compatible = find_compatible_keys(camelot)
                row = {
                    'File': fname,
                    'BPM': bpm,
                    'Key': f"{key} ({camelot})",
                    'Compatibili': ', '.join(compatible),
                    'Energia': energy,
                    'Colore': color
                }
                self.tree.insert("", "end", values=tuple(row.values()))
                results.append(row)
                if not self.paused:
                    self.show_spectrum(path)
            pd.DataFrame(results).to_csv(os.path.join(self.output_folder.get(), 'analisi.csv'), index=False)
            messagebox.showinfo("Completato", "Analisi completata e salvata!")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def show_spectrum(self, file_path):
        try:
            y, sr = librosa.load(file_path, sr=None)
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
            fig, ax = plt.subplots(figsize=(10, 3))
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', cmap='magma', ax=ax)
            ax.set(title='Spettro')
            fig.tight_layout(pad=0)
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close(fig)
            buf.seek(0)
            img = Image.open(buf)
            img = img.resize((900, 300))
            img_tk = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor='nw', image=img_tk)
            self.canvas.image = img_tk
        except Exception as e:
            print(f"Errore spettro: {e}")

if __name__ == '__main__':
    app = DJAnalyzerApp()
    app.mainloop()
