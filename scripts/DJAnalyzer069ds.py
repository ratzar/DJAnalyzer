import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import queue
import time
import librosa
import numpy as np
import pandas as pd
import traceback
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# =============================================
# Configurazioni e strutture dati
# =============================================

@dataclass
class AnalysisResult:
    filename: str
    bpm: int
    key: str
    camelot_code: str
    compatible_keys: str
    energy: int
    camelot_color: str
    energy_color: str

# Mappature costanti
CAMELOT_MAP = {
    'C': '8B', 'C#': '3B', 'D': '10B', 'D#': '5B', 'E': '12B', 'F': '7B',
    'F#': '2B', 'G': '9B', 'G#': '4B', 'A': '11B', 'A#': '6B', 'B': '1B',
    'Cm': '5A', 'C#m': '12A', 'Dm': '7A', 'D#m': '2A', 'Em': '9A', 'Fm': '4A',
    'F#m': '11A', 'Gm': '6A', 'G#m': '1A', 'Am': '8A', 'A#m': '3A', 'Bm': '10A'
}

CAMELOT_COLORS = {
    '1A': 'medium orchid', '1B': 'sky blue',
    '2A': 'magenta', '2B': 'deep sky blue',
    '3A': 'dodger blue', '3B': 'green yellow',
    '4A': 'royal blue', '4B': 'chartreuse',
    '5A': 'spring green', '5B': 'yellow green',
    '6A': 'lawn green', '6B': 'dark sea green',
    '7A': 'gold', '7B': 'yellow',
    '8A': 'orange', '8B': 'light coral',
    '9A': 'dark orange', '9B': 'indian red',
    '10A': 'tomato', '10B': 'medium violet red',
    '11A': 'red', '11B': 'purple',
    '12A': 'dark violet', '12B': 'blue violet',
    'N/A': 'white'
}

ENERGY_COLORS = {
    1: "PaleTurquoise1", 2: "PaleTurquoise2",
    3: "PaleGreen1", 4: "PaleGreen2",
    5: "SpringGreen2", 6: "SpringGreen3",
    7: "yellow1", 8: "gold1",
    9: "dark orange", 10: "red1"
}

# =============================================
# Classe principale dell'applicazione
# =============================================

class DJAnalyzerApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("DJAnalyzer Pro v1.0")
        master.geometry("1024x768")
        
        # Configurazione stato iniziale
        self._initialize_state()
        
        # Setup dell'interfaccia grafica
        self._setup_gui()
        
        # Gestione evento chiusura
        master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _initialize_state(self):
        """Inizializza tutte le variabili di stato"""
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.status_message = tk.StringVar(value="Pronto. Seleziona le cartelle e avvia l'analisi.")
        
        self.analysis_thread: Optional[threading.Thread] = None
        self.results_queue = queue.Queue()
        self.analysis_results: List[AnalysisResult] = []
        
        self.analysis_active = False
        self.analysis_paused = False
        self.stop_requested = False

    def _setup_gui(self):
        """Configura tutti i componenti dell'interfaccia grafica"""
        self._create_folder_selection_frame()
        self._create_control_buttons()
        self._create_results_table()
        self._create_status_bar()

    # =============================================
    # Componenti GUI
    # =============================================

    def _create_folder_selection_frame(self):
        """Crea il frame per la selezione delle cartelle"""
        frame = ttk.LabelFrame(self.master, text="Cartelle")
        frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(frame, text="Cartella Input", command=self._select_input_folder).grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.input_folder, width=60).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(frame, text="Cartella Output", command=self._select_output_folder).grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.output_folder, width=60).grid(row=1, column=1, padx=5, pady=5)

    def _create_control_buttons(self):
        """Crea i pulsanti di controllo dell'analisi"""
        frame = ttk.LabelFrame(self.master, text="Controlli Analisi")
        frame.pack(padx=10, pady=5, fill="x")

        self.start_btn = ttk.Button(frame, text="Avvia Analisi", command=self.start_analysis)
        self.pause_btn = ttk.Button(frame, text="Pausa", state=tk.DISABLED, command=self.toggle_pause)
        self.stop_btn = ttk.Button(frame, text="Ferma", state=tk.DISABLED, command=self.stop_analysis)

        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.pause_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def _create_results_table(self):
        """Crea la tabella dei risultati"""
        frame = ttk.Frame(self.master)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ("File", "BPM", "Key", "Camelot", "Compatibili", "Energia")
        self.results_tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        
        # Configura colonne
        col_widths = {"File": 300, "BPM": 70, "Key": 70, "Camelot": 90, "Compatibili": 200, "Energia": 80}
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=col_widths[col], anchor=tk.CENTER if col != "File" else tk.W)

        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.results_tree.pack(fill="both", expand=True)

    def _create_status_bar(self):
        """Crea la barra di stato"""
        status_bar = ttk.Label(self.master, textvariable=self.status_message, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # =============================================
    # Logica di analisi
    # =============================================

    def start_analysis(self):
        """Avvia il processo di analisi"""
        if not self._validate_paths():
            return

        self._prepare_for_analysis()
        self.analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
        self.analysis_thread.start()
        self.master.after(100, self._process_queue)

    def _analysis_worker(self):
        """Thread worker per l'analisi dei file"""
        try:
            files = self._get_audio_files()
            total_files = len(files)
            
            for idx, file_path in enumerate(files, 1):
                if self.stop_requested:
                    break
                
                self._process_file(file_path, idx, total_files)
                
        finally:
            self.results_queue.put(("analysis_complete", None))
            self._cleanup_after_analysis()

    def _process_file(self, file_path: str, current: int, total: int):
        """Elabora un singolo file audio"""
        try:
            filename = os.path.basename(file_path)
            self._update_status(f"Analisi ({current}/{total}): {filename}")
            
            # Caricamento e analisi
            y, sr = librosa.load(file_path, sr=None, mono=True)
            bpm = self._calculate_bpm(y, sr)
            key, camelot = self._detect_key(y, sr)
            compatible_keys = self._find_compatible_keys(camelot)
            energy = self._calculate_energy(y, sr)
            
            # Creazione risultato
            result = AnalysisResult(
                filename=filename,
                bpm=bpm,
                key=key,
                camelot_code=camelot,
                compatible_keys=", ".join(compatible_keys),
                energy=energy,
                camelot_color=CAMELOT_COLORS.get(camelot, "white"),
                energy_color=ENERGY_COLORS.get(energy, "grey")
            )
            
            self.results_queue.put(("data", result))
            
        except Exception as e:
            error_msg = f"Errore analisi {filename}: {str(e)}"
            self.results_queue.put(("error", error_msg))

    # =============================================
    # Metodi di analisi audio
    # =============================================

    def _calculate_bpm(self, y: np.ndarray, sr: int) -> int:
        """Calcola il BPM di un segnale audio"""
        tempo = librosa.beat.tempo(y=y, sr=sr, aggregate=np.median)
        return int(np.round(tempo))

    def _detect_key(self, y: np.ndarray, sr: int) -> Tuple[str, str]:
        """Rileva la tonalità musicale"""
        try:
            # Separazione componente armonica
            y_harmonic = librosa.effects.harmonic(y, margin=8)
            
            # Chromagramma avanzato
            chroma = librosa.feature.chroma_cens(y=y_harmonic, sr=sr)
            chroma_avg = np.mean(chroma, axis=1)
            
            # Correlazione con profili
            major_profile = np.array([5.0, 2.0, 3.5, 2.1, 4.5, 4.0, 2.3, 4.9, 2.4, 3.7, 2.2, 3.0])
            minor_profile = np.array([5.0, 2.7, 3.5, 5.4, 2.5, 3.5, 2.5, 4.8, 4.0, 2.7, 3.3, 3.2])
            
            # ... (resto della logica di rilevamento chiave)
            
            return "C", "8B"  # Esempio semplificato
        except Exception as e:
            print(f"Errore rilevamento chiave: {str(e)}")
            return "N/A", "N/A"

    def _find_compatible_keys(self, camelot_code: str) -> List[str]:
        """Trova le tonalità compatibili"""
        # ... (implementazione esistente)
        return []

    def _calculate_energy(self, y: np.ndarray, sr: int) -> int:
        """Calcola il livello di energia"""
        # ... (implementazione esistente)
        return 5

    # =============================================
    # Gestione file e utilità
    # =============================================

    def _get_audio_files(self) -> List[str]:
        """Restituisce la lista di file audio nella cartella input"""
        supported_ext = ('.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a')
        return [
            os.path.join(self.input_folder.get(), f)
            for f in os.listdir(self.input_folder.get())
            if f.lower().endswith(supported_ext)
        ]

    def _validate_paths(self) -> bool:
        """Verifica la validità dei percorsi"""
        errors = []
        if not os.path.isdir(self.input_folder.get()):
            errors.append("Cartella input non valida")
        if not os.path.isdir(self.output_folder.get()):
            errors.append("Cartella output non valida")
        
        if errors:
            messagebox.showerror("Errore", "\n".join(errors))
            return False
        return True

    # =============================================
    # Gestione interfaccia e stato
    # =============================================

    def _prepare_for_analysis(self):
        """Prepara l'interfaccia per una nuova analisi"""
        self.analysis_active = True
        self.stop_requested = False
        self.analysis_results.clear()
        self.results_tree.delete(*self.results_tree.get_children())
        
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)

    def _cleanup_after_analysis(self):
        """Ripristina l'interfaccia dopo l'analisi"""
        self.analysis_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

    def _process_queue(self):
        """Elabora i messaggi dalla coda risultati"""
        try:
            while True:
                msg_type, data = self.results_queue.get_nowait()
                
                if msg_type == "data":
                    self._add_result_to_table(data)
                elif msg_type == "error":
                    self._show_error(data)
                elif msg_type == "analysis_complete":
                    self._finalize_analysis()
                    return
                    
        except queue.Empty:
            pass
        
        if self.analysis_thread.is_alive():
            self.master.after(100, self._process_queue)

    def _add_result_to_table(self, result: AnalysisResult):
        """Aggiunge un risultato alla tabella"""
        values = (
            result.filename,
            result.bpm,
            result.key,
            result.camelot_code,
            result.compatible_keys,
            result.energy
        )
        item_id = self.results_tree.insert("", tk.END, values=values, tags=(result.camelot_color,))
        self.results_tree.see(item_id)
        self.analysis_results.append(result)

    def _finalize_analysis(self):
        """Operazioni finali dopo l'analisi"""
        self._update_status("Analisi completata")
        self._save_results()
        self._cleanup_after_analysis()

    # =============================================
    # Metodi utilità e gestione errori
    # =============================================

    def _select_input_folder(self):
        """Seleziona la cartella di input"""
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def _select_output_folder(self):
        """Seleziona la cartella di output"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def toggle_pause(self):
        """Mette in pausa/riprende l'analisi"""
        self.analysis_paused = not self.analysis_paused
        self.pause_btn.config(text="Riprendi" if self.analysis_paused else "Pausa")
        self._update_status("Analisi in pausa" if self.analysis_paused else "Analisi ripresa")

    def stop_analysis(self):
        """Ferma l'analisi in corso"""
        self.stop_requested = True
        self._update_status("Interruzione analisi...")
        self.stop_btn.config(state=tk.DISABLED)

    def _save_results(self):
        """Salva i risultati in CSV"""
        try:
            df = pd.DataFrame([vars(r) for r in self.analysis_results])
            df.drop(columns=['camelot_color', 'energy_color'], inplace=True)
            
            output_path = os.path.join(self.output_folder.get(), "DJAnalyzer_Results.csv")
            df.to_csv(output_path, index=False)
            
            messagebox.showinfo("Salvataggio completato", f"Risultati salvati in:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", f"Impossibile salvare i risultati:\n{str(e)}")

    def _update_status(self, message: str):
        """Aggiorna la barra di stato"""
        self.status_message.set(message)
        self.master.update_idletasks()

    def _show_error(self, message: str):
        """Mostra un messaggio di errore"""
        self._update_status(f"ERRORE: {message}")
        messagebox.showerror("Errore", message)

    def _on_closing(self):
        """Gestisce la chiusura dell'applicazione"""
        if self.analysis_active and not messagebox.askokcancel("Uscita", "L'analisi è in corso. Uscire