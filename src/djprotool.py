import tkinter as tk
from file_loader import carica_file_audio, carica_cartella
from analyzer import AudioAnalyzer
from logger import logger

class DJProToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJ Pro Tool")
        self.geometry("800x600")
        self.analyzer = AudioAnalyzer()

        # Frame comandi in orizzontale in cima
        cmd_frame = tk.Frame(self)
        cmd_frame.pack(fill=tk.X)
        tk.Button(cmd_frame, text="Carica File", command=self.load_file)\
            .pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(cmd_frame, text="Analizza BPM", command=self.analyze)\
            .pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(cmd_frame, text="Seleziona Cartella", command=self.load_folder)\
            .pack(side=tk.LEFT, padx=5, pady=5)

        # Canvas principale
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Label di stato in basso
        self.status_label = tk.Label(self, text="Pronto.", anchor=tk.W)
        self.status_label.pack(fill=tk.X)

    def load_file(self):
        path = carica_file_audio()
        if path:
            self.file_path = path
            logger.info(f"File caricato: {path}")
            self.canvas.delete("all")
            self._display_text(f"File caricato: {path}")
            self.status_label.config(text=f"File caricato: {path}")

    def load_folder(self):
        folder = carica_cartella()
        if folder:
            self.folder_path = folder
            logger.info(f"Cartella selezionata: {folder}")
            self.status_label.config(text=f"Cartella: {folder}")

    def analyze(self):
        if not hasattr(self, 'file_path'):
            self.status_label.config(text="Nessun file caricato.")
            return
        audio = self.analyzer.carica_audio(self.file_path)
        bpm = self.analyzer.calcola_bpm(audio)
        results = [
            f"Risultati analisi per: {self.file_path}",
            f"BPM stimato: {bpm:.2f}",
        ]
        self.canvas.delete("all")
        for idx, line in enumerate(results, start=1):
            self.canvas.create_text(400, 50 * idx, text=line)
        self.status_label.config(text="Analisi completata. Risultati salvati.")

    def _display_text(self, text: str):
        self.canvas.create_text(400, 300, text=text)
