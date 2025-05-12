# DJAnalyzer - Programma completo (Analisi BPM, Chiave, Energia, Spettro)
# Versione con THREADING per GUI reattiva

import os
import threading
from queue import Queue, Empty as QueueEmpty # Per comunicare tra thread e GUI
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
CAMELOT_MAP = {
    "Abm": "1A", "Ebm": "2A", "Bbm": "3A", "Fm": "4A", "Cm": "5A", "Gm": "6A", "Dm": "7A", "Am": "8A",
    "Em": "9A", "Bm": "10A", "F#m": "11A", "C#m": "12A", "G#m": "1A", # G#m è enarmonico di Abm
    "B": "1B", "F#": "2B", "C#": "3B", "G#": "4B", "D#": "5B", "A#": "6B",
    "E": "7B", "A": "8B", "D": "9B", "G": "10B", "C": "11B", "F": "12B",
    "Ab": "4B", "Eb": "5B", "Bb": "6B" # Aggiunte le maggiori con bemolle se l'algoritmo le produce
}

PITCH_MAP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Mappatura alternativa per bemolle se necessario
PITCH_MAP_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']


def analyze_key_internal(y, sr):
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, n_chroma=12, bins_per_octave=36)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Tenta un approccio basato su template (molto semplificato)
        # Definisci template grezzi per maggiore e minore
        major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]) # Profilo Krumhansl-Schmuckler (approssimato)
        minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1]) # Profilo Krumhansl-Schmuckler (approssimato)
        
        best_corr_maj = -1
        best_corr_min = -1
        key_idx_maj = 0
        key_idx_min = 0

        for i in range(12):
            # Correlazione con il profilo maggiore shiftato
            corr_maj = np.corrcoef(chroma_mean, np.roll(major_profile, i))[0, 1]
            if corr_maj > best_corr_maj:
                best_corr_maj = corr_maj
                key_idx_maj = i
            
            # Correlazione con il profilo minore shiftato
            corr_min = np.corrcoef(chroma_mean, np.roll(minor_profile, i))[0, 1]
            if corr_min > best_corr_min:
                best_corr_min = corr_min
                key_idx_min = i
        
        if best_corr_maj > best_corr_min:
            key_label = PITCH_MAP[key_idx_maj]
        else:
            key_label = PITCH_MAP[key_idx_min] + 'm'
            
        camelot = CAMELOT_MAP.get(key_label, 'N/A')
        # Se non trovato, prova con notazione bemolle per la radice (euristica)
        if camelot == 'N/A' and '#' in key_label:
            try:
                note_root_idx = PITCH_MAP.index(key_label.replace('m',''))
                flat_equivalent_root = PITCH_MAP_FLAT[(note_root_idx + 1) % 12 if '#' in PITCH_MAP[(note_root_idx + 1) % 12] else note_root_idx] # Semplificazione
                # Questa logica di conversione diesis->bemolle è molto grezza e andrebbe migliorata
                if 'm' in key_label:
                    camelot_try = CAMELOT_MAP.get(flat_equivalent_root + 'm', 'N/A')
                else:
                    camelot_try = CAMELOT_MAP.get(flat_equivalent_root, 'N/A')
                if camelot_try != 'N/A':
                    key_label = flat_equivalent_root + ('m' if 'm' in key_label else '')
                    camelot = camelot_try
            except ValueError:
                pass


        return key_label, camelot
    except Exception as e:
        print(f"Errore (analyze_key_internal): {e}")
        return 'N/A', 'N/A'

def analyze_bpm_internal(y, sr):
    try:
        tempo_array = librosa.beat.tempo(y=y, sr=sr)
        bpm = int(round(tempo_array[0])) if tempo_array.size > 0 else 0
        return bpm
    except Exception as e:
        print(f"Errore (analyze_bpm_internal): {e}")
        return 0

def analyze_energy_internal(y):
    try:
        rms = librosa.feature.rms(y=y)
        energy = float(np.mean(rms)) if rms.size > 0 and np.all(np.isfinite(rms)) else 0.0
        if energy == 0.0:
            scaled_energy = 1
        else:
            scaled_energy = min(10, max(1, int(np.ceil(energy * 20))))
        color = energy_to_color(scaled_energy)
        return scaled_energy, color
    except Exception as e:
        print(f"Errore (analyze_energy_internal): {e}")
        return 1, "Gray"

def energy_to_color(value):
    palette = {
        1: "Gray", 2: "LightBlue", 3: "Cyan", 4: "LightGreen", 5: "Lime",
        6: "Yellow", 7: "Orange", 8: "Red", 9: "Magenta", 10: "HotPink" # Colori più vivaci
    }
    return palette.get(value, "Gray")

def find_compatible_keys(camelot_key):
    if not camelot_key or camelot_key == 'N/A':
        return []
    try:
        num_str = camelot_key[:-1]
        letter = camelot_key[-1]
        if not num_str.isdigit() or letter not in ('A', 'B'): return []
        num = int(num_str)
        
        compatible = [
            f"{num}{letter}",
            f"{ (num % 12) + 1 }{letter}",
            f"{ (num - 2 + 12) % 12 + 1 }{letter}",
            f"{num}{'A' if letter == 'B' else 'B'}"
        ]
        return sorted(list(set(compatible)))
    except Exception as e:
        print(f"Errore (find_compatible_keys) per {camelot_key}: {e}")
        return []

class DJAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJAnalyzer v0.3 (Threaded)")
        self.geometry("1000x800")
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        
        self.analysis_thread = None
        self.analysis_queue = Queue()
        self.pause_event = threading.Event() # Evento per la pausa

        self.current_file_label = tk.StringVar(value="Pronto per l'analisi.")
        self.setup_ui()
        self.image_ref = None

    def setup_ui(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
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
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        self.start_button = ttk.Button(action_frame, text="Avvia Analisi", command=self.start_analysis_thread)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = ttk.Button(action_frame, text="Pausa Analisi", command=self.toggle_pause_analysis, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(self, textvariable=self.current_file_label, font=("Arial", 10), foreground="blue").pack(pady=(0, 5), fill=tk.X, padx=10)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scrollbar_x.pack(side="bottom", fill="x")
        self.tree = ttk.Treeview(tree_frame, columns=("File", "BPM", "Key", "Camelot", "Compatibili", "Energia", "Colore Energia"), show="headings", yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)
        cols_config = { "File": 250, "BPM": 60, "Key": 70, "Camelot": 70, "Compatibili": 150, "Energia": 70, "Colore Energia": 100}
        for col, width in cols_config.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=width // 2, anchor=tk.CENTER if col not in ["File", "Compatibili"] else tk.W)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_scrollbar_y.config(command=self.tree.yview)
        tree_scrollbar_x.config(command=self.tree.xview)

        self.spectrum_display_frame = ttk.LabelFrame(self, text="Spettro Audio")
        self.spectrum_display_frame.pack(fill=tk.X, expand=False, padx=10, pady=5, ipady=5) # fill=tk.X, expand=False
        self.spectrum_canvas = tk.Canvas(self.spectrum_display_frame, bg="black", height=200) # Altezza fissa
        self.spectrum_canvas.pack(fill=tk.X, expand=True, padx=5, pady=5) # fill=tk.X, expand=True

    def browse_input(self):
        folder = filedialog.askdirectory(title="Seleziona Cartella Input Audio")
        if folder: self.input_folder.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Seleziona Cartella Output per CSV")
        if folder: self.output_folder.set(folder)

    def toggle_pause_analysis(self):
        if self.pause_event.is_set(): # Se è in pausa (evento settato)
            self.pause_event.clear() # Riprendi (cancella evento)
            self.pause_button.config(text="Pausa Analisi")
            self.current_file_label.set(self.last_analysis_status_message if hasattr(self, 'last_analysis_status_message') else "Ripresa analisi...")

        else: # Se non è in pausa
            self.pause_event.set() # Metti in pausa (setta evento)
            self.pause_button.config(text="Riprendi Analisi")
            self.last_analysis_status_message = self.current_file_label.get() # Salva ultimo messaggio
            self.current_file_label.set("Analisi in pausa...")


    def start_analysis_thread(self):
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
        
        self.tree.delete(*self.tree.get_children())
        self.pause_event.clear() # Assicura che non sia in pausa all'inizio
        self.current_file_label.set("Avvio analisi...")

        self.analysis_thread = threading.Thread(target=self.run_full_analysis, args=(input_dir, output_dir, self.analysis_queue, self.pause_event), daemon=True)
        self.analysis_thread.start()
        self.process_analysis_queue()

    def run_full_analysis(self, input_dir, output_dir, queue, pause_event_thread):
        supported_ext = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")
        files_to_analyze = [os.path.join(r, f) for r, _, fs in os.walk(input_dir) for f in fs if f.lower().endswith(supported_ext)]
        
        if not files_to_analyze:
            queue.put({"type": "info_message", "title": "Info", "message": "Nessun file audio supportato trovato."})
            queue.put({"type": "final_status", "message": "Nessun file da analizzare."})
            return

        results_data = []
        total_files = len(files_to_analyze)

        for i, file_path in enumerate(files_to_analyze):
            if pause_event_thread.is_set():
                queue.put({"type": "status_update", "message": f"Analisi in pausa... In attesa su {os.path.basename(file_path)}"})
                pause_event_thread.wait() # Il thread si blocca qui finché l'evento non viene cancellato
                # Quando riprende, aggiorna lo status
                queue.put({"type": "status_update", "message": f"Ripresa analisi... Analizzando ({i+1}/{total_files}): {os.path.basename(file_path)}"})


            file_name = os.path.basename(file_path)
            queue.put({"type": "status_update", "message": f"Analizzando ({i+1}/{total_files}): {file_name}"})

            y, sr = None, None
            bpm, key, camelot, energy, color = 0, 'N/A', 'N/A', 1, "Gray"
            compat_keys = []

            try:
                print(f"THREAD: Caricamento {file_path}")
                y, sr = librosa.load(file_path, sr=None)
            except Exception as e:
                print(f"THREAD: Errore caricamento {file_name}: {e}")
                row_err_vals = (file_name, "Errore Caricamento", "N/A", "N/A", "", "N/A", "N/A")
                queue.put({"type": "new_row", "data": row_err_vals})
                queue.put({"type": "spectrum_error", "title": file_name})
                results_data.append(dict(zip(self.tree["columns"], row_err_vals)))
                continue
            
            try: bpm = analyze_bpm_internal(y, sr)
            except Exception as e: print(f"THREAD: Errore BPM {file_name}: {e}")
            try: key, camelot = analyze_key_internal(y, sr)
            except Exception as e: print(f"THREAD: Errore Key {file_name}: {e}")
            try: energy, color = analyze_energy_internal(y)
            except Exception as e: print(f"THREAD: Errore Energy {file_name}: {e}")
            try: compat_keys = find_compatible_keys(camelot)
            except Exception as e: print(f"THREAD: Errore Compat {file_name}: {e}")

            print(f"THREAD: Risultati {file_name}: BPM:{bpm}, Key:{key}({camelot}), Energy:{energy}-{color}")
            
            row_vals = (file_name, bpm, key, camelot, ', '.join(compat_keys), energy, color)
            queue.put({"type": "new_row", "data": row_vals})
            if y is not None: # Solo se l'audio è stato caricato
                 queue.put({"type": "spectrum_data", "y": y.copy(), "sr": sr, "title": file_name}) # Passa una copia
            results_data.append(dict(zip(self.tree["columns"], row_vals)))
        
        # Fine analisi
        if results_data:
            csv_path = os.path.join(output_dir, 'DJAnalyzer_analisi_v0.3.csv')
            try:
                pd.DataFrame(results_data).to_csv(csv_path, index=False, encoding='utf-8-sig')
                queue.put({"type": "analysis_complete", "message": f"Analisi completata! {total_files} file.\nCSV: {csv_path}"})
            except Exception as e:
                queue.put({"type": "error_message", "title": "Errore CSV", "message": f"Errore salvataggio CSV: {e}"})
        else:
            queue.put({"type": "info_message", "title": "Info", "message": "Nessun dato processato da salvare."})
        queue.put({"type": "final_status", "message": f"Completato. {total_files} file processati."})


    def process_analysis_queue(self):
        try:
            while True: # Continua a prendere messaggi finché la coda non è vuota
                message = self.analysis_queue.get_nowait() # Non bloccante
                msg_type = message.get("type")

                if msg_type == "status_update":
                    self.current_file_label.set(message.get("message", ""))
                elif msg_type == "new_row":
                    item_id = self.tree.insert("", "end", values=message.get("data"))
                    self.tree.see(item_id)
                elif msg_type == "spectrum_data":
                    if not self.pause_event.is_set(): # Non aggiornare spettro se in pausa per evitare accodamenti
                        self.display_spectrum(message.get("y"), message.get("sr"), message.get("title"))
                elif msg_type == "spectrum_error":
                    self.show_spectrum_error(f"Errore spettro: {message.get('title', 'N/D')}")
                elif msg_type == "analysis_complete":
                    messagebox.showinfo("Completato", message.get("message"))
                elif msg_type == "error_message":
                    messagebox.showerror(message.get("title", "Errore"), message.get("message"))
                elif msg_type == "info_message":
                    messagebox.showinfo(message.get("title", "Info"), message.get("message"))
                elif msg_type == "final_status":
                    self.current_file_label.set(message.get("message", "Completato."))
                    self.reset_ui_after_analysis() # Chiama una funzione per resettare la UI
                
                self.analysis_queue.task_done()
        except QueueEmpty: # La coda è vuota, non fare nulla
            pass
        except Exception as e:
            print(f"Errore in process_analysis_queue: {e}")
        finally:
            if self.analysis_thread and self.analysis_thread.is_alive():
                self.after(100, self.process_analysis_queue) # Richiama se il thread è ancora vivo
            else: # Il thread è terminato
                # Processa eventuali messaggi rimanenti
                try:
                    while True: 
                        message = self.analysis_queue.get_nowait()
                        # ... (duplicazione della logica di gestione messaggi qui per gli ultimi)
                        # Questo può essere rifattorizzato in una funzione helper
                        self.handle_queue_message(message)
                        self.analysis_queue.task_done()
                except QueueEmpty:
                    pass # Finito
                self.reset_ui_after_analysis() # Assicura reset UI

    def handle_queue_message(self, message): # Funzione helper per processare messaggi
        msg_type = message.get("type")
        if msg_type == "status_update": self.current_file_label.set(message.get("message", ""))
        elif msg_type == "new_row":
            item_id = self.tree.insert("", "end", values=message.get("data"))
            self.tree.see(item_id)
        elif msg_type == "spectrum_data":
            if not self.pause_event.is_set():
                self.display_spectrum(message.get("y"), message.get("sr"), message.get("title"))
        elif msg_type == "spectrum_error": self.show_spectrum_error(f"Errore spettro: {message.get('title', 'N/D')}")
        elif msg_type == "analysis_complete": messagebox.showinfo("Completato", message.get("message"))
        elif msg_type == "error_message": messagebox.showerror(message.get("title", "Errore"), message.get("message"))
        elif msg_type == "info_message": messagebox.showinfo(message.get("title", "Info"), message.get("message"))
        elif msg_type == "final_status": self.current_file_label.set(message.get("message", "Completato."))


    def reset_ui_after_analysis(self):
        self.current_file_label.set("Pronto per una nuova analisi o analisi terminata.")
        self.pause_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.browse_input_button.config(state=tk.NORMAL)
        self.browse_output_button.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.output_entry.config(state=tk.NORMAL)
        print("Thread di analisi terminato e UI resettata.")


    def display_spectrum(self, y, sr, track_title="Spettro Audio"):
        try:
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=512)), ref=np.max)
            # Usa le dimensioni attuali del canvas per la figura matplotlib
            # Questo potrebbe ancora causare problemi se il canvas non è ancora stato disegnato la prima volta
            canvas_width_px = self.spectrum_canvas.winfo_width()
            canvas_height_px = self.spectrum_canvas.winfo_height()

            if canvas_width_px <= 1 or canvas_height_px <= 1: # Canvas non ancora pronto
                print("Canvas dello spettro non ancora dimensionato, uso dimensioni di default.")
                fig_width_inches, fig_height_inches = 8, 2 # Default
            else:
                fig_width_inches = canvas_width_px / 100 # Assumendo 100 DPI
                fig_height_inches = canvas_height_px / 100

            fig, ax = plt.subplots(figsize=(fig_width_inches, fig_height_inches), dpi=100)
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', cmap='magma', ax=ax)
            ax.set_title(track_title, fontsize=9)
            ax.tick_params(axis='both', which='major', labelsize=7)
            fig.tight_layout(pad=0.1)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.05)
            plt.close(fig)
            buf.seek(0)
            
            img = Image.open(buf)
            if canvas_width_px > 1 and canvas_height_px > 1:
                img = img.resize((canvas_width_px, canvas_height_px), Image.Resampling.LANCZOS)
            
            self.image_ref = ImageTk.PhotoImage(img)
            self.spectrum_canvas.delete("all")
            self.spectrum_canvas.create_image(0, 0, anchor='nw', image=self.image_ref)
        except Exception as e:
            print(f"Errore in display_spectrum per {track_title}: {e}")
            self.show_spectrum_error(f"Errore spettro: {track_title.split('/')[-1]}")

    def show_spectrum_error(self, message="Errore visualizzazione spettro"):
        try:
            self.spectrum_canvas.delete("all")
            cw = self.spectrum_canvas.winfo_width()
            ch = self.spectrum_canvas.winfo_height()
            if cw > 1 and ch > 1:
                self.spectrum_canvas.create_text(cw/2, ch/2, text=message, fill="red", font=("Arial",10), anchor=tk.CENTER)
        except Exception: pass # Evita errori se il canvas non è pronto

    def on_closing(self): # Gestione chiusura finestra
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askyesno("Esci", "L'analisi è ancora in corso. Vuoi davvero uscire?"):
                # Qui potresti voler implementare un modo più pulito per fermare il thread
                # ad esempio usando un altro evento `self.stop_event.set()`
                # e poi `self.analysis_thread.join(timeout=1)`
                self.destroy()
            else:
                return # Non chiudere
        else:
            self.destroy()

if __name__ == '__main__':
    app = DJAnalyzerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing) # Gestisce la chiusura della finestra
    app.mainloop()