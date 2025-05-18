import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import queue
# import time # Non sembra usato attivamente, commentato per ora
import librosa
import numpy as np
import pandas as pd
import traceback
from dataclasses import dataclass, fields # Aggiunto fields per il salvataggio CSV
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
    # Questi campi sono per la visualizzazione, potrebbero essere rimossi dal salvataggio CSV
    # se non si vogliono colonne extra lì. Li lascio per ora nella dataclass.
    _camelot_color_tag: str # Rinominato per chiarezza che è un tag
    _energy_color_tag: str  # Rinominato per chiarezza che è un tag

# Mappature costanti
CAMELOT_MAP = {
    'C': '8B', 'C#': '3B', 'D': '10B', 'D#': '5B', 'E': '12B', 'F': '7B',
    'F#': '2B', 'G': '9B', 'G#': '4B', 'A': '11B', 'A#': '6B', 'B': '1B',
    'Cm': '5A', 'C#m': '12A', 'Dm': '7A', 'D#m': '2A', 'Em': '9A', 'Fm': '4A',
    'F#m': '11A', 'Gm': '6A', 'G#m': '1A', 'Am': '8A', 'A#m': '3A', 'Bm': '10A'
}

CAMELOT_COLORS = { # Usato per i tag colore della Treeview
    '1A': 'medium orchid', '1B': 'sky blue', '2A': 'magenta', '2B': 'deep sky blue',
    '3A': 'dodger blue', '3B': 'green yellow', '4A': 'royal blue', '4B': 'chartreuse',
    '5A': 'spring green', '5B': 'yellow green', '6A': 'lawn green', '6B': 'dark sea green',
    '7A': 'gold', '7B': 'yellow', '8A': 'orange', '8B': 'light coral',
    '9A': 'dark orange', '9B': 'indian red', '10A': 'tomato', '10B': 'medium violet red',
    '11A': 'red', '11B': 'purple', '12A': 'dark violet', '12B': 'blue violet',
    'N/A': 'white' # Sfondo di default per la treeview
}

ENERGY_COLORS = { # Usato per i tag colore della Treeview (per la colonna Energia)
    1: "PaleTurquoise1", 2: "PaleTurquoise2", 3: "PaleGreen1", 4: "PaleGreen2",
    5: "SpringGreen2", 6: "SpringGreen3", 7: "yellow1", 8: "gold1",
    9: "dark orange", 10: "red1",
    # Aggiungiamo un colore di fallback se il valore non è in mappa
    "default": "grey"
}

# Profili tonali per l'algoritmo avanzato di stima della chiave
MAJOR_PROFILE_ADV = np.array([5.0, 2.0, 3.5, 2.1, 4.5, 4.0, 2.3, 4.9, 2.4, 3.7, 2.2, 3.0])
MINOR_PROFILE_ADV = np.array([5.0, 2.7, 3.5, 5.4, 2.5, 3.5, 2.5, 4.8, 4.0, 2.7, 3.3, 3.2])
# Normalizzare i profili può migliorare la stabilità della correlazione
# MAJOR_PROFILE_ADV = MAJOR_PROFILE_ADV / np.sum(MAJOR_PROFILE_ADV)
# MINOR_PROFILE_ADV = MINOR_PROFILE_ADV / np.sum(MINOR_PROFILE_ADV)

NOTES_MAJOR_STD = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTES_MINOR_STD = ['Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm']


# =============================================
# Classe principale dell'applicazione
# =============================================

class DJAnalyzerApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        # Titolo aggiornato per riflettere una nuova versione/iterazione
        master.title("DJAnalyzer Pro v0.7.0 (KeyDetector Integrato)") 
        master.geometry("1024x768")
        
        self._initialize_state()
        self._setup_gui()
        self._configure_treeview_tags() # Configura i tag colore una volta all'inizio
        
        master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _initialize_state(self):
        """Inizializza tutte le variabili di stato"""
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.status_message = tk.StringVar(value="Pronto. Seleziona le cartelle e avvia l'analisi.")
        
        self.analysis_thread: Optional[threading.Thread] = None
        self.results_queue = queue.Queue()
        self.analysis_results_data: List[AnalysisResult] = [] # Rinominato per chiarezza
        
        self.analysis_active = False
        self.analysis_paused_event = threading.Event() # Usiamo un Event per la pausa
        self.analysis_paused_event.set() # Inizia non in pausa (evento settato)
        self.stop_requested = False

        # Profili tonali come attributi di istanza (se vuoi renderli modificabili o centralizzati)
        # Altrimenti, possono essere costanti globali come definite sopra.
        # Per ora uso le costanti globali MAJOR_PROFILE_ADV, MINOR_PROFILE_ADV.

    def _setup_gui(self):
        """Configura tutti i componenti dell'interfaccia grafica"""
        # --- Frame per Selezione Cartelle ---
        folder_frame = ttk.LabelFrame(self.master, text="Cartelle")
        folder_frame.pack(padx=10, pady=10, fill="x", side=tk.TOP)

        self.select_input_button = ttk.Button(folder_frame, text="Cartella Input", command=self._select_input_folder)
        self.select_input_button.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=70).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        self.select_output_button = ttk.Button(folder_frame, text="Cartella Output", command=self._select_output_folder)
        self.select_output_button.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=70).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        folder_frame.columnconfigure(1, weight=1) # Fa espandere l'entry

        # --- Frame per Controlli Analisi ---
        control_frame = ttk.LabelFrame(self.master, text="Controlli Analisi")
        control_frame.pack(padx=10, pady=5, fill="x", side=tk.TOP)

        self.start_btn = ttk.Button(control_frame, text="Avvia Analisi", command=self.start_analysis)
        self.pause_btn = ttk.Button(control_frame, text="Pausa", state=tk.DISABLED, command=self.toggle_pause)
        self.stop_btn = ttk.Button(control_frame, text="Ferma", state=tk.DISABLED, command=self.stop_analysis)

        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.pause_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Tabella dei Risultati ---
        table_frame = ttk.Frame(self.master)
        table_frame.pack(padx=10, pady=10, fill="both", expand=True, side=tk.TOP)

        columns = ("File", "BPM", "Key", "Camelot", "Compatibili", "Energia")
        self.results_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        col_widths = {"File": 350, "BPM": 60, "Key": 70, "Camelot": 80, "Compatibili": 200, "Energia": 70}
        for col_name in columns:
            self.results_tree.heading(col_name, text=col_name)
            self.results_tree.column(col_name, width=col_widths[col_name], 
                                     anchor=tk.CENTER if col_name not in ["File", "Compatibili"] else tk.W,
                                     stretch=tk.YES if col_name == "File" else tk.NO)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x") # Metti hsb sotto la tabella
        self.results_tree.pack(fill="both", expand=True)
        table_frame.columnconfigure(0, weight=1) # Permette alla tabella di espandersi

        # --- Barra di Stato ---
        status_bar = ttk.Label(self.master, textvariable=self.status_message, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0), padx=0)

    def _configure_treeview_tags(self):
        """Configura i tag colore per la Treeview una sola volta."""
        for color_name in CAMELOT_COLORS.values():
            if color_name != 'white': # 'white' è lo sfondo di default
                try:
                    self.results_tree.tag_configure(color_name, background=color_name)
                except tk.TclError: # Può succedere se il colore non è valido per Tk
                    print(f"Attenzione: Colore Camelot '{color_name}' non valido per tag Treeview.")
        
        for color_name in ENERGY_COLORS.values():
            tag_name = f"energy_{color_name}" # Crea un nome tag univoco
            try:
                self.results_tree.tag_configure(tag_name, background=color_name)
            except tk.TclError:
                 print(f"Attenzione: Colore Energia '{color_name}' non valido per tag Treeview.")
        # Tag per testo (se necessario, es. testo bianco su sfondi scuri)
        # self.results_tree.tag_configure("white_text", foreground="white")


    # =============================================
    # Logica di analisi (come da DJAnalyzer069ds.py, ma con analisi audio completate)
    # =============================================

    def start_analysis(self):
        if not self._validate_paths():
            return

        self._prepare_for_analysis_ui_state()
        
        # Ottieni la lista dei file PRIMA di avviare il thread
        try:
            audio_files = self._get_audio_files()
            if not audio_files:
                messagebox.showinfo("Info", "Nessun file audio supportato trovato nella cartella selezionata.")
                self._cleanup_after_analysis_ui_state() # Ripristina UI se non ci sono file
                return
        except Exception as e:
            messagebox.showerror("Errore Lettura Cartella", f"Errore durante la lettura dei file: {str(e)}")
            self._cleanup_after_analysis_ui_state()
            return
            
        self.analysis_thread = threading.Thread(target=self._analysis_worker, args=(audio_files,), daemon=True)
        self.analysis_thread.start()
        self.master.after(100, self._process_results_queue) # Rinominato per chiarezza

    def _analysis_worker(self, files_to_analyze: List[str]):
        """Thread worker per l'analisi dei file"""
        self._update_status("Avvio analisi in background...")
        total_files = len(files_to_analyze)
        try:
            for idx, file_path in enumerate(files_to_analyze, 1):
                self.analysis_paused_event.wait() # Il thread si blocca qui se l'evento non è settato (pausa)
                if self.stop_requested:
                    self._update_status("Analisi interrotta dall'utente.")
                    break
                
                self._process_single_file(file_path, idx, total_files)
        except Exception as e:
            # Log errore nel thread worker
            print(f"Errore grave nel thread worker: {str(e)}")
            traceback.print_exc()
            self.results_queue.put(("error", f"Errore critico nel thread: {str(e)}"))
        finally:
            # Assicura che il completamento venga segnalato
            self.results_queue.put(("analysis_complete", None))
            print("DEBUG WORKER: Segnale 'analysis_complete' inviato alla coda.")


    def _process_single_file(self, file_path: str, current_idx: int, total_files: int):
        """Elabora un singolo file audio e mette il risultato in coda."""
        filename = os.path.basename(file_path)
        self.results_queue.put(("status_update", f"Analisi ({current_idx}/{total_files}): {filename}"))
        
        try:
            # Caricamento audio (una sola volta per tutte le analisi su questo file)
            # Aumentata durata per migliore analisi chiave, ma può rallentare. Tarare se necessario.
            y, sr = librosa.load(file_path, sr=None, mono=True, duration=90) 
            
            bpm = self._calculate_bpm(y, sr)
            key_traditional, camelot_code = self._detect_key(y, sr) # NUOVO METODO
            compatible_keys_list = self._find_compatible_keys(camelot_code)
            energy_scaled = self._calculate_energy(y, sr) # NUOVO METODO
            
            camelot_color_tag = CAMELOT_COLORS.get(camelot_code, CAMELOT_COLORS['N/A'])
            # Per l'energia, costruiamo il nome del tag per coerenza con _configure_treeview_tags
            energy_color_name = ENERGY_COLORS.get(energy_scaled, ENERGY_COLORS['default'])
            energy_color_tag_name = f"energy_{energy_color_name}"

            result = AnalysisResult(
                filename=filename,
                bpm=bpm,
                key=key_traditional,
                camelot_code=camelot_code,
                compatible_keys=", ".join(compatible_keys_list),
                energy=energy_scaled,
                _camelot_color_tag=camelot_color_tag,
                _energy_color_tag=energy_color_tag_name 
            )
            self.results_queue.put(("new_data", result))
            
        except Exception as e:
            error_msg = f"Errore durante l'analisi di {filename}: {str(e)}"
            print(f"ECCEZIONE in _process_single_file per {filename}:")
            traceback.print_exc()
            self.results_queue.put(("error", error_msg))

    # =============================================
    # Metodi di analisi audio (COMPLETATI)
    # =============================================

    def _calculate_bpm(self, y: np.ndarray, sr: int) -> int:
        """Calcola il BPM di un segnale audio"""
        try:
            # Usare aggregate=np.median è più robusto per BPM
            tempo_values = librosa.beat.tempo(y=y, sr=sr, aggregate=None)
            if tempo_values.size > 0:
                return int(round(np.median(tempo_values)))
            return 0 # Fallback se non trova tempi
        except Exception as e:
            print(f"Errore calcolo BPM: {str(e)}")
            return 0

    def _detect_bass_note_chroma_idx(self, y: np.ndarray, sr: int) -> Optional[int]:
        """Helper per rilevare la nota di basso predominante (indice cromatico 0-11)."""
        try:
            # CQT focalizzato sulle basse frequenze (es. 3 ottave da C1)
            cqt = np.abs(librosa.cqt(y, sr=sr, fmin=librosa.note_to_hz('C1'), 
                                   n_bins=36, bins_per_octave=12)) # 12 bin per ottava
            bass_chroma_energy = np.zeros(12)
            for i in range(12):
                # Somma l'energia per ciascuna delle 12 classi cromatiche attraverso le ottave analizzate
                bass_chroma_energy[i] = np.sum(cqt[i : cqt.shape[0] : 12, :])
            
            bass_note_idx = np.argmax(bass_chroma_energy)
            # print(f"DEBUG BASS: Nota di basso rilevata (indice): {bass_note_idx} ({NOTES_MAJOR_STD[bass_note_idx]})")
            return bass_note_idx
        except Exception as e:
            print(f"Errore nel rilevamento nota di basso: {str(e)}")
            # traceback.print_exc() # Decommenta per debug più dettagliato
            return None # Restituisce None se fallisce, così la logica chiamante può gestirlo

    def _detect_key(self, y: np.ndarray, sr: int) -> Tuple[str, str]:
        """Rileva la tonalità musicale usando un algoritmo avanzato."""
        try:
            # 1. Separazione componente armonica
            y_harmonic = librosa.effects.harmonic(y, margin=8)
            
            # 2. Chromagramma avanzato (CENS è robusto, ma CQT con tuning può essere preciso)
            # Proviamo CENS come nelle bozze precedenti
            chroma_features = librosa.feature.chroma_cens(y=y_harmonic, sr=sr, bins_per_octave=12, n_chroma=12)
            chroma_avg_profile = np.mean(chroma_features, axis=1)

            # Normalizza il profilo cromatico del brano (opzionale, ma può aiutare)
            # if np.sum(chroma_avg_profile) > 0:
            #    chroma_avg_profile = chroma_avg_profile / np.sum(chroma_avg_profile)
            
            # 3. Profili tonali (globali o self. se li hai messi in __init__)
            # Assicurati che MAJOR_PROFILE_ADV e MINOR_PROFILE_ADV siano definiti
            
            # 4. Correlazione
            scores = [] # Lista di dizionari per tracciare meglio
            for i in range(12): # Per ogni possibile tonica (C=0, C#=1, ..., B=11)
                # Per la tonalità maggiore con tonica 'i':
                # Ruotiamo il profilo cromatico del brano per allineare la sua 'i'-esima nota con la 'C' del profilo di C Maggiore
                # Oppure, equivalentemente, ruotiamo il profilo di C Maggiore per allinearlo con la tonica 'i'
                shifted_major_template = np.roll(MAJOR_PROFILE_ADV, i)
                major_corr = np.corrcoef(chroma_avg_profile, shifted_major_template)[0, 1]
                
                shifted_minor_template = np.roll(MINOR_PROFILE_ADV, i)
                minor_corr = np.corrcoef(chroma_avg_profile, shifted_minor_template)[0, 1]
                
                scores.append({'tonic_pitch_class': i, 'type': 'major', 'score': major_corr if not np.isnan(major_corr) else -1})
                scores.append({'tonic_pitch_class': i, 'type': 'minor', 'score': minor_corr if not np.isnan(minor_corr) else -1})
            
            # 5. Rilevamento nota di basso
            bass_note_idx = self._detect_bass_note_chroma_idx(y, sr) # y originale per il basso
            
            # 6. Applica peso del basso ai punteggi
            if bass_note_idx is not None:
                bass_weight = 0.3 # Valore empirico, da tarare
                for score_info in scores:
                    # Se la tonica della tonalità candidata (maggiore o minore) corrisponde alla nota di basso
                    if score_info['tonic_pitch_class'] == bass_note_idx:
                        score_info['score'] += bass_weight
            
            # 7. Trova la migliore tonalità
            if not scores: return "N/A", "N/A" # Se scores è vuoto per qualche motivo

            best_score_info = max(scores, key=lambda x: x['score'])
            
            best_tonic_idx = best_score_info['tonic_pitch_class']
            best_type = best_score_info['type']

            traditional_key_name: str
            if best_type == 'major':
                traditional_key_name = NOTES_MAJOR_STD[best_tonic_idx]
            else: # minor
                traditional_key_name = NOTES_MINOR_STD[best_tonic_idx]
                
            camelot_code = CAMELOT_MAP.get(traditional_key_name, "N/A")
            
            # print(f"DEBUG KEY: File: {os.path.basename(y[:10]) if hasattr(y, 'name') else 'buffer'}, Trad: {traditional_key_name}, Camelot: {camelot_code}, Score: {best_score_info['score']:.3f}")
            return traditional_key_name, camelot_code
            
        except Exception as e:
            print(f"Errore dettagliato in _detect_key: {str(e)}")
            traceback.print_exc()
            return "N/A", "N/A"

    def _find_compatible_keys(self, camelot_code: str) -> List[str]:
        if not camelot_code or camelot_code == "N/A":
            return []
        try:
            num = int(camelot_code[:-1])
            mode = camelot_code[-1].upper()
        except ValueError:
            return [] # Formato Camelot non valido

        compatible = [camelot_code]
        compatible.append(f"{ (num - 2 + 12) % 12 + 1 }{mode}") # num-1 (corretto)
        compatible.append(f"{ (num % 12) + 1 }{mode}")     # num+1 (corretto)
        compatible.append(f"{num}{'B' if mode == 'A' else 'A'}")
        
        # Filtra per assicurarsi che siano codici Camelot validi (opzionale ma sicuro)
        valid_camelot_codes = set(CAMELOT_MAP.values())
        return sorted([c for c in list(set(compatible)) if c in valid_camelot_codes or c == camelot_code])


    def _calculate_energy(self, y: np.ndarray, sr: int) -> int:
        try:
            rms_frames = librosa.feature.rms(y=y)[0]
            if rms_frames.size == 0: return 1 # Evita errore su array vuoto

            energy_mean = np.mean(rms_frames)
            energy_std = np.std(rms_frames)
            energy_score = energy_mean + 0.5 * energy_std
            
            scaled_value = 1 
            if energy_score > 0: 
                min_expected_score = 0.055 # Valori da tarare
                max_expected_score = 0.130 # Valori da tarare
                
                if energy_score <= min_expected_score:
                    scaled_value = 1
                elif energy_score >= max_expected_score:
                    scaled_value = 10
                else:
                    scaled_value = 1 + 9 * (energy_score - min_expected_score) / (max_expected_score - min_expected_score)
            
            return int(np.clip(round(scaled_value), 1, 10))
        except Exception as e:
            print(f"Errore nel calcolo energia: {str(e)}")
            return 1

    # =============================================
    # Gestione file e utilità (come da DJAnalyzer069ds.py)
    # =============================================
    def _get_audio_files(self) -> List[str]:
        input_dir = self.input_folder.get()
        if not input_dir or not os.path.isdir(input_dir):
            return []
            
        supported_ext = ('.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a')
        audio_files = []
        for f in os.listdir(input_dir):
            if f.lower().endswith(supported_ext):
                full_path = os.path.join(input_dir, f)
                if os.path.isfile(full_path): # Assicura sia un file
                    audio_files.append(full_path)
        return audio_files

    def _validate_paths(self) -> bool:
        errors = []
        if not self.input_folder.get() or not os.path.isdir(self.input_folder.get()):
            errors.append("Cartella input non valida o non selezionata.")
        if not self.output_folder.get() or not os.path.isdir(self.output_folder.get()):
            errors.append("Cartella output non valida o non selezionata.")
        
        if errors:
            messagebox.showerror("Errore Percorsi", "\n".join(errors))
            return False
        return True

    # =============================================
    # Gestione interfaccia e stato (come da DJAnalyzer069ds.py, con piccole correzioni)
    # =============================================
    def _prepare_for_analysis_ui_state(self): # Rinominato per chiarezza
        """Prepara l'interfaccia per una nuova analisi"""
        self.analysis_active = True
        self.stop_requested = False
        self.analysis_paused_event.set() # Assicura che non parta in pausa
        
        self.analysis_results_data.clear()
        self.results_tree.delete(*self.results_tree.get_children())
        
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text="Pausa") # Testo iniziale Pausa
        self.stop_btn.config(state=tk.NORMAL)
        self.select_input_button.config(state=tk.DISABLED)
        self.select_output_button.config(state=tk.DISABLED)
        self._update_status("Preparazione analisi...")


    def _cleanup_after_analysis_ui_state(self): # Rinominato per chiarezza
        """Ripristina l'interfaccia dopo l'analisi o in caso di errore iniziale."""
        self.analysis_active = False
        # self.stop_requested rimane com'è, verrà resettato al prossimo start
        # self.analysis_paused_event rimane settato (non in pausa)

        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="Pausa")
        self.stop_btn.config(state=tk.DISABLED)
        self.select_input_button.config(state=tk.NORMAL)
        self.select_output_button.config(state=tk.NORMAL)
        self.analysis_thread = None # Resetta il riferimento al thread


    def _process_results_queue(self): # Rinominato per chiarezza
        try:
            while True: # Processa tutti i messaggi disponibili
                msg_type, data = self.results_queue.get_nowait()
                
                if msg_type == "new_data": # Rinominato per chiarezza
                    self._add_result_to_table(data)
                elif msg_type == "error":
                    self._show_error_message(data) # Rinominato per chiarezza
                elif msg_type == "status_update": # Nuovo tipo di messaggio
                    self._update_status(data)
                elif msg_type == "analysis_complete":
                    print("DEBUG QUEUE: Ricevuto 'analysis_complete'.")
                    self._finalize_analysis_flow() # Rinominato per chiarezza
                    return # IMPORTANTE: esci dal loop e ferma il polling after()
                    
        except queue.Empty:
            pass # Normale, la coda è vuota
        
        # Ricontrolla la coda solo se l'analisi dovrebbe essere attiva
        # (il thread è vivo O ci sono ancora cose nella coda E non è stato richiesto lo stop)
        if self.analysis_active and not self.stop_requested:
            if (self.analysis_thread and self.analysis_thread.is_alive()) or not self.results_queue.empty():
                self.master.after(100, self._process_results_queue)
            else:
                # Thread morto, coda vuota, ma analysis_complete non ancora processato (improbabile se il finally del worker funziona)
                # o l'analisi è finita ma il messaggio è ancora in coda.
                # Forziamo un ultimo check se non è già in finalizzazione.
                if not self.results_queue.empty(): # Controlla di nuovo la coda
                     self.master.after(100, self._process_results_queue)
                else:
                    print("DEBUG QUEUE: Thread non vivo, coda vuota, stop non richiesto. L'analisi dovrebbe essere completa.")
                    # Se analysis_complete non è stato inviato/ricevuto, questo è un problema
                    # Ma il finally nel worker dovrebbe averlo gestito.
                    # Per sicurezza, se l'UI non è già stata resettata, fallo.
                    if self.start_btn['state'] == tk.DISABLED: # Un modo per vedere se l'UI è ancora in "analisi"
                        self._finalize_analysis_flow() # Tenta di finalizzare


    def _add_result_to_table(self, result: AnalysisResult):
        values = (
            result.filename, result.bpm, result.key,
            result.camelot_code, result.compatible_keys, result.energy
        )
        # Applica il tag colore per Camelot. Il tag per l'energia è più complesso
        # da applicare a una singola cella in ttk.Treeview senza subclassing.
        # Per ora, coloriamo l'intera riga con il colore Camelot.
        # Il tag colore deve essere il nome del colore stesso, come configurato.
        item_id = self.results_tree.insert("", tk.END, values=values, tags=(result._camelot_color_tag,))
        self.results_tree.see(item_id) # Scrolla per vedere l'ultimo elemento
        self.analysis_results_data.append(result) # Aggiungi ai dati per il CSV

    def _finalize_analysis_flow(self): # Rinominato per chiarezza
        """Operazioni finali dopo il completamento di TUTTE le analisi."""
        if self.stop_requested:
            self._update_status("Analisi interrotta e finalizzata.")
        else:
            self._update_status("Analisi completata. Salvataggio risultati...")
        
        self._save_results_to_csv() # Rinominato
        self._cleanup_after_analysis_ui_state()
        # Assicura che non ci siano chiamate after() pendenti se siamo arrivati qui
        # (il return in _process_results_queue dopo analysis_complete dovrebbe averlo gestito)
        print("DEBUG: Flusso di analisi finalizzato.")


    # =============================================
    # Metodi utilità e gestione eventi (come da DJAnalyzer069ds.py)
    # =============================================
    def _select_input_folder(self):
        folder = filedialog.askdirectory(title="Seleziona Cartella Input Audio")
        if folder:
            self.input_folder.set(folder)
            self._update_status(f"Cartella Input: {folder}")

    def _select_output_folder(self):
        folder = filedialog.askdirectory(title="Seleziona Cartella Output per CSV")
        if folder:
            self.output_folder.set(folder)
            self._update_status(f"Cartella Output: {folder}")

    def toggle_pause(self):
        if not self.analysis_active: return

        if self.analysis_paused_event.is_set(): # Se è settato, significa che NON è in pausa
            self.analysis_paused_event.clear() # Mette in pausa il worker
            self.pause_btn.config(text="Riprendi")
            self._update_status("Analisi in pausa.")
        else:
            self.analysis_paused_event.set() # Riprende il worker
            self.pause_btn.config(text="Pausa")
            self._update_status("Analisi ripresa.")


    def stop_analysis(self):
        if not self.analysis_active: return

        self.stop_requested = True
        self.analysis_paused_event.set() # Sblocca il worker se era in pausa per permettergli di vedere stop_requested
        self._update_status("Interruzione analisi in corso...")
        self.stop_btn.config(state=tk.DISABLED) # Disabilita subito per evitare click multipli
        self.pause_btn.config(state=tk.DISABLED) # Anche il pulsante pausa
        # Il thread worker noterà self.stop_requested e terminerà, 
        # inviando poi 'analysis_complete' che chiamerà _finalize_analysis_flow.

    def _save_results_to_csv(self): # Rinominato per chiarezza
        if not self.analysis_results_data:
            self._update_status("Nessun dato da salvare.")
            # messagebox.showinfo("Info", "Nessun dato da salvare.") # Forse non necessario se lo status lo dice
            return

        output_dir = self.output_folder.get()
        if not output_dir or not os.path.isdir(output_dir):
            error_msg = "Cartella di output non valida. Impossibile salvare il CSV."
            self._show_error_message(error_msg)
            return

        # Prepara i dati escludendo i campi interni (che iniziano con '_')
        # e mantenendo l'ordine desiderato
        column_order = [f.name for f in fields(AnalysisResult) if not f.name.startswith('_')]
        
        # Crea lista di dizionari per il DataFrame
        df_data = []
        for r_obj in self.analysis_results_data:
            row_dict = {}
            for col_name in column_order:
                row_dict[col_name] = getattr(r_obj, col_name)
            df_data.append(row_dict)
            
        df = pd.DataFrame(df_data, columns=column_order)
        
        try:
            filename = "DJAnalyzer_Results.csv" 
            full_path = os.path.join(output_dir, filename)
            
            df.to_csv(full_path, index=False, encoding='utf-8-sig')
            
            success_msg = f"Risultati salvati in: {full_path}"
            self._update_status(success_msg)
            messagebox.showinfo("Salvataggio Completato", success_msg)
        except Exception as e:
            error_msg = f"Errore durante il salvataggio del CSV: {str(e)}"
            self._show_error_message(error_msg, is_fatal=False) # Non è fatale per l'app

    def _update_status(self, message: str):
        self.status_message.set(message)
        # print(f"STATUS GUI: {message}") # Decommenta per debug pesante dell'UI
        # self.master.update_idletasks() # Usare con cautela, può causare problemi se chiamato troppo spesso da thread

    def _show_error_message(self, message: str, is_fatal: bool = True): # Rinominato
        """Mostra un messaggio di errore all'utente."""
        self._update_status(f"ERRORE: {message}")
        messagebox.showerror("Errore DJAnalyzer", message)
        if is_fatal:
            # Potremmo voler resettare l'UI in caso di errore fatale nel thread
            self._cleanup_after_analysis_ui_state()


    def _on_closing(self):
        """Gestisce la chiusura dell'applicazione in modo sicuro."""
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askokcancel("Uscita - DJAnalyzer", 
                                     "L'analisi è ancora in corso.\nVuoi davvero chiudere il programma?"):
                self.stop_requested = True
                self.analysis_paused_event.set() # Sblocca il thread se in pausa
                # Dare un po' di tempo al thread per terminare
                # Non bloccare la GUI per troppo tempo con join() qui
                # Il thread dovrebbe uscire e inviare analysis_complete
                print("DEBUG: Chiusura richiesta durante analisi. Thread dovrebbe terminare.")
                # Potremmo aspettare un timeout breve e poi distruggere
                # self.master.after(700, self.master.destroy) # Distrugge dopo un po'
                self.master.destroy() # Tentativo di chiusura più rapida
            else:
                return # Non chiudere
        else:
            self.master.destroy()

# =============================================
# Avvio dell'applicazione
# =============================================
if __name__ == "__main__":
    root = tk.Tk()
    # Style per ttk (opzionale, per un look migliore)
    # style = ttk.Style(root)
    # print(style.theme_names()) # Vedi temi disponibili
    # try:
    #    style.theme_use('clam') # 'clam', 'alt', 'default', 'vista', 'xpnative'
    # except tk.TclError:
    #    print("Tema 'clam' non disponibile, usando default.")
       
    app = DJAnalyzerApp(root)
    root.mainloop()