# DJAnalyzer - Programma completo (Analisi BPM, Chiave, Energia)
# Versione v0.6.5 - CORREZIONE DEFINITIVA (speriamo!) per configurazione tag in setup_ui

import os
import threading
from queue import Queue, Empty as QueueEmpty 
import io 
import librosa
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk 

# --- Costanti e Mappe --- (Identiche)
PITCH_MAP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
PITCH_MAP_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'] 
CAMELOT_MAP = {
    "Abm": "1A", "G#m": "1A", "Ebm": "2A", "D#m": "2A", "Bbm": "3A", "A#m": "3A",
    "Fm":  "4A", "Cm":  "5A", "Gm":  "6A", "Dm":  "7A", "Am":  "8A", "Em":  "9A",
    "Bm":  "10A", "F#m": "11A", "C#m": "12A", "Dbm": "12A",
    "B":   "1B", "Cb": "1B", "F#":  "2B", "Gb":  "2B", "Db":  "3B", "C#":  "3B",
    "Ab":  "4B", "G#":  "4B", "Eb":  "5B", "D#":  "5B", "Bb":  "6B", "A#":  "6B",
    "F":   "7B", "C":   "8B", "G":   "9B", "D":   "10B", "A":   "11B", "E":   "12B",
}
CAMELOT_COLOR_MAP = {
    "1A": "light sky blue",  "1B": "sky blue", "2A": "light blue", "2B": "steel blue",
    "3A": "dodger blue",     "3B": "green yellow", "4A": "medium sea green","4B": "chartreuse",
    "5A": "spring green",    "5B": "yellow green", "6A": "lawn green", "6B": "yellow",
    "7A": "gold",            "7B": "dark salmon",  "8A": "orange", "8B": "light coral",
    "9A": "dark orange",     "9B": "indian red",   "10A": "tomato", "10B": "medium violet red",
    "11A": "hot pink",       "11B": "purple",     "12A": "medium orchid",  "12B": "blue violet",
    "N/A": "grey70"
}
ENERGY_RMS_COLOR_PALETTE = { 
    1: "Gray70", 2: "LightBlue1", 3: "PaleTurquoise1", 4: "PaleGreen1", 5: "SpringGreen2",
    6: "yellow1", 7: "orange1", 8: "IndianRed1", 9: "HotPink1", 10: "DeepPink1"
}

# --- Funzioni di Analisi --- (Identiche alla v0.6.2 / v0.6.4)
def analyze_key_internal(y, sr):
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, n_chroma=12, bins_per_octave=36)
        chroma_profile = np.mean(chroma, axis=1)
        major_profile = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
        minor_profile = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.78,3.98,2.69,3.34,3.17])
        best_corr_maj, key_idx_maj, best_corr_min, key_idx_min = -np.inf, 0, -np.inf, 0
        for i in range(12):
            corr_maj = np.corrcoef(chroma_profile, np.roll(major_profile, i))[0, 1]
            if corr_maj > best_corr_maj: best_corr_maj, key_idx_maj = corr_maj, i
            corr_min = np.corrcoef(chroma_profile, np.roll(minor_profile, i))[0, 1]
            if corr_min > best_corr_min: best_corr_min, key_idx_min = corr_min, i
        if best_corr_maj >= best_corr_min: key_label = PITCH_MAP[key_idx_maj]
        else: key_label = PITCH_MAP[key_idx_min] + 'm'
        camelot = CAMELOT_MAP.get(key_label, 'N/A')
        if camelot == 'N/A': 
            if 'm' in key_label: note_root, suffix = key_label[:-1], 'm'
            else: note_root, suffix = key_label, ''
            if note_root in PITCH_MAP:
                idx = PITCH_MAP.index(note_root)
                if '#' in note_root: 
                    try: # Cerca l'equivalente bemolle
                        flat_equivalent_root = PITCH_MAP_FLAT[PITCH_MAP.index(note_root)] # Assumendo che PITCH_MAP_FLAT[idx] sia l'equivalente bemolle
                        key_label_flat = flat_equivalent_root + suffix
                        camelot_flat = CAMELOT_MAP.get(key_label_flat, 'N/A')
                        if camelot_flat != 'N/A': key_label, camelot = key_label_flat, camelot_flat
                    except ValueError: # Se la nota non è in PITCH_MAP (es. già bemolle)
                         pass 
        return key_label, camelot
    except Exception as e: print(f"Errore (analyze_key_internal): {e}"); return 'N/A', 'N/A'

def analyze_bpm_internal(y, sr):
    try:
        if hasattr(librosa.feature, 'rhythm') and hasattr(librosa.feature.rhythm, 'tempo'):
            tempo_array = librosa.feature.rhythm.tempo(y=y, sr=sr, aggregate=None)
        else: 
            tempo_array = librosa.beat.tempo(y=y, sr=sr, aggregate=None)
        bpm = int(round(np.median(tempo_array))) if tempo_array.size > 0 else 0
        return bpm
    except Exception as e: print(f"Errore (analyze_bpm_internal): {e}"); return 0

def analyze_energy_rms_internal(y):
    try:
        rms = librosa.feature.rms(y=y)[0] 
        energy_raw = float(np.mean(rms)) if rms.size > 0 and np.all(np.isfinite(rms)) else 0.0
        print(f"DEBUG Energia: RMS grezzo = {energy_raw:.6f}")
        if energy_raw == 0.0: scaled_energy = 1
        else: scaled_energy = min(10, max(1, int(np.ceil(energy_raw * 50)))) 
        print(f"DEBUG Energia: RMS Scalata = {scaled_energy}")
        color = ENERGY_RMS_COLOR_PALETTE.get(scaled_energy, "Gray70")
        return scaled_energy, color
    except Exception as e: print(f"Errore (analyze_energy_rms_internal): {e}"); return 1, "Gray70"

def find_compatible_keys(camelot_key):
    if not camelot_key or camelot_key == 'N/A': return []
    try:
        num_str, letter = camelot_key[:-1], camelot_key[-1]
        if not num_str.isdigit() or letter not in ('A', 'B'): return []
        num = int(num_str)
        compat_codes = [f"{num}{letter}", f"{(num % 12) + 1}{letter}", f"{ (num - 2 + 12) % 12 + 1}{letter}", f"{num}{'A' if letter == 'B' else 'B'}"]
        valid_compat = []
        for c_code in compat_codes:
            c_num_str, c_letter = c_code[:-1], c_code[-1]
            if c_num_str.isdigit():
                c_num = int(c_num_str)
                if 1 <= c_num <= 12 and c_letter in ('A','B'):
                    valid_compat.append(c_code)
        return sorted(list(set(valid_compat)))
    except Exception as e: print(f"Errore (find_compatible_keys) per {camelot_key}: {e}"); return []

# --- Interfaccia Grafica ---
class DJAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJAnalyzer v0.6.5 (Threaded - Tag Fix Definitivo Reale!)") 
        self.geometry("1100x600") 
        self.input_folder, self.output_folder = tk.StringVar(), tk.StringVar()
        self.analysis_thread, self.analysis_queue = None, Queue()
        self.pause_event, self.stop_event = threading.Event(), threading.Event()
        self.current_file_label = tk.StringVar(value="Pronto.")
        self.last_analysis_status_message = "Pronto."
        self.setup_ui() # Chiamata a setup_ui
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._analysis_ongoing = False 

    def setup_ui(self):
        # ... (Layout GUI come in v0.6.2, fino alla pre-configurazione dei tag) ...
        top_frame = ttk.Frame(self); top_frame.pack(fill=tk.X, padx=10, pady=5)
        input_frame = ttk.LabelFrame(top_frame, text="Cartelle"); input_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Label(input_frame, text="Input:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_folder, width=35)
        self.input_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        self.browse_input_button = ttk.Button(input_frame, text="Sfoglia", command=self.browse_input)
        self.browse_input_button.grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(input_frame, text="Output:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.output_entry = ttk.Entry(input_frame, textvariable=self.output_folder, width=35)
        self.output_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        self.browse_output_button = ttk.Button(input_frame, text="Sfoglia", command=self.browse_output)
        self.browse_output_button.grid(row=1, column=2, padx=5, pady=2)
        input_frame.columnconfigure(1, weight=1)

        action_buttons_frame = ttk.LabelFrame(top_frame, text="Azioni")
        action_buttons_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        self.start_button = ttk.Button(action_buttons_frame, text="Avvia Analisi", command=self.start_analysis_thread)
        self.start_button.pack(pady=2, padx=5, fill=tk.X)
        self.pause_button = ttk.Button(action_buttons_frame, text="Pausa Analisi", command=self.toggle_pause_analysis, state=tk.DISABLED)
        self.pause_button.pack(pady=2, padx=5, fill=tk.X)
        self.stop_button = ttk.Button(action_buttons_frame, text="Ferma Analisi", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_button.pack(pady=2, padx=5, fill=tk.X)
        
        ttk.Label(self, textvariable=self.current_file_label, font=("Segoe UI", 9)).pack(pady=(0,5), fill=tk.X, padx=10, anchor=tk.W)

        tree_frame = ttk.Frame(self); tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_sb_y = ttk.Scrollbar(tree_frame, orient="vertical"); tree_sb_y.pack(side="right", fill="y")
        tree_sb_x = ttk.Scrollbar(tree_frame, orient="horizontal"); tree_sb_x.pack(side="bottom", fill="x")
        
        self.tree_columns = ("File", "BPM", "Key", "Camelot", "Colore Camelot", "Compatibili", "Energia RMS", "Colore RMS")
        self.tree = ttk.Treeview(tree_frame, columns=self.tree_columns, show="headings", 
                                 yscrollcommand=tree_sb_y.set, xscrollcommand=tree_sb_x.set)
        cols_conf = {"File":230,"BPM":40,"Key":50,"Camelot":50,"Colore Camelot":90,"Compatibili":120,"Energia RMS":80,"Colore RMS":90}
        for col, wd in cols_conf.items():
            anc = tk.W if col in ["File", "Compatibili", "Colore Camelot"] else tk.CENTER
            self.tree.heading(col, text=col, anchor=anc); self.tree.column(col, width=wd, minwidth=max(30,wd//2), anchor=anc)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_sb_y.config(command=self.tree.yview); tree_sb_x.config(command=self.tree.xview)

        # Pre-configura i tag colore per Camelot
        for camelot_key_code_map_key, color_name_val in CAMELOT_COLOR_MAP.items():
            tag_name = color_name_val.lower().replace(" ", "_").replace("-", "_") + "_tag" 
            try: self.tree.tag_configure(tag_name, background=color_name_val)
            except tk.TclError: 
                print(f"Attenzione: colore Tkinter non valido '{color_name_val}' per tag '{tag_name}'. Uso grigio.")
                self.tree.tag_configure(tag_name, background="grey70")
        
        default_color_name = CAMELOT_COLOR_MAP.get("N/A", "grey70")
        default_tag_name = default_color_name.lower().replace(" ", "_").replace("-","_") + "_tag"
        
        # CORREZIONE DEFINITIVA E GIUSTA: self.tree.tag_configure() (SENZA argomenti) restituisce la tupla dei tag.
        # L'avevo corretto a tag_names() per errore nel messaggio precedente, scusa!
        existing_tags = self.tree.tag_configure() # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CORREZIONE APPLICATA QUI
        if default_tag_name not in existing_tags: 
             try:
                self.tree.tag_configure(default_tag_name, background=default_color_name)
             except tk.TclError:
                self.tree.tag_configure(default_tag_name, background="grey70") 
        elif default_tag_name in existing_tags: 
            try:
                self.tree.tag_configure(default_tag_name, background=default_color_name)
            except tk.TclError:
                self.tree.tag_configure(default_tag_name, background="grey70")
        
        self.spectrum_display_frame = ttk.LabelFrame(self, text="Spettro Audio (Disattivato)")
        self.spectrum_display_frame.pack(fill=tk.X, expand=False, padx=10, pady=(0,5), ipady=5)
        ttk.Label(self.spectrum_display_frame, text="Visualizzazione spettrogramma temporaneamente disattivata.").pack(padx=5, pady=10)

    # ... (resto dei metodi browse_input, browse_output, ecc. IDENTICI alla v0.6.2) ...
    # Assicurati che l'indentazione sia corretta per tutti i metodi della classe.

    def browse_input(self): folder = filedialog.askdirectory(title="Seleziona Cartella Input");_=[self.input_folder.set(folder)] if folder else None
    def browse_output(self): folder = filedialog.askdirectory(title="Seleziona Cartella Output");_=[self.output_folder.set(folder)] if folder else None
    
    def toggle_pause_analysis(self):
        if not self._analysis_ongoing: return 
        if self.pause_event.is_set(): 
            self.pause_event.clear(); self.pause_button.config(text="Pausa Analisi"); self.current_file_label.set(self.last_analysis_status_message)
            print("THREADING: Analisi Ripresa.")
        else: 
            self.pause_event.set(); self.pause_button.config(text="Riprendi Analisi"); self.last_analysis_status_message = self.current_file_label.get(); self.current_file_label.set("Analisi in pausa...")
            print("THREADING: Analisi in Pausa.")
            
    def stop_analysis(self):
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askyesno("Ferma Analisi", "Interrompere l'analisi in corso?"):
                print("THREADING: Richiesta di stop analisi.")
                self.stop_event.set(); 
                if self.pause_event.is_set(): self.pause_event.clear() 
                self.current_file_label.set("Interruzione analisi richiesta...")
        elif self._analysis_ongoing: 
             self.reset_ui_after_analysis()
        else: 
            self.reset_ui_after_analysis()

    def start_analysis_thread(self):
        input_dir, output_dir = self.input_folder.get(), self.output_folder.get()
        if not (input_dir and output_dir and os.path.isdir(input_dir)): messagebox.showerror("Errore", "Seleziona cartelle Input/Output valide."); return
        try: os.makedirs(output_dir, exist_ok=True)
        except OSError as e: messagebox.showerror("Errore", f"Creazione cartella Output: {e}"); return

        self.start_button.config(state=tk.DISABLED); self.browse_input_button.config(state=tk.DISABLED)
        self.browse_output_button.config(state=tk.DISABLED); self.input_entry.config(state=tk.DISABLED)
        self.output_entry.config(state=tk.DISABLED); self.pause_button.config(state=tk.NORMAL, text="Pausa Analisi")
        self.stop_button.config(state=tk.NORMAL)
        
        self.tree.delete(*self.tree.get_children()); self.pause_event.clear(); self.stop_event.clear()
        self.current_file_label.set("Avvio preparazione analisi..."); self._analysis_ongoing = True

        self.analysis_thread = threading.Thread(target=self.run_full_analysis, args=(input_dir, output_dir, self.analysis_queue, self.pause_event, self.stop_event), daemon=True)
        self.analysis_thread.start()
        self.after(50, self.process_analysis_queue)

    def run_full_analysis(self, input_dir, output_dir, queue, pause_event_thread, stop_event_thread):
        supported_ext = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")
        files_to_analyze = []
        for r, _, fs in os.walk(input_dir):
            for f in fs:
                if f.lower().endswith(supported_ext):
                    files_to_analyze.append(os.path.join(r,f))
        
        if not files_to_analyze:
            queue.put({"type": "final_status", "message": "Nessun file audio trovato."}); return

        results_data, total_files, processed_count = [], len(files_to_analyze), 0
        queue.put({"type": "status_update", "message": f"Trovati {total_files} file. Inizio analisi..."})

        for i, file_path in enumerate(files_to_analyze):
            if stop_event_thread.is_set(): queue.put({"type": "final_status", "message": "Analisi interrotta!"}); break 
            
            if pause_event_thread.is_set():
                current_status_paused = f"Pausa... In attesa su {os.path.basename(file_path)}"
                queue.put({"type": "status_update", "message": current_status_paused})
                while pause_event_thread.is_set(): 
                    if stop_event_thread.is_set(): break
                    threading.Event().wait(0.1) 
                if stop_event_thread.is_set(): queue.put({"type": "final_status", "message": "Analisi interrotta durante pausa!"}); break
                queue.put({"type": "status_update", "message": f"Ripresa...({i+1}/{total_files}): {os.path.basename(file_path)}"})
            
            file_name = os.path.basename(file_path)
            queue.put({"type": "status_update", "message": f"Analizzando ({i+1}/{total_files}): {file_name}"})
            
            y, sr, bpm, key, camelot, camelot_clr_name, energy_rms, clr_rms, compat_k = None,None,0,'N/A','N/A',"grey70",1,"Gray70",[]
            
            try:
                print(f"THREAD: Caricamento {file_path}"); y, sr = librosa.load(file_path, sr=None)
            except Exception as e_load:
                print(f"THREAD: Errore caricamento {file_name}: {e_load}")
                row_err = (file_name,"Err Load",'N/A','N/A',"grey70","",'N/A',"grey70")
                default_color_name_err = CAMELOT_COLOR_MAP.get('N/A',"grey70")
                tag_for_error = default_color_name_err.lower().replace(" ", "_").replace("-","_") + "_tag"
                queue.put({"type":"new_row", "data":row_err, "camelot_color_tag": tag_for_error})
                results_data.append(dict(zip(self.tree_columns, row_err))); continue
            
            try: bpm = analyze_bpm_internal(y, sr)
            except Exception as e: print(f"THREAD: Errore BPM {file_name}: {e}")
            try: key, camelot = analyze_key_internal(y, sr)
            except Exception as e: print(f"THREAD: Errore Key {file_name}: {e}")
            
            camelot_clr_name = CAMELOT_COLOR_MAP.get(camelot, "grey70")
            
            try: energy_rms, clr_rms = analyze_energy_rms_internal(y)
            except Exception as e: print(f"THREAD: Errore Energy {file_name}: {e}")
            try: compat_k = find_compatible_keys(camelot)
            except Exception as e: print(f"THREAD: Errore Compat {file_name}: {e}")

            row_vals = (file_name, bpm, key, camelot, camelot_clr_name, ', '.join(compat_k), energy_rms, clr_rms)
            tag_name = camelot_clr_name.lower().replace(" ", "_").replace("-","_") + "_tag"
            queue.put({"type": "new_row", "data": row_vals, "camelot_color_tag": tag_name})
            results_data.append(dict(zip(self.tree_columns, row_vals)))
            processed_count += 1
        
        final_prefix = "Interrotta" if stop_event_thread.is_set() else "Completata"
        csv_filename = f'DJAnalyzer_analisi_{final_prefix.lower()}_({processed_count}_files)_v0.6.5.csv' # Versione nel nome file
        if results_data:
            csv_path = os.path.join(output_dir, csv_filename)
            try:
                pd.DataFrame(results_data).to_csv(csv_path, index=False, encoding='utf-8-sig')
                queue.put({"type": "analysis_complete", "message": f"Analisi {final_prefix.lower()}! {processed_count}/{total_files} file.\nCSV: {csv_path}"})
            except Exception as e_csv: queue.put({"type": "error_message", "title": "Errore CSV", "message": f"Salvataggio CSV: {e_csv}"})
        else: queue.put({"type": "info_message", "title": "Info", "message": f"Analisi {final_prefix.lower()}. Nessun dato."})
        queue.put({"type": "final_status", "message": f"Analisi {final_prefix.lower()}. {processed_count} di {total_files} file processati."})

    def process_analysis_queue(self):
        try:
            for _ in range(10): 
                if self.analysis_queue.empty(): break
                message = self.analysis_queue.get_nowait()
                self.handle_queue_message(message)
                self.analysis_queue.task_done()
        except QueueEmpty: pass
        except Exception as e: print(f"Errore process_analysis_queue: {e}")
        finally:
            if self._analysis_ongoing:
                if (self.analysis_thread and self.analysis_thread.is_alive()) or \
                   not self.analysis_queue.empty():
                    self.after(100, self.process_analysis_queue)
                elif not (self.analysis_thread and self.analysis_thread.is_alive()) and self.analysis_queue.empty():
                    self.reset_ui_after_analysis()

    def handle_queue_message(self, message):
        msg_type = message.get("type")
        if msg_type == "status_update": self.current_file_label.set(message.get("message","")); self.last_analysis_status_message = message.get("message","")
        elif msg_type == "new_row":
            row_data = message.get("data"); tag_name_from_queue = message.get("camelot_color_tag", "")
            tags_to_apply = (tag_name_from_queue,) if tag_name_from_queue else ()
            item_id = self.tree.insert("", "end", values=row_data, tags=tags_to_apply)
            self.tree.see(item_id)
        elif msg_type == "analysis_complete": messagebox.showinfo("Completato", message.get("message"))
        elif msg_type == "error_message": messagebox.showerror(message.get("title","Errore"), message.get("message"))
        elif msg_type == "info_message": messagebox.showinfo(message.get("title","Info"), message.get("message"))
        elif msg_type == "final_status": 
            self.current_file_label.set(message.get("message","Completato."))
            if not (self.analysis_thread and self.analysis_thread.is_alive()):
                 self.reset_ui_after_analysis()

    def reset_ui_after_analysis(self):
        print("THREADING: Chiamata a reset_ui_after_analysis.")
        if not self._analysis_ongoing: 
            print("THREADING: Reset UI - Analisi già considerata non in corso.")
            return 
        
        current_msg = self.current_file_label.get()
        if "Analizzando" in current_msg or "Pausa" in current_msg or "Interruzione" in current_msg or "Avvio" in current_msg or "Trovati" in current_msg or "Pronto." in current_msg:
             self.current_file_label.set("Pronto per una nuova analisi o analisi terminata.")

        self.pause_button.config(state=tk.DISABLED); self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL); self.browse_input_button.config(state=tk.NORMAL)
        self.browse_output_button.config(state=tk.NORMAL); self.input_entry.config(state=tk.NORMAL)
        self.output_entry.config(state=tk.NORMAL)
        self._analysis_ongoing = False 
        
        self.after(150, self._ensure_queue_empty_after_reset) 
        print("THREADING: UI resettata (pulsanti e flag).")

    def _ensure_queue_empty_after_reset(self):
        count = 0
        try:
            while not self.analysis_queue.empty():
                last_msg = self.analysis_queue.get_nowait()
                print(f"THREADING: Messaggio rimanente in coda durante reset: {last_msg.get('type')}")
                self.analysis_queue.task_done()
                count +=1
        except QueueEmpty: pass
        if count > 0: print(f"THREADING: Svuotati {count} messaggi rimanenti dalla coda durante il reset.")
        else: print("THREADING: Coda già vuota durante il reset finale.")
        
        final_label_text = "Pronto."
        # Conserva il messaggio se è di completamento o errore specifico
        if "Completata!" in self.current_file_label.get() or \
           "Interrotta!" in self.current_file_label.get() or \
           "Nessun file" in self.current_file_label.get():
            final_label_text = self.current_file_label.get()
        self.current_file_label.set(final_label_text)


    def display_spectrum(self, y, sr, track_title="Spettro Audio"): pass 
    def show_spectrum_error(self, message="Errore spettro"): pass

    def on_closing(self):
        print("THREADING: on_closing chiamato.")
        if self._analysis_ongoing and self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askyesno("Esci", "Analisi in corso. Interrompere e uscire?"):
                print("THREADING: Utente ha scelto di uscire durante analisi.")
                self.stop_event.set(); 
                if self.pause_event.is_set(): self.pause_event.clear()
                # Lasciamo che il thread termini da solo dato che è daemon
                # Potremmo voler attendere un breve timeout, ma self.destroy() dovrebbe bastare
                self.destroy()
            # else: non fare nulla se l'utente dice no e l'analisi continua
        else:
            print("THREADING: Uscita normale o analisi non in corso.")
            self.destroy()

if __name__ == '__main__':
    app = DJAnalyzerApp()
    app.mainloop()