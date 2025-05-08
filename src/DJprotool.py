import os
import datetime
import re
import tkinter as tk
from tkinter import filedialog

from file_loader      import carica_file_audio, carica_cartella
from analyzer         import AudioAnalyzer
from logger           import logger
from harmonic         import rileva_chiave
from energy           import calcola_energia
from cue              import rileva_cue
from quantization     import quantizza_audio
from harmony_opt      import ottimizza_chiave

# --- helper per Text widget ---
def append_output(widget, text):
    widget.configure(state="normal")
    widget.insert("end", text + "\n")
    widget.see("end")
    widget.configure(state="disabled")

# Camelot map
CAMELOT_MAP = {
    'A#': '1A', 'Bb': '1A', 'F': '1B',
    'C': '2B', 'G': '3B', 'D': '4B', 'A': '5B', 'E': '6B', 'B': '7B',
    'F#': '8B', 'Gb': '8B', 'C#': '9B', 'Db': '9B', 'G#': '10B', 'Ab': '10B',
    'D#': '11B', 'Eb': '11B'
}

class DJProToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJ Pro Tool")
        self.geometry("900x650")
        self.analyzer = AudioAnalyzer()
        self.path = None

        # Bottoni
        frame = tk.Frame(self, pady=10)
        frame.pack(fill=tk.X)
        tk.Button(frame, text="Seleziona File", command=self.load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Seleziona Cartella", command=self.load_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Analizza", command=self.analyze).pack(side=tk.LEFT, padx=5)

        # Output area
        self.txt = tk.Text(self, state="disabled", wrap=tk.WORD)
        self.txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def load_file(self):
        f = carica_file_audio()
        if f:
            self.path = f
            append_output(self.txt, f">> File: {os.path.basename(f)}")

    def load_folder(self):
        d = carica_cartella()
        if d:
            self.path = d
            append_output(self.txt, f">> Cartella: {d}")

    def analyze(self):
        if not self.path:
            append_output(self.txt, "Seleziona prima file o cartella.")
            return

        # Header
        append_output(self.txt, "Analisi files:")
        append_output(self.txt, "Avvio analisi…")

        # Prepare results dir
        base = self.path if os.path.isdir(self.path) else os.path.dirname(self.path)
        outdir = os.path.join(base, 'risultati', datetime.datetime.now().strftime('Risultati_%Y%m%d_%H%M%S'))
        os.makedirs(outdir, exist_ok=True)

        # Collect files
        if os.path.isfile(self.path):
            files = [self.path]
        else:
            files = [os.path.join(self.path, f) for f in os.listdir(self.path)
                     if f.lower().endswith(('.mp3', '.wav'))]
        if not files:
            append_output(self.txt, "Nessun file audio.")
            return

        # Process each file
        for idx, filepath in enumerate(files, 1):
            name = os.path.basename(filepath)
            clean = re.sub(r"\s*\[.*?\]", "", os.path.splitext(name)[0]) + os.path.splitext(name)[1]
            append_output(self.txt, f"{idx}. Analizzo: {clean}")
            try:
                audio = self.analyzer.carica_audio(filepath)
                bpm = int(self.analyzer.calcola_bpm(audio))
                key = rileva_chiave(filepath)
                camelot = CAMELOT_MAP.get(key, '?')
                energy = int(calcola_energia(filepath) * 100)
                cues = rileva_cue(filepath)
                append_output(self.txt, f"   → BPM:{bpm}, Key:{key} ({camelot}), Energy:{energy}, Cues:{cues}")
            except Exception as e:
                logger.error(f"Errore su {name}: {e}")
                append_output(self.txt, f"   Errore su {clean}")

        # Save and open
        rpt = os.path.join(outdir, 'risultati.txt')
        with open(rpt, 'w', encoding='utf-8') as f:
            f.write(self.txt.get('1.0', 'end'))
        append_output(self.txt, f"Fine. Risultati in: {outdir}")
        try:
            os.startfile(outdir)
        except:
            pass

if __name__ == '__main__':
    DJProToolApp().mainloop()
