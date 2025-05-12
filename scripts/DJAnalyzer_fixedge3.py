# DJAnalyzer - Programma completo (Analisi BPM, Chiave, Energia, Spettro)
# Versione v0.4 - THREADING GUI, PAUSA MIGLIORATA, MAPPE CAMELOT CORRETTE

import os
import threading
from queue import Queue, Empty as QueueEmpty
import io
import librosa
import librosa.display
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt

# --- Costanti e Mappe ---
PITCH_MAP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# Mappatura alternativa per bemolle se necessario per l'output dell'algoritmo di chiave
PITCH_MAP_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

CAMELOT_MAP = {
    # Minori (A)
    "Abm": "1A", "G#m": "1A",
    "Ebm": "2A", "D#m": "2A",
    "Bbm": "3A", "A#m": "3A",
    "Fm":  "4A",
    "Cm":  "5A",
    "Gm":  "6A",
    "Dm":  "7A",
    "Am":  "8A",
    "Em":  "9A",
    "Bm":  "10A",
    "F#m": "11A",
    "C#m": "12A", "Dbm": "12A",
    # Maggiori (B)
    "B":   "1B", "Cb": "1B",
    "F#":  "2B", "Gb":  "2B",
    "Db":  "3B", "C#":  "3B", # C# Major è Db Major
    "Ab":  "4B", "G#":  "4B",
    "Eb":  "5B", "D#":  "5B",
    "Bb":  "6B", "A#":  "6B",
    "F":   "7B",
    "C":   "8B",
    "G":   "9B",
    "D":   "10B",
    "A":   "11B",
    "E":   "12B",
}

CAMELOT_COLOR_MAP = {
    "1A": "light sky blue",  "1B": "sky blue",
    "2A": "light blue",      "2B": "steel blue",
    "3A": "dodger blue",     "3B": "green yellow", # Db Major
    "4A": "medium sea green","4B": "chartreuse",   # Ab Major
    "5A": "spring green",    "5B": "yellow green", # Eb Major
    "6A": "lawn green",      "6B": "yellow",       # Bb Major
    "7A": "gold",            "7B": "dark salmon",  # F Major
    "8A": "orange",          "8B": "light coral",  # C Major
    "9A": "dark orange",     "9B": "indian red",   # G Major
    "10A": "tomato",         "10B": "medium violet red", # D Major
    "11A": "hot pink",       "11B": "purple",       # A Major
    "12A": "medium orchid",  "12B": "blue violet",  # E Major
    "N/A": "grey70"
}

ENERGY_RMS_COLOR_PALETTE = {
    1: "Gray", 2: "LightBlue", 3: "Cyan", 4: "LightGreen", 5: "Lime",
    6: "Yellow", 7: "Orange", 8: "Red", 9: "Magenta", 10: "HotPink"
}

# --- Funzioni di Analisi ---
def analyze_key_internal(y, sr):
    try:
        # L'algoritmo di chiave qui è ancora molto rudimentale e necessita di miglioramenti significativi!
        # (Usare Krumhansl-Schmuckler o ispirarsi a KeyFinder/Mixxx)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, n_chroma=12, bins_per_octave=36)
        chroma_profile = np.mean(chroma, axis=1)
        
        # Profili di Krumhansl-Schmuckler (approssimati)
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.78, 3.98, 2.69, 3.34, 3.17])

        best_corr_maj, key_idx_maj = -np.inf, 0
        best_corr_min, key_idx_min = -np.inf, 0

        for i in range(12):
            corr_maj = np.corrcoef(chroma_profile, np.roll(major_profile, i))[0, 1]
            if corr_maj > best_corr_maj: best_corr_maj, key_idx_maj = corr_maj, i
            
            corr_min = np.corrcoef(chroma_profile, np.roll(minor_profile, i))[0, 1]
            if corr_min > best_corr_min: best_corr_min, key_idx_min = corr_min, i
        
        # Semplice decisione basata sulla correlazione più alta
        # Un approccio migliore potrebbe considerare la differenza tra le correlazioni
        if best_corr_maj >= best_corr_min: # Preferisce maggiore in caso di parità o quasi
            key_label = PITCH_MAP[key_idx_maj]
        else:
            key_label = PITCH_MAP[key_idx_min] + 'm'
            
        camelot = CAMELOT_MAP.get(key_label, 'N/A')
        return key_label, camelot
    except Exception as e:
        print(f"Errore (analyze_key_internal): {e}")
        return 'N/A', 'N/A'

def analyze_bpm_internal(y, sr):
    try:
        tempo_array = librosa.beat.tempo(y=y, sr=sr, aggregate=None) # Ottieni tutti i tempi stimati
        if tempo_array.size > 0:
            # Potremmo usare una logica più sofisticata per scegliere il BPM corretto
            # (es. median, o quello più vicino a un range tipico)
            bpm = int(round(np.median(tempo_array))) # Usa la mediana dei tempi trovati
        else:
            bpm = 0
        return bpm
    except Exception as e:
        print(f"Errore (analyze_bpm_internal): {e}")
        return 0

def analyze_energy_rms_internal(y): # Rinominata per chiarezza che è basata su RMS
    try:
        rms = librosa.feature.rms(y=y)[0] # Prendi il primo (e unico) array RMS
        energy_raw = float(np.mean(rms)) if rms.size > 0 and np.all(np.isfinite(rms)) else 0.0
        
        print(f"DEBUG Energia: RMS grezzo = {energy_raw:.6f}") # DEBUG

        if energy_raw == 0.0:
            scaled_energy = 1
        else:
            # Questa scalatura è ancora un placeholder e va rivista
            # Potremmo usare una scalatura logaritmica o basata su percentile
            scaled_energy = min(10, max(1, int(np.ceil(energy_raw * 50)))) # Aumentato il fattore per test
        
        print(f"DEBUG Energia: RMS Scalata = {scaled_energy}") # DEBUG
        color = ENERGY_RMS_COLOR_PALETTE.get(scaled_energy, "Gray")
        return scaled_energy, color
    except Exception as e:
        print(f"Errore (analyze_energy_rms_internal): {e}")
        return 1, "Gray"

def find_compatible_keys(camelot_key):
    if not camelot_key or camelot_key == 'N/A': return []
    try:
        num_str, letter = camelot_key[:-1], camelot_key[-1]
        if not num_str.isdigit() or letter not in ('A', 'B'): return []
        num = int(num_str)
        
        compat = [
            f"{num}{letter}",
            f"{(num % 12) + 1}{letter}",
            f"{(num - 2 + 12) % 12 + 1}{letter}", # (num-1+12-1)%12 + 1
            f"{num}{'A' if letter == 'B' else 'B'}"
        ]
        return sorted(list(set(c for c in compat if c in CAMELOT_MAP.values() or c[:-1].isdigit() and int(c[:-1]) in range(1,13) ))) # Filtra per validità
    except Exception as e:
        print(f"Errore (find_compatible_keys) per {camelot_key}: {e}")
        return []

# --- Interfaccia Grafica ---
class DJAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJAnalyzer v0.4 (Threaded)")
        self.geometry("1100x800") # Leggermente più largo
        
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        
        self.analysis_thread = None
        self.analysis_queue = Queue()
        self.pause_event = threading.Event()
        self.stop_event = threading.Event() # Per fermare il thread in modo pulito

        self.current_file_label = tk.StringVar(value="Pronto per l'analisi.")
        self.last_analysis_status_message = "" # Per ripristinare dopo la pausa
        
        self.setup_ui()
        self.image_ref = None # Per matplotlib su canvas

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # ... (UI Setup come nella versione precedente, ma con "Colore Camelot" e "Colore Energia RMS")
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=(10,5)) # Meno pady bottom
        # ... (Input/Output Entries and Buttons come prima)
        ttk.Label(control_frame, text="Cartella Input:").pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(control_frame, textvariable=self.input_folder, width=30)
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.browse_input_button = ttk.Button(control_frame, text="Sfoglia Input", command=self.browse_input)
        self.browse_input_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Cartella Output:").pack(side=tk.LEFT, padx=(10, 0))
        self.output_entry = ttk.Entry(control_frame, textvariable=self.output_folder, width=30)
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.browse_output_button = ttk.Button(control_frame, text="Sfoglia Output", command=self.browse_output)
        self.browse_output_button.pack(side=tk.LEFT, padx=5)


        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=0)
        self.start_button = ttk.Button(action_frame, text="Avvia Analisi", command=self.start_analysis_thread)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = ttk.Button(action_frame, text="Pausa Analisi", command=self.toggle_pause_analysis, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(action_frame, text="Ferma Analisi", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)


        ttk.Label(self, textvariable=self.current_file_label, font=("Arial", 10), foreground="blue").pack(pady=(2, 5), fill=tk.X, padx=10)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        # ... (Scrollbars come prima)
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scrollbar_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(tree_frame, 
                                 columns=("File", "BPM", "Key", "Camelot", "Colore Camelot", "Compatibili", "Energia RMS", "Colore RMS"), 
                                 show="headings", 
                                 yscrollcommand=tree_scrollbar_y.set,
                                 xscrollcommand=tree_scrollbar_x.set)
        
        cols_config = { 
            "File": 220, "BPM": 50, "Key": 60, "Camelot": 60, 
            "Colore Camelot": 90, 
            "Compatibili": 130, "Energia RMS": 80, "Colore RMS": 90
        }
        for col, width in cols_config.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=max(40,width // 2), anchor=tk.CENTER if col not in ["File", "Compatibili", "Colore Camelot"] else tk.W)
        
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_scrollbar_y.config(command=self.tree.yview)
        tree_scrollbar_x.config(command=self.tree.xview)

        self.spectrum_display_frame = ttk.LabelFrame(self, text="Spettro Audio")
        self.spectrum_display_frame.pack(fill=tk.X, expand=False, padx=10, pady=(0,5), ipady=5)
        self.spectrum_canvas = tk.Canvas(self.spectrum_display_frame, bg="black", height=180) # Altezza ridotta
        self.spectrum_canvas.pack(fill=tk.X, expand=True, padx=5, pady=5)


    def browse_input(self): # ... (come prima)
        folder = filedialog.askdirectory(title="Seleziona Cartella Input Audio")
        if folder: self.input_folder.set(folder)

    def browse_output(self): # ... (come prima)
        folder = filedialog.askdirectory(title="Seleziona Cartella Output per CSV")
        if folder: self.output_folder.set(folder)

    def toggle_pause_analysis(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="Pausa Analisi")
            self.current_file_label.set(self.last_analysis_status_message)
        else:
            self.pause_event.set()
            self.pause_button.config(text="Riprendi Analisi")
            self.last_analysis_status_message = self.current_file_label.get()
            self.current_file_label.set("Analisi in pausa...")
            
    def stop_analysis(self):
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askyesno("Ferma Analisi", "Vuoi davvero fermare l'analisi in corso?"):
                self.stop_event.set() # Segnala al thread di fermarsi
                if self.pause_event.is_set(): # Se era in pausa, sbloccalo per farlo terminare
                    self.pause_event.clear()
                self.current_file_label.set("Interruzione analisi in corso...")
                # Non chiamare join() qui per non bloccare la GUI, il reset avverrà
                # quando il thread effettivamente termina e process_analysis_queue lo rileva.
        else:
            self.reset_ui_after_analysis()


    def start_analysis_thread(self):
        # ... (controlli e creazione cartella output come prima) ...
        input_dir = self.input_folder.get()
        output_dir = self.output_folder.get()
        if not input_dir or not output_dir:
            messagebox.showerror("Errore", "Seleziona sia la cartella di Input che quella di Output."); return
        if not os.path.isdir(input_dir):
            messagebox.showerror("Errore", "La cartella di Input non è valida."); return
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Errore", f"Impossibile creare la cartella di Output: {e}"); return

        self.start_button.config(state=tk.DISABLED)
        self.browse_input_button.config(state=tk.DISABLED)
        self.browse_output_button.config(state=tk.DISABLED)
        self.input_entry.config(state=tk.DISABLED)
        self.output_entry.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL, text="Pausa Analisi")
        self.stop_button.config(state=tk.NORMAL) # Abilita stop
        
        self.tree.delete(*self.tree.get_children())
        self.pause_event.clear()
        self.stop_event.clear() # Resetta l'evento di stop
        self.current_file_label.set("Avvio analisi...")

        self.analysis_thread = threading.Thread(
            target=self.run_full_analysis, 
            args=(input_dir, output_dir, self.analysis_queue, self.pause_event, self.stop_event), # Passa anche stop_event
            daemon=True
        )
        self.analysis_thread.start()
        self.process_analysis_queue()

    def run_full_analysis(self, input_dir, output_dir, queue, pause_event_thread, stop_event_thread):
        # ... (logica per ottenere files_to_analyze come prima) ...
        supported_ext = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")
        files_to_analyze = [os.path.join(r, f) for r, _, fs in os.walk(input_dir) for f in fs if f.lower().endswith(supported_ext)]
        
        if not files_to_analyze:
            queue.put({"type": "info_message", "title": "Info", "message": "Nessun file audio supportato trovato."})
            queue.put({"type": "final_status", "message": "Nessun file da analizzare."}); return

        results_data = []
        total_files = len(files_to_analyze)
        processed_count = 0

        for i, file_path in enumerate(files_to_analyze):
            if stop_event_thread.is_set():
                queue.put({"type": "status_update", "message": "Analisi interrotta dall'utente."})
                break # Esce dal ciclo for

            if pause_event_thread.is_set():
                queue.put({"type": "status_update", "message": f"Analisi in pausa... In attesa su {os.path.basename(file_path)}"})
                pause_event_thread.wait() 
                if stop_event_thread.is_set(): break # Controlla stop anche dopo la pausa
                queue.put({"type": "status_update", "message": f"Ripresa analisi... ({i+1}/{total_files}): {os.path.basename(file_path)}"})
            
            file_name = os.path.basename(file_path)
            queue.put({"type": "status_update", "message": f"Analizzando ({i+1}/{total_files}): {file_name}"})

            y, sr = None, None
            bpm, key, camelot, camelot_color, energy_rms, color_rms = 0, 'N/A', 'N/A', "grey70", 1, "Gray"
            compat_keys = []

            try:
                print(f"THREAD: Caricamento {file_path}")
                y, sr = librosa.load(file_path, sr=None)
            except Exception as e:
                # ... (gestione errore caricamento e invio alla coda come prima) ...
                print(f"THREAD: Errore caricamento {file_name}: {e}")
                row_err_vals = (file_name, "Errore Caricamento", "N/A", "N/A", "N/A", "", "N/A", "N/A")
                queue.put({"type": "new_row", "data": row_err_vals, "camelot_color_tag": "grey70_tag"})
                queue.put({"type": "spectrum_error", "title": file_name})
                results_data.append(dict(zip(self.tree["columns"], row_err_vals)))
                continue
            
            try: bpm = analyze_bpm_internal(y, sr)
            except Exception as e: print(f"THREAD: Errore BPM {file_name}: {e}")
            try: key, camelot = analyze_key_internal(y, sr)
            except Exception as e: print(f"THREAD: Errore Key {file_name}: {e}")
            
            camelot_color = CAMELOT_COLOR_MAP.get(camelot, "grey70")
            
            try: energy_rms, color_rms = analyze_energy_rms_internal(y)
            except Exception as e: print(f"THREAD: Errore Energy {file_name}: {e}")
            try: compat_keys = find_compatible_keys(camelot)
            except Exception as e: print(f"THREAD: Errore Compat {file_name}: {e}")

            print(f"THREAD: Risultati {file_name}: BPM:{bpm}, Key:{key}({camelot}), CColor:{camelot_color}, EnergyRMS:{energy_rms}-{color_rms}")
            
            row_vals = (file_name, bpm, key, camelot, camelot_color, ', '.join(compat_keys), energy_rms, color_rms)
            queue.put({"type": "new_row", "data": row_vals, "camelot_color_tag": camelot_color.lower().replace(" ", "_").replace("-","_") + "_tag"})
            if y is not None:
                 queue.put({"type": "spectrum_data", "y": y.copy(), "sr": sr, "title": file_name})
            results_data.append(dict(zip(self.tree["columns"], row_vals)))
            processed_count +=1
        
        # Fine analisi
        final_message_prefix = "Analisi interrotta." if stop_event_thread.is_set() else "Analisi completata!"
        if results_data:
            csv_path = os.path.join(output_dir, 'DJAnalyzer_analisi_v0.4.csv')
            try:
                pd.DataFrame(results_data).to_csv(csv_path, index=False, encoding='utf-8-sig')
                queue.put({"type": "analysis_complete", "message": f"{final_message_prefix} {processed_count}/{total_files} file.\nCSV: {csv_path}"})
            except Exception as e:
                queue.put({"type": "error_message", "title": "Errore CSV", "message": f"Errore salvataggio CSV: {e}"})
        else:
            queue.put({"type": "info_message", "title": "Info", "message": f"{final_message_prefix} Nessun dato processato."})
        queue.put({"type": "final_status", "message": f"{final_message_prefix} {processed_count}/{total_files} file processati."})


    def process_analysis_queue(self):
        try:
            while True: 
                message = self.analysis_queue.get_nowait()
                self.handle_queue_message(message) # Usa la funzione helper
                self.analysis_queue.task_done()
        except QueueEmpty:
            pass
        except Exception as e:
            print(f"Errore in process_analysis_queue: {e}")
        finally:
            # Schedula il prossimo controllo solo se il thread è (o era appena) vivo
            # o se ci sono ancora messaggi nella coda da processare
            is_thread_alive = self.analysis_thread and self.analysis_thread.is_alive()
            if is_thread_alive or not self.analysis_queue.empty():
                self.after(100, self.process_analysis_queue)
            elif not is_thread_alive and self.analysis_queue.empty(): # Thread finito e coda vuota
                self.reset_ui_after_analysis()


    def handle_queue_message(self, message):
        msg_type = message.get("type")
        if msg_type == "status_update":
            self.current_file_label.set(message.get("message", ""))
            self.last_analysis_status_message = message.get("message", "") # Salva l'ultimo messaggio di analisi
        elif msg_type == "new_row":
            row_data = message.get("data")
            camelot_tag_name = message.get("camelot_color_tag")
            
            if camelot_tag_name:
                actual_color = CAMELOT_COLOR_MAP.get(row_data[3], "grey70") # row_data[3] è il valore Camelot "XA/XB"
                if camelot_tag_name not in self.tree.tag_configure():
                     try:
                        self.tree.tag_configure(camelot_tag_name, background=actual_color)
                     except tk.TclError: # Può succedere se il nome colore non è valido per Tkinter
                        print(f"Attenzione: colore non valido per tag: {actual_color}, uso grigio.")
                        self.tree.tag_configure(camelot_tag_name, background="grey70")
                item_id = self.tree.insert("", "end", values=row_data, tags=(camelot_tag_name,))
            else:
                item_id = self.tree.insert("", "end", values=row_data)
            self.tree.see(item_id)

        elif msg_type == "spectrum_data":
            # Non aggiornare lo spettro se l'analisi è in pausa per evitare ritardi nella ripresa
            if not self.pause_event.is_set(): 
                self.display_spectrum(message.get("y"), message.get("sr"), message.get("title"))
        elif msg_type == "spectrum_error":
            self.show_spectrum_error(f"Errore spettro: {message.get('title', 'N/D')}")
        elif msg_type == "analysis_complete":
            messagebox.showinfo("Completato", message.get("message"))
        elif msg_type == "error_message":
            messagebox.showerror(message.get("title", "Errore"), message.get("message"))
        elif msg_type == "info_message":
            messagebox.showinfo(message.get("title", "Info"), message.get("message"))
        # "final_status" ora gestito da reset_ui_after_analysis quando il thread termina

    def reset_ui_after_analysis(self):
        self.current_file_label.set("Pronto per una nuova analisi o analisi terminata.")
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED) # Disabilita stop quando finito
        self.start_button.config(state=tk.NORMAL)
        self.browse_input_button.config(state=tk.NORMAL)
        self.browse_output_button.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.output_entry.config(state=tk.NORMAL)
        # Svuota la coda per sicurezza
        while not self.analysis_queue.empty():
            try: self.analysis_queue.get_nowait(); self.analysis_queue.task_done()
            except QueueEmpty: break
        print("Thread di analisi terminato e UI resettata.")

    def display_spectrum(self, y, sr, track_title="Spettro Audio"):
        # ... (come prima, ma assicurati che canvas_width_px e canvas_height_px siano > 1 prima di usarli)
        try:
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=512)), ref=np.max)
            
            # Ottieni dimensioni canvas DOPO che la finestra è stata disegnata e aggiornata
            self.update_idletasks() # Assicura che le dimensioni siano aggiornate
            canvas_width_px = self.spectrum_canvas.winfo_width()
            canvas_height_px = self.spectrum_canvas.winfo_height()

            if canvas_width_px <= 1 or canvas_height_px <= 1:
                print("Canvas dello spettro non ancora dimensionato correttamente, uso dimensioni di default per la figura.")
                fig_width_inches, fig_height_inches = 8, 1.8 
            else:
                fig_width_inches = canvas_width_px / 100 
                fig_height_inches = canvas_height_px / 100
            
            fig, ax = plt.subplots(figsize=(fig_width_inches, fig_height_inches), dpi=100)
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', cmap='magma', ax=ax)
            ax.set_title(track_title, fontsize=8) # Titolo più piccolo
            ax.tick_params(axis='both', which='major', labelsize=6) # Tick più piccoli
            fig.tight_layout(pad=0.05) # Padding minimo
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.02)
            plt.close(fig) 
            buf.seek(0)
            
            img_pil = Image.open(buf)
            if canvas_width_px > 1 and canvas_height_px > 1:
                # Ridimensiona l'immagine PIL alle dimensioni esatte del canvas
                img_pil_resized = img_pil.resize((canvas_width_px, canvas_height_px), Image.Resampling.LANCZOS)
                self.image_ref = ImageTk.PhotoImage(img_pil_resized)
            else: # Fallback se il canvas non ha ancora dimensioni
                self.image_ref = ImageTk.PhotoImage(img_pil) 
            
            self.spectrum_canvas.delete("all")
            self.spectrum_canvas.create_image(0, 0, anchor='nw', image=self.image_ref)
            
        except Exception as e:
            print(f"Errore in display_spectrum per {track_title}: {e}")
            self.show_spectrum_error(f"Errore spettro: {os.path.basename(track_title)}")


    def show_spectrum_error(self, message="Errore visualizzazione spettro"):
        # ... (come prima) ...
        try:
            self.spectrum_canvas.delete("all")
            self.update_idletasks()
            cw = self.spectrum_canvas.winfo_width()
            ch = self.spectrum_canvas.winfo_height()
            if cw > 1 and ch > 1:
                self.spectrum_canvas.create_text(cw/2, ch/2, text=message, fill="red", font=("Arial",10), anchor=tk.CENTER)
            else: # Se il canvas non ha dimensioni, stampa sulla console
                print(f"CANVAS_ERROR_DISPLAY: {message}")
        except Exception: pass

    def on_closing(self):
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askyesno("Esci", "L'analisi è in corso. Interrompere e uscire?"):
                self.stop_event.set()
                if self.pause_event.is_set(): self.pause_event.clear() # Sblocca se in pausa
                # Dai un po' di tempo al thread per terminare
                # Non usare join() qui per non bloccare la GUI nella chiusura
                self.destroy()
            else:
                return 
        else:
            self.destroy()

if __name__ == '__main__':
    app = DJAnalyzerApp()
    app.mainloop()