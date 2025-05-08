import os
import tkinter as tk
from tkinter import filedialog, messagebox

from file_loader      import carica_file_audio, carica_cartella
from analyzer         import AudioAnalyzer
from logger           import logger
from harmonic         import rileva_chiave
from energy           import calcola_energia
from cue              import rileva_cue
from quantization     import quantizza_audio
from harmony_opt      import ottimizza_chiave

class DJProToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJ Pro Tool")
        self.geometry("900x650")
        self.path = None        # file o cartella
        self.analyzer = AudioAnalyzer()

        # --- Pulsanti in alto ---
        cmd_frame = tk.Frame(self, pady=10)
        cmd_frame.pack(fill=tk.X)
        btn_cfg = dict(padx=8, pady=4)

        tk.Button(cmd_frame, text="Seleziona File",   command=self.load_file)   .pack(side=tk.LEFT, **btn_cfg)
        tk.Button(cmd_frame, text="Seleziona Cartella", command=self.load_folder).pack(side=tk.LEFT, **btn_cfg)
        tk.Button(cmd_frame, text="Analizza",          command=self.analyze)     .pack(side=tk.LEFT, **btn_cfg)

        # --- Area di output (Text widget) ---
        self.output = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED, height=20)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Barra di stato in basso ---
        self.status_label = tk.Label(self, text="Pronto.", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10, pady=(0,10))

    def _append_output(self, text: str):
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def load_file(self):
        f = carica_file_audio()
        if f:
            self.path = f
            self.status_label.config(text=f"File selezionato: {f}")
            self.output.configure(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.configure(state=tk.DISABLED)
            self._append_output(f"→ File: {f}")

    def load_folder(self):
        d = carica_cartella()
        if d:
            self.path = d
            self.status_label.config(text=f"Cartella selezionata: {d}")
            self.output.configure(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.configure(state=tk.DISABLED)
            self._append_output(f"→ Cartella: {d}")

    def analyze(self):
        if not self.path:
            self.status_label.config(text="Seleziona prima file o cartella.")
            return

        # Reset output
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)

        # File singolo
        if os.path.isfile(self.path):
            self._process_and_display(self.path, 1)
            self.status_label.config(text="Analisi file completata.")
            return

        # Cartella
        files = [f for f in os.listdir(self.path) if f.lower().endswith((".mp3", ".wav"))]
        if not files:
            self.status_label.config(text="Nessun file audio.")
            return

        self.status_label.config(text="Analisi batch in corso…")
        for idx, fname in enumerate(files, start=1):
            full = os.path.join(self.path, fname)
            self._process_and_display(full, idx)
        self.status_label.config(text="Analisi batch completata.")

    def _process_and_display(self, filepath: str, idx: int):
        name = os.path.basename(filepath)
        # Mostra in output che stiamo per analizzare questo brano
        self._append_output(f"{idx}. Analizzo brano: {name}")
        try:
            audio = self.analyzer.carica_audio(filepath)
            bpm   = int(self.analyzer.calcola_bpm(audio))
            key   = rileva_chiave(filepath)
            energy = int(calcola_energia(filepath) * 100)
            cues  = rileva_cue(filepath)
        except Exception as e:
            logger.error(f"Errore su {name}: {e}")
            bpm = 0; key = "?"; energy = 0; cues = []

        # Ora appendi i risultati
        self._append_output(f"   Risultati → BPM: {bpm}, Key: {key}, Energy: {energy}, Cues: {cues}")
        self._append_output("")  # riga vuota per separazione

if __name__ == "__main__":
    app = DJProToolApp()
    app.mainloop()
