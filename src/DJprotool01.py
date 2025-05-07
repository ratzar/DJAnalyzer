import os
import tkinter as tk
from tkinter import filedialog, messagebox

# Import relativi: carica i moduli dallo stesso folder src/
from file_loader import carica_file_audio, carica_cartella
from analyzer import AudioAnalyzer
from logger import logger

class DJProToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJ Pro Tool")
        self.geometry("800x600")
        self.folder_path = None
        self.analyzer = AudioAnalyzer()

        # Frame comandi in orizzontale in cima
        cmd_frame = tk.Frame(self, pady=10)
        cmd_frame.pack(fill=tk.X)
        btn_padx = 10
        btn_pady = 5

        tk.Button(cmd_frame, text="Seleziona Cartella", command=self.load_folder)\
            .pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        tk.Button(cmd_frame, text="Analizza Cartella", command=self.analyze_folder)\
            .pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)

        # Area di output (Text widget)
        self.output = tk.Text(self, wrap=tk.WORD, height=20)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Label di stato in basso
        self.status_label = tk.Label(self, text="Pronto.", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10, pady=(0,10))

    def load_folder(self):
        path = filedialog.askdirectory(title="Seleziona la cartella dei brani")
        if not path:
            messagebox.showwarning("Errore", "Nessuna cartella selezionata.")
            return
        self.folder_path = path
        self.status_label.config(text=f"Cartella selezionata: {path}")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"-> Cartella: {path}\n")

    def analyze_folder(self):
        if not self.folder_path:
            self.status_label.config(text="Devi prima selezionare una cartella.")
            return

        files = [f for f in os.listdir(self.folder_path)
                 if f.lower().endswith((".mp3", ".wav"))]
        if not files:
            self.output.insert(tk.END, "Nessun file audio trovato.\n")
            self.status_label.config(text="Nessun file audio nella cartella.")
            return

        self.output.delete("1.0", tk.END)
        self.status_label.config(text="Analisi in corso...")
        for idx, fname in enumerate(files, start=1):
            # placeholder per la tua logica di analisi:
            # audio = self.analyzer.carica_audio(os.path.join(self.folder_path, fname))
            # bpm = self.analyzer.calcola_bpm(audio)
            bpm = 0.0  
            line = f"{idx}. {fname} -> BPM: {bpm:.2f}\n"
            self.output.insert(tk.END, line)

        self.status_label.config(text=f"Analisi completata: {len(files)} file elaborati.")

if __name__ == "__main__":
    app = DJProToolApp()
    app.mainloop()
