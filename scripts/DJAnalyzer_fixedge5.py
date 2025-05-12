# DJAnalyzer - Programma completo (Analisi BPM, Chiave, Energia)
# Versione v0.6 - THREADING GUI CORE, PAUSA/STOP, SPETTROGRAMMA LOGICA DISATTIVATA

import os
import threading
from queue import Queue, Empty as QueueEmpty 
import io # Ancora qui sebbene lo spettrogramma sia disattivato, per futura riattivazione
import librosa
# import librosa.display # Non serve ora
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk # Ancora qui per futura riattivazione spettrogramma
import matplotlib.pyplot as plt # Ancora qui per futura riattivazione spettrogramma

# --- Costanti e Mappe ---
PITCH_MAP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
PITCH_MAP_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'] # Per conversioni enarmoniche

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

ENERGY_RMS_COLOR_PALETTE = { # Palette per l'energia RMS (da rivedere)
    1: "Gray", 2: "LightBlue", 3: "Cyan", 4: "LightGreen", 5: "Lime",
    6: "Yellow", 7: "Orange", 8: "Red", 9: "Magenta", 10: "HotPink"
}

# --- Funzioni di Analisi (da migliorare significativamente) ---
def analyze_key_internal(y, sr):
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, n_chroma=12, bins_per_octave=36)
        chroma_profile = np.mean(chroma, axis=1)
        major_profile = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]) # Krumhansl-Schmuckler (approx)
        minor_profile = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.78,3.98,2.69,3.34,3.17]) # Krumhansl-Schmuckler (approx)
        best_corr_maj, key_idx_maj, best_corr_min, key_idx_min = -np.inf, 0, -np.inf, 0
        for i in range(12):
            corr_maj = np.corrcoef(chroma_profile, np.roll(major_profile, i))[0, 1]
            if corr_maj > best_corr_maj: best_corr_maj, key_idx_maj = corr_maj, i
            corr_min = np.corrcoef(chroma_profile, np.roll(minor_profile, i))[0, 1]
            if corr_min > best_corr_min: best_corr_min, key_idx_min = corr_min, i
        if best_corr_maj >= best_corr_min: key_label = PITCH_MAP[key_idx_maj]
        else: key_label = PITCH_MAP[key_idx_min] + 'm'
        camelot = CAMELOT_MAP.get(key_label, 'N/A')
        return key_label, camelot
    except Exception as e: print(f"Errore (analyze_key_internal): {e}"); return 'N/A', 'N/A'

def analyze_bpm_internal(y, sr):
    try:
        if hasattr(librosa.feature, 'rhythm') and hasattr(librosa.feature.rhythm, 'tempo'):
            tempo_array = librosa.feature.rhythm.tempo(y=y, sr=sr, aggregate=None)
        else: tempo_array = librosa.beat.tempo(y=y, sr=sr, aggregate=None)
        bpm = int(round(np.median(tempo_array))) if tempo_array.size > 0 else 0
        return bpm
    except Exception as e: print(f"Errore (analyze_bpm_internal): {e}"); return 0

def analyze_energy_rms_internal(y):
    try:
        rms = librosa.feature.rms(y=y)[0]
        energy_raw = float(np.mean(rms)) if rms.size > 0 and np.all(np.isfinite(rms)) else 0.0
        print(f"DEBUG Energia: RMS grezzo = {energy_raw:.6f}")
        if energy_raw == 0.0: scaled_energy = 1
        else: scaled_energy = min(10, max(1, int(np.ceil(energy_raw * 50)))) # Fattore 50 per test, da rivedere!
        print(f"DEBUG Energia: RMS Scalata = {scaled_energy}")
        color = ENERGY_RMS_COLOR_PALETTE.get(scaled_energy, "Gray")
        return scaled_energy, color
    except Exception as e: print(f"Errore (analyze_energy_rms_internal): {e}"); return 1, "Gray"

def find_compatible_keys(camelot_key):
    if not camelot_key or camelot_key == 'N/A': return []
    try:
        num_str, letter = camelot_key[:-1], camelot_key[-1]
        if not num_str.isdigit() or letter not in ('A', 'B'): return []
        num = int(num_str)
        compat_codes = [f"{num}{letter}", f"{(num % 12) + 1}{letter}", f"{ (num - 2 + 12) % 12 + 1}{letter}", f"{num}{'A' if letter == 'B' else 'B'}"]
        # Filtra per assicurarsi che i codici generati siano validi (1-12 A/B)
        valid_compat = []
        for c_code in compat_codes:
            c_num_str, c_letter = c_code[:-1], c_code[-1]
            if c_num_str.isdigit() and int(c_num_str) in range(1,13) and c_letter in ('A','B'):
                 valid_compat.append(c_code)
        return sorted(list(set(valid_compat)))
    except Exception as e: print(f"Errore (find_compatible_keys) per {camelot_key}: {e}"); return []

# --- Interfaccia Grafica ---
class DJAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJAnalyzer v0.6 (Threaded Core)")
        self.geometry("1100x650") # Altezza adattata per assenza spettrogramma
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.analysis_thread = None
        self.analysis_queue = Queue()
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.current_file_label = tk.StringVar(value="Pronto per l'analisi.")
        self.last_analysis_status_message = "Pronto."
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._analysis_completed_flag = True # Inizia come se un'analisi fosse già "completata"

    def setup_ui(self):
        # Frame Controlli (Input/Output/Azioni)
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        input_frame = ttk.LabelFrame(top_frame, text="Input/Output")
        input_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Label(input_frame, text="Cartella Input:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_folder, width=40)
        self.input_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        self.browse_input_button = ttk.Button(input_frame, text="Sfoglia", command=self.browse_input)
        self.browse_input_button.grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(input_frame, text="Cartella Output:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.output_entry = ttk.Entry(input_frame, textvariable=self.output_folder, width=40)
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
        
        ttk.Label(self, textvariable=self.current_file_label, font=("Arial", 10), foreground="blue").pack(pady=(2,5), fill=tk.X, padx=10, anchor=tk.W)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scrollbar_x.pack(side="bottom", fill="x")
        
        self.tree_columns = ("File", "BPM", "Key", "Camelot", "Colore Camelot", "Compatibili", "Energia RMS", "Colore RMS")
        self.tree = ttk.Treeview(tree_frame, columns=self.tree_columns, show="headings", 
                                 yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)
        cols_config = {"File": 250, "BPM": 50, "Key": 60, "Camelot": 60, "Colore Camelot": 100, "Compatibili": 150, "Energia RMS": 80, "Colore RMS": 100}
        for col, width in cols_config.items():
            anchor_val = tk.W if col in ["File", "Compatibili", "Colore Camelot"] else tk.CENTER
            self.tree.heading(col, text=col, anchor=anchor_val)
            self.tree.column(col, width=width, minwidth=max(40, width // 2), anchor=anchor_val)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_scrollbar_y.config(command=self.tree.yview)
        tree_scrollbar_x.config(command=self.tree.xview)

        # Pre-configura i tag colore per Camelot
        for camelot_key_code, color_name_val in CAMELOT_COLOR_MAP.items(): # Iteriamo sulla mappa Camelot -> Colore
            tag_name = color_name_val.lower().replace(" ", "_").replace("-", "_") + "_tag" # Nome tag basato sul NOME COLORE
            try:
                self.tree.tag_configure(tag_name, background=color_name_val)
            except tk.TclError:
                print(f"Attenzione: colore Tkinter non valido '{color_name_val}' per tag '{tag_name}'. Uso grigio.")
                self.tree.tag_configure(tag_name, background="grey70")


    def browse_input(self): folder = filedialog.askdirectory(title="Seleziona Cartella Input Audio");_ = [self.input_folder.set(folder)] if folder else None
    def browse_output(self): folder = filedialog.askdirectory(title="Seleziona Cartella Output per CSV");_ = [self.output_folder.set(folder)] if folder else None
    def toggle_pause_analysis(self): # ... (come prima)
        if self.pause_event.is_set():
            self.pause_event.clear(); self.pause_button.config(text="Pausa Analisi"); self.current_file_label.set(self.last_analysis_status_message)
        else:
            self.pause_event.set(); self.pause_button.config(text="Riprendi Analisi"); self.last_analysis_status_message = self.current_file_label.get(); self.current_file_label.set("Analisi in pausa...")
    def stop_analysis(self): # ... (come prima)
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askyesno("Ferma Analisi", "Vuoi davvero fermare l'analisi in corso?"):
                self.stop_event.set(); 
                if self.pause_event.is_set(): self.pause_event.clear()
                self.current_file_label.set("Interruzione analisi in corso...")
        else: self.reset_ui_after_analysis()

    def start_analysis_thread(self):
        input_dir, output_dir = self.input_folder.get(), self.output_folder.get()
        if not (input_dir and output_dir and os.path.isdir(input_dir)):
            messagebox.showerror("Errore", "Seleziona cartelle di Input e Output valide."); return
        try: os.makedirs(output_dir, exist_ok=True)
        except OSError as e: messagebox.showerror("Errore", f"Impossibile creare cartella Output: {e}"); return

        self.start_button.config(state=tk.DISABLED); self.browse_input_button.config(state=tk.DISABLED)
        self.browse_output_button.config(state=tk.DISABLED); self.input_entry.config(state=tk.DISABLED)
        self.output_entry.config(state=tk.DISABLED); self.pause_button.config(state=tk.NORMAL, text="Pausa Analisi")
        self.stop_button.config(state=tk.NORMAL)
        
        self.tree.delete(*self.tree.get_children()); self.pause_event.clear(); self.stop_event.clear()
        self.current_file_label.set("Avvio analisi..."); self._analysis_completed_flag = False

        self.analysis_thread = threading.Thread(target=self.run_full_analysis, args=(input_dir, output_dir, self.analysis_queue, self.pause_event, self.stop_event), daemon=True)
        self.analysis_thread.start()
        self.process_analysis_queue() # Avvia il listener della coda

    def run_full_analysis(self, input_dir, output_dir, queue, pause_event_thread, stop_event_thread):
        supported_ext = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")
        files_to_analyze = [os.path.join(r, f) for r, _, fs in os.walk(input_dir) for f in fs if f.lower().endswith(supported_ext)]
        if not files_to_analyze:
            queue.put({"type": "final_status", "message": "Nessun file audio trovato da analizzare."}); return

        results_data, total_files, processed_count = [], len(files_to_analyze), 0
        for i, file_path in enumerate(files_to_analyze):
            if stop_event_thread.is_set(): queue.put({"type": "status_update", "message": "Analisi interrotta."}); break
            if pause_event_thread.is_set():
                queue.put({"type": "status_update", "message": f"Pausa... {os.path.basename(file_path)}"}); pause_event_thread.wait()
                if stop_event_thread.is_set(): queue.put({"type": "status_update", "message": "Analisi interrotta."}); break
                queue.put({"type": "status_update", "message": f"Ripresa... ({i+1}/{total_files}): {os.path.basename(file_path)}"})
            
            file_name = os.path.basename(file_path)
            queue.put({"type": "status_update", "message": f"Analizzando ({i+1}/{total_files}): {file_name}"})
            y, sr, bpm, key, camelot, camelot_color_val, energy_rms, color_rms, compat_keys = None,None,0,'N/A','N/A',"grey70",1,"Gray",[]
            try:
                print(f"THREAD: Caricamento {file_path}"); y, sr = librosa.load(file_path, sr=None)
            except Exception as e:
                print(f"THREAD: Errore caricamento {file_name}: {e}")
                queue.put({"type": "new_row", "data": (file_name,"Err Caricamento",'N/A','N/A','N/A',"",'N/A','N/A'), "camelot_color_tag": "grey70_tag"})
                results_data.append(dict(zip(self.tree_columns, (file_name,"Err Caricamento",'N/A','N/A','N/A',"",'N/A','N/A'))))
                continue
            try: bpm = analyze_bpm_internal(y, sr)
            except Exception as e_bpm: print(f"THREAD: Errore BPM {file_name}: {e_bpm}")
            try: key, camelot = analyze_key_internal(y, sr)
            except Exception as e_key: print(f"THREAD: Errore Key {file_name}: {e_key}")
            camelot_color_val = CAMELOT_COLOR_MAP.get(camelot, "grey70")
            try: energy_rms, color_rms = analyze_energy_rms_internal(y)
            except Exception as e_energy: print(f"THREAD: Errore Energy {file_name}: {e_energy}")
            try: compat_keys = find_compatible_keys(camelot)
            except Exception as e_compat: print(f"THREAD: Errore Compat {file_name}: {e_compat}")

            print(f"THREAD: Ris {file_name}: BPM:{bpm}, Key:{key}({camelot}), CC:{camelot_color_val}, E_RMS:{energy_rms}-{color_rms}")
            row_values = (file_name, bpm, key, camelot, camelot_color_val, ', '.join(compat_keys), energy_rms, color_rms)
            tag_name = camelot_color_val.lower().replace(" ", "_").replace("-","_") + "_tag"
            queue.put({"type": "new_row", "data": row_values, "camelot_color_tag": tag_name})
            results_data.append(dict(zip(self.tree_columns, row_values)))
            processed_count += 1
        
        final_msg_prefix = "Interrotta" if stop_event_thread.is_set() else "Completata"
        if results_data:
            csv_path = os.path.join(output_dir, f'DJAnalyzer_analisi_{final_msg_prefix.lower()}.csv')
            try:
                pd.DataFrame(results_data).to_csv(csv_path, index=False, encoding='utf-8-sig')
                queue.put({"type": "analysis_complete", "message": f"Analisi {final_msg_prefix.lower()}! {processed_count}/{total_files} file.\nCSV: {csv_path}"})
            except Exception as e_csv: queue.put({"type": "error_message", "title": "Errore CSV", "message": f"Salvataggio CSV: {e_csv}"})
        else: queue.put({"type": "info_message", "title": "Info", "message": f"Analisi {final_msg_prefix.lower()}. Nessun dato."})
        queue.put({"type": "final_status", "message": f"Analisi {final_msg_prefix.lower()}. {processed_count}/{total_files} file."})

    def process_analysis_queue(self):
        try:
            for _ in range(10): # Processa max 10 messaggi per volta per mantenere reattività
                if self.analysis_queue.empty(): break
                message = self.analysis_queue.get_nowait()
                self.handle_queue_message(message)
                self.analysis_queue.task_done()
        except QueueEmpty: pass
        except Exception as e: print(f"Errore process_analysis_queue: {e}")
        finally:
            if (self.analysis_thread and self.analysis_thread.is_alive()) or not self.analysis_queue.empty():
                self.after(100, self.process_analysis_queue) # Continua a controllare
            elif not getattr(self, '_analysis_completed_flag', False) : # Thread finito e coda vuota
                 self.reset_ui_after_analysis()
                 self._analysis_completed_flag = True


    def handle_queue_message(self, message):
        msg_type = message.get("type")
        if msg_type == "status_update": self.current_file_label.set(message.get("message","")); self.last_analysis_status_message = message.get("message","")
        elif msg_type == "new_row":
            row_data, tag_name = message.get("data"), message.get("camelot_color_tag")
            tags_to_apply = (tag_name,) if tag_name else ()
            # La pre-configurazione dei tag è in setup_ui, qui assumiamo che esista
            # Se il tag non fosse pre-configurato, potremmo aggiungerlo qui come fallback
            # if tag_name and tag_name not in self.tree.tag_configure():
            #    actual_color = CAMELOT_COLOR_MAP.get(row_data[3], "grey70") # row_data[3] è Camelot Code
            #    self.tree.tag_configure(tag_name, background=actual_color)
            item_id = self.tree.insert("", "end", values=row_data, tags=tags_to_apply)
            self.tree.see(item_id)
        # elif msg_type == "spectrum_data": # SPETTROGRAMMA DISATTIVATO PER ORA
        #     if not self.pause_event.is_set(): self.display_spectrum(message.get("y"), message.get("sr"), message.get("title"))
        # elif msg_type == "spectrum_error": print(f"INFO: spectrum_error (visualizzazione disattivata): {message.get('title')}")
        elif msg_type == "analysis_complete": messagebox.showinfo("Completato", message.get("message"))
        elif msg_type == "error_message": messagebox.showerror(message.get("title", "Errore"), message.get("message"))
        elif msg_type == "info_message": messagebox.showinfo(message.get("title", "Info"), message.get("message"))
        # final_status è gestito dalla logica in finally di process_analysis_queue tramite reset_ui_after_analysis

    def reset_ui_after_analysis(self):
        final_msg = self.current_file_label.get() # Mantiene l'ultimo messaggio di stato (es. completato/interrotto)
        if "Analizzando" in final_msg or "Pausa" in final_msg: # Se il thread è stato interrotto bruscamente
            final_msg = "Pronto per una nuova analisi o analisi terminata."
        self.current_file_label.set(final_msg)
        self.pause_button.config(state=tk.DISABLED); self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL); self.browse_input_button.config(state=tk.NORMAL)
        self.browse_output_button.config(state=tk.NORMAL); self.input_entry.config(state=tk.NORMAL)
        self.output_entry.config(state=tk.NORMAL)
        while not self.analysis_queue.empty(): # Svuota la coda
            try: self.analysis_queue.get_nowait(); self.analysis_queue.task_done()
            except QueueEmpty: break
        print("THREADING: UI resettata dopo fine analisi.")

    def display_spectrum(self, y, sr, track_title="Spettro Audio"): pass # Disattivato
    def show_spectrum_error(self, message="Errore spettro"): pass # Disattivato

    def on_closing(self):
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askyesno("Esci", "Analisi in corso. Interrompere e uscire?"):
                self.stop_event.set(); 
                if self.pause_event.is_set(): self.pause_event.clear()
                # Non fare self.analysis_thread.join() qui per non bloccare la GUI
                self.destroy()
        else: self.destroy()

if __name__ == '__main__':
    app = DJAnalyzerApp()
    app.mainloop()