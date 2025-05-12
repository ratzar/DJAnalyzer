import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import queue
import time # Aggiunto per eventuali sleep o logging
import librosa
import numpy as np
import pandas as pd
import traceback # Per loggare eccezioni complete

# --- Costanti ---
CAMELOT_MAP = {
    'C': '8B', 'C#': '3B', 'D': '10B', 'D#': '5B', 'E': '12B', 'F': '7B',
    'F#': '2B', 'G': '9B', 'G#': '4B', 'A': '11B', 'A#': '6B',
    'Cm': '5A', 'C#m': '12A', 'Dm': '7A', 'D#m': '2A', 'Em': '9A', 'Fm': '4A',
    'F#m': '11A', 'Gm': '6A', 'G#m': '1A', 'Am': '8A', 'A#m': '3A', 'Bm': '10A'
}

CAMELOT_COLOR_MAP = {
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

# Scala colori per Energia (da adattare)
ENERGY_COLORS = {
    1: "PaleTurquoise1", 2: "PaleTurquoise2",
    3: "PaleGreen1", 4: "PaleGreen2",
    5: "SpringGreen2", 6: "SpringGreen3",
    7: "yellow1", 8: "gold1",
    9: "dark orange", 10: "red1"
}

class DJAnalyzerApp:
    def __init__(self, master):
        self.master = master
        master.title("DJAnalyzer v0.6.7 - Corretto") # Versione aggiornata
        master.geometry("800x600")

        self.SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a')

        self.input_folder_path = tk.StringVar()
        self.output_folder_path = tk.StringVar()
        self.status_label_var = tk.StringVar()
        self.status_label_var.set("Pronto. Seleziona le cartelle e avvia l'analisi.")

        self.is_paused = False
        self.stop_requested = False
        self.analysis_paused_event = threading.Event()
        self.analysis_paused_event.set() # Inizia non in pausa

        self.result_queue = queue.Queue()
        self.analysis_thread = None
        self.analyzed_data = [] # Lista per i dati da salvare in CSV

        # --- GUI Setup ---
        # Frame per selezione cartelle
        folder_frame = ttk.LabelFrame(master, text="Cartelle")
        folder_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(folder_frame, text="Cartella Input", command=self.select_input_folder).grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(folder_frame, textvariable=self.input_folder_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="Cartella Output", command=self.select_output_folder).grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(folder_frame, textvariable=self.output_folder_path, width=50).grid(row=1, column=1, padx=5, pady=5)

        # Frame per controlli analisi
        control_frame = ttk.LabelFrame(master, text="Controlli Analisi")
        control_frame.pack(padx=10, pady=5, fill="x")

        self.start_button = ttk.Button(control_frame, text="Avvia Analisi", command=self.start_analysis)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.pause_button = ttk.Button(control_frame, text="Pausa", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_button = ttk.Button(control_frame, text="Ferma", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Etichetta di stato
        status_label = ttk.Label(master, textvariable=self.status_label_var)
        status_label.pack(padx=10, pady=5, fill="x")

        # Treeview per risultati
        tree_frame = ttk.Frame(master)
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("File", "BPM", "Key", "Camelot", "Compatibili", "Energia"), show="headings")
        self.tree.heading("File", text="File")
        self.tree.heading("BPM", text="BPM")
        self.tree.heading("Key", text="Key")
        self.tree.heading("Camelot", text="Camelot")
        self.tree.heading("Compatibili", text="Compatibili")
        self.tree.heading("Energia", text="Energia")

        self.tree.column("File", width=250)
        self.tree.column("BPM", width=50, anchor=tk.CENTER)
        self.tree.column("Key", width=50, anchor=tk.CENTER)
        self.tree.column("Camelot", width=70, anchor=tk.CENTER)
        self.tree.column("Compatibili", width=150)
        self.tree.column("Energia", width=60, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        
        # Configura i tag colore (lo facciamo dinamicamente in process_queue ora)
        for code, color_name in CAMELOT_COLOR_MAP.items():
            if color_name != 'white': # 'white' è lo sfondo di default
                 try:
                    self.tree.tag_configure(color_name, background=color_name)
                 except tk.TclError as e:
                    print(f"Attenzione: Colore '{color_name}' non valido per tag Treeview: {e}")
        
        # Configura colori per energia (se diversi dai camelot)
        for level, color_name in ENERGY_COLORS.items():
            tag_name = f"energy_{color_name}" # Assicura nomi univoci per i tag
            try:
                self.tree.tag_configure(tag_name, background=color_name)
            except tk.TclError as e:
                print(f"Attenzione: Colore energia '{color_name}' non valido per tag Treeview: {e}")


        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def select_input_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.input_folder_path.set(folder_selected)

    def select_output_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_folder_path.set(folder_selected)

    def update_status_label(self, message):
        self.status_label_var.set(message)
        print(f"STATUS: {message}") # Anche in console per debug

    def start_analysis(self):
        print("DEBUG: Pulsante 'Avvia Analisi' premuto.")
        self.is_paused = False
        self.stop_requested = False
        self.analysis_paused_event.set()

        input_path = self.input_folder_path.get()
        output_path = self.output_folder_path.get()

        if not input_path or not os.path.isdir(input_path):
            self.update_status_label("Errore: Cartella di input non valida o non selezionata.")
            messagebox.showerror("Errore", "Seleziona una cartella di input valida.")
            return
        if not output_path or not os.path.isdir(output_path):
            self.update_status_label("Errore: Cartella di output non valida o non selezionata.")
            messagebox.showerror("Errore", "Seleziona una cartella di output valida.")
            return

        # --- INIZIO NUOVA LOGICA PER RACCOGLIERE FILE (SOLO CARTELLA PRINCIPALE) ---
        audio_files_to_process = []
        try:
            print(f"DEBUG: Scansione cartella input (solo principale): {input_path}")
            for item_name in os.listdir(input_path):
                item_full_path = os.path.join(input_path, item_name)
                if os.path.isfile(item_full_path):
                    if item_name.lower().endswith(self.SUPPORTED_EXTENSIONS):
                        audio_files_to_process.append(item_full_path)
            
            print(f"DEBUG: File trovati per l'analisi: {audio_files_to_process}")

            if not audio_files_to_process:
                self.update_status_label("Nessun file audio supportato trovato nella cartella selezionata.")
                messagebox.showinfo("Info", "Nessun file audio supportato trovato nella cartella selezionata.")
                return # Non c'è niente da fare, torna allo stato iniziale dei pulsanti (già gestito)
                
        except Exception as e:
            error_msg = f"Errore durante la lettura della cartella di input: {e}"
            traceback.print_exc()
            self.update_status_label(error_msg)
            messagebox.showerror("Errore Lettura Cartella", error_msg)
            return
        # --- FINE NUOVA LOGICA PER RACCOGLIERE FILE ---

        # Pulisci la UI e i dati precedenti
        print("DEBUG: Pulizia Treeview e dati analizzati.")
        self.tree.delete(*self.tree.get_children())
        self.analyzed_data.clear()

        # Aggiorna stato pulsanti
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL, text="Pausa")
        self.stop_button.config(state=tk.NORMAL)
        self.select_input_button.config(state=tk.DISABLED)
        self.select_output_button.config(state=tk.DISABLED)

        self.update_status_label("Avvio analisi...")
        
        # Avvia il thread di analisi
        # Passa una COPIA della lista dei file, così modifiche future non la impattano
        self.analysis_thread = threading.Thread(target=self._worker_thread, args=(list(audio_files_to_process),), daemon=True)
        self.analysis_thread.start()
        print(f"DEBUG: Thread di analisi avviato: {self.analysis_thread.name}")

        # Avvia il controllo periodico della coda dei risultati
        # Questo viene chiamato solo una volta qui per iniziare il polling
        self.master.after(100, self.process_queue)

    def _worker_thread(self, files_to_analyze):
        print(f"DEBUG THREAD ({threading.get_ident()}): Inizio elaborazione di {len(files_to_analyze)} file.")
        total_files = len(files_to_analyze)
        try:
            for i, file_path in enumerate(files_to_analyze):
                if self.stop_requested:
                    self.result_queue.put(("status", "Analisi interrotta dall'utente."))
                    print(f"DEBUG THREAD ({threading.get_ident()}): Stop richiesto, interruzione ciclo.")
                    break

                self.analysis_paused_event.wait() # Si blocca qui se is_paused è True

                if self.stop_requested: # Ricontrolla dopo eventuale pausa
                    self.result_queue.put(("status", "Analisi interrotta dall'utente (dopo pausa)."))
                    print(f"DEBUG THREAD ({threading.get_ident()}): Stop richiesto dopo pausa, interruzione ciclo.")
                    break
                
                self.result_queue.put(("processing", os.path.basename(file_path), i + 1, total_files))
                
                try:
                    self.analyze_file_and_queue_results(file_path)
                except Exception as e:
                    error_msg = f"Errore analisi di {os.path.basename(file_path)}: {e}"
                    print(f"ECCEZIONE in _worker_thread per {file_path}:")
                    traceback.print_exc()
                    self.result_queue.put(("error", error_msg))
        finally:
            # Assicura che il messaggio di completamento venga inviato
            # anche se il ciclo viene interrotto o c'è un'eccezione non gestita sopra
            if not self.stop_requested:
                 self.result_queue.put(("status", f"Elaborazione di {total_files} file terminata nel thread."))
            self.result_queue.put(("analysis_complete", None))
            print(f"DEBUG THREAD ({threading.get_ident()}): Segnale 'analysis_complete' inviato.")


    def analyze_file_and_queue_results(self, file_path):
        filename = os.path.basename(file_path)
        print(f"THREAD: Caricamento {file_path}")

        try:
            y, sr = librosa.load(file_path, sr=None)
            
            # BPM
            tempo_array = librosa.beat.tempo(y=y, sr=sr, aggregate=None) # Questo causa FutureWarning
            bpm = int(np.median(tempo_array))

            # Key
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key_str = self.detect_key_from_chroma(chroma) 
            
            camelot_code = CAMELOT_MAP.get(key_str, "N/A")
            camelot_color_name = CAMELOT_COLOR_MAP.get(camelot_code, "white") # Nome colore per tag
            
            compatible_keys_str = "N/A"
            if camelot_code != "N/A":
                compatible_keys = self.find_compatible_keys(camelot_code)
                compatible_keys_str = ", ".join(compatible_keys)

            # --- NUOVA LOGICA ENERGIA ---
            scaled_energy, energy_color_name = self.analyze_energy(y, sr) # Passa y, sr
            # --- FINE NUOVA LOGICA ENERGIA ---

            result_data = {
                "File": filename, "BPM": bpm, "Key": key_str,
                "Camelot": camelot_code, "Compatibili": compatible_keys_str,
                "Energia": scaled_energy,
                "_camelot_color_tag": camelot_color_name, # Per il tag colore della riga
                "_energy_color_tag": f"energy_{ENERGY_COLORS.get(scaled_energy, 'grey')}" # Per il tag colore cella Energia
            }
            self.result_queue.put(("data", result_data))
            # Non aggiungiamo a self.analyzed_data qui, ma in process_queue dopo l'inserimento nella treeview
        except Exception as e:
            error_msg = f"Errore dettagliato durante analisi di {filename}: {e}"
            print(f"ECCEZIONE in analyze_file_and_queue_results per {filename}:")
            traceback.print_exc()
            self.result_queue.put(("error", error_msg))


    def detect_key_from_chroma(self, chroma_features):
        # Implementazione Krumhansl-Schmuckler approssimata (placeholder)
        # Maggiori (0-11), Minori (12-23)
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        chroma_mean = np.mean(chroma_features, axis=1)
        
        correlations_major = [np.corrcoef(chroma_mean, np.roll(major_profile, i))[0, 1] for i in range(12)]
        correlations_minor = [np.corrcoef(chroma_mean, np.roll(minor_profile, i))[0, 1] for i in range(12)]
        
        max_corr_major = np.max(correlations_major)
        max_corr_minor = np.max(correlations_minor)
        
        best_idx_major = np.argmax(correlations_major)
        best_idx_minor = np.argmax(correlations_minor)
        
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        if max_corr_major > max_corr_minor:
            return keys[best_idx_major]
        else:
            return keys[best_idx_minor] + "m"

    def find_compatible_keys(self, camelot_code):
        if camelot_code == "N/A": return []
        num = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        compatible = [camelot_code] # Sé stesso
        
        # Stessa lettera, numero +/- 1
        compatible.append(f"{ (num - 1 -1 + 12) % 12 + 1 }{mode}") # num-1
        compatible.append(f"{ (num + 1 -1 + 12) % 12 + 1 }{mode}") # num+1
        
        # Stesso numero, lettera opposta
        compatible.append(f"{num}{'B' if mode == 'A' else 'A'}")
        
        return sorted(list(set(c for c in compatible if c in CAMELOT_MAP.values())))


    # --- NUOVA FUNZIONE ENERGIA ---
    def analyze_energy(self, y_audio, sr_audio): # Riceve y e sr
        try:
            # y, sr = librosa.load(file_path, sr=None) # Caricamento già fatto prima
            rms_frames = librosa.feature.rms(y=y_audio)[0]
            
            energy_mean = np.mean(rms_frames)
            energy_std = np.std(rms_frames)

            energy_score = energy_mean + 0.5 * energy_std # La tua formula
            
            # DEBUG ENERGIA: Stampa energy_score prima della scalatura
            print(f"DEBUG ENERGIA: mean_rms={energy_mean:.4f}, std_rms={energy_std:.4f}, RAW energy_score={energy_score:.6f}")

            # Normalizza tra 1 e 10 (scalatura logica, non lineare - DA TARARE!)
            scaled_value = 1 # Default a 1
            if energy_score > 0: # Evita errori con log o divisioni per zero se energy_score è 0 o negativo
                 # Prova con una scalatura che mappa un range atteso (es. 0.01 a 0.2) a 1-10
                 # Questi min_expected_score e max_expected_score sono da aggiustare!
                min_expected_score = 0.005 # Valore minimo che potrebbe avere senso
                max_expected_score = 0.15   # Valore massimo atteso per un brano "forte"
                
                if energy_score <= min_expected_score:
                    scaled_value = 1
                elif energy_score >= max_expected_score:
                    scaled_value = 10
                else:
                    # Scalatura lineare nel range atteso
                    scaled_value = 1 + 9 * (energy_score - min_expected_score) / (max_expected_score - min_expected_score)
            
            scaled_value = int(np.clip(round(scaled_value), 1, 10)) # Arrotonda prima di clip e int
            print(f"DEBUG ENERGIA: Scaled Energy = {scaled_value}")

            # Colore basato sulla nuova scala
            color_name = ENERGY_COLORS.get(scaled_value, "grey") # Default a grigio
            return scaled_value, color_name

        except Exception as e:
            print(f"Errore nell'analisi energia: {e}")
            traceback.print_exc()
            return 1, ENERGY_COLORS.get(1, "grey") # Default a 1 e colore associato
    # --- FINE NUOVA FUNZIONE ENERGIA ---

    def process_queue(self):
        # print("DEBUG: process_queue chiamata.") # Può essere molto verboso
        try:
            while True: # Processa tutti i messaggi attualmente nella coda
                message_type, data, *extra_data = self.result_queue.get_nowait()
                
                if message_type == "data":
                    # Aggiungi alla treeview
                    row_values = (data["File"], data["BPM"], data["Key"], data["Camelot"], 
                                  data["Compatibili"], data["Energia"])
                    
                    camelot_tag = data.get("_camelot_color_tag", "white")
                    # energy_tag = data.get("_energy_color_tag", "white") # Non usato per ora per riga intera

                    # Assicurati che il tag esista prima di usarlo
                    try:
                        self.tree.tag_configure(camelot_tag, background=camelot_tag)
                    except tk.TclError: # Se il colore non è valido o già configurato con altro
                        if camelot_tag != 'white': # Non loggare per il bianco di default
                            print(f"Avviso: Impossibile configurare/usare tag colore Camelot: {camelot_tag}")
                        camelot_tag = () # No tag se problematico
                    
                    item_id = self.tree.insert("", tk.END, values=row_values, tags=(camelot_tag,))
                    self.analyzed_data.append(data) # Aggiungi ai dati per il CSV
                    self.tree.see(item_id) # Scrolla per vedere l'ultimo elemento

                elif message_type == "status":
                    self.update_status_label(data)
                elif message_type == "error":
                    self.update_status_label(f"ERRORE: {data}")
                elif message_type == "processing":
                    filename, current_num, total_num = data, extra_data[0], extra_data[1]
                    self.update_status_label(f"Elaborazione ({current_num}/{total_num}): {filename}")
                
                elif message_type == "analysis_complete":
                    self.update_status_label("Analisi completata. Salvataggio risultati...")
                    print("DEBUG: Ricevuto 'analysis_complete' in process_queue.")
                    self.save_results_to_csv()
                    self.reset_ui_after_analysis()
                    return # IMPORTANTE: Esci da process_queue per fermare il polling `after`

        except queue.Empty:
            pass # La coda è vuota, niente da fare ora
        
        # Continua a controllare la coda SOLO SE il thread è vivo o la coda non è vuota
        # E non abbiamo ancora ricevuto 'analysis_complete' (che ora fa 'return')
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.master.after(100, self.process_queue)
        elif not self.result_queue.empty(): # Se il thread è morto ma c'è ancora roba
             print("DEBUG: Thread morto ma coda non vuota, riprogrammo process_queue.")
             self.master.after(100, self.process_queue)
        else:
            # Se il thread è morto e la coda è vuota, ma non abbiamo gestito analysis_complete
            # Questo non dovrebbe succedere se _worker_thread manda sempre il segnale
            if self.analysis_thread is not None: # Significa che un'analisi era partita
                print("AVVISO: Thread morto, coda vuota, 'analysis_complete' non gestito esplicitamente. UI potrebbe essere in stato inconsistente.")
                # Potremmo forzare un reset, ma è meglio che analysis_complete sia sempre gestito.
                # self.reset_ui_after_analysis() # Sconsigliato qui, potrebbe mascherare problemi


    def reset_ui_after_analysis(self):
        print("DEBUG: reset_ui_after_analysis chiamata.")
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Pausa")
        self.stop_button.config(state=tk.DISABLED)
        self.select_input_button.config(state=tk.NORMAL)
        self.select_output_button.config(state=tk.NORMAL)
        
        self.is_paused = False
        # self.stop_requested è già False o gestito da start_analysis
        
        self.analysis_thread = None # Molto importante per la logica di process_queue
        
        # Svuota la coda da eventuali messaggi residui (anche se non dovrebbe essercene molti)
        print("DEBUG: Tentativo di svuotare la coda durante il reset finale.")
        count = 0
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
                count +=1
            except queue.Empty:
                break
        if count > 0:
            print(f"DEBUG: Rimossi {count} messaggi residui dalla coda durante il reset.")
        else:
            print("DEBUG: Coda già vuota durante il reset finale.")
        
        self.update_status_label("Pronto per una nuova analisi.")


    def toggle_pause(self):
        if self.is_paused:
            self.is_paused = False
            self.analysis_paused_event.set() # Sblocca il thread
            self.pause_button.config(text="Pausa")
            self.update_status_label("Analisi ripresa.")
        else:
            self.is_paused = True
            self.analysis_paused_event.clear() # Blocca il thread
            self.pause_button.config(text="Riprendi")
            self.update_status_label("Analisi in pausa.")

    def stop_analysis(self):
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.stop_requested = True
            self.analysis_paused_event.set() # Sblocca se era in pausa per permettere lo stop
            self.update_status_label("Richiesta di interruzione analisi...")
            print("DEBUG: Richiesta di stop inviata.")
            # Il thread dovrebbe terminare e inviare 'analysis_complete'
            # che poi chiamerà reset_ui_after_analysis.
            # Non resettiamo i pulsanti qui direttamente.
            self.stop_button.config(state=tk.DISABLED) # Disabilita subito stop per evitare click multipli
            self.pause_button.config(state=tk.DISABLED)


    def save_results_to_csv(self):
        if not self.analyzed_data:
            self.update_status_label("Nessun dato da salvare.")
            return

        output_folder = self.output_folder_path.get()
        if not output_folder or not os.path.isdir(output_folder):
            self.update_status_label("Cartella di output non valida. Impossibile salvare CSV.")
            messagebox.showwarning("Salvataggio CSV", "Seleziona una cartella di output valida per salvare il CSV.")
            return

        # Prepara i dati per il DataFrame, escludendo le chiavi interne con '_'
        df_data = [{k: v for k, v in row.items() if not k.startswith('_')} for row in self.analyzed_data]
        df = pd.DataFrame(df_data)
        
        # Ordina le colonne come nella Treeview
        column_order = ["File", "BPM", "Key", "Camelot", "Compatibili", "Energia"]
        df = df[column_order] # Riordina e seleziona solo queste colonne

        try:
            # Crea un nome file univoco o standard
            # Potremmo usare un timestamp per evitare sovrascritture accidentali
            # Ma per ora usiamo un nome fisso come da specifiche iniziali
            filename = "DJAnalyzer_analisi_completata.csv"
            full_path = os.path.join(output_folder, filename)
            
            df.to_csv(full_path, index=False, encoding='utf-8-sig') # utf-8-sig per Excel
            self.update_status_label(f"Risultati salvati in: {full_path}")
            messagebox.showinfo("Salvataggio CSV", f"Risultati salvati in:\n{full_path}")
        except Exception as e:
            error_msg = f"Errore durante il salvataggio del CSV: {e}"
            traceback.print_exc()
            self.update_status_label(error_msg)
            messagebox.showerror("Errore Salvataggio CSV", error_msg)

    def on_closing(self):
        if self.analysis_thread and self.analysis_thread.is_alive():
            if messagebox.askokcancel("Esci", "L'analisi è ancora in corso. Vuoi davvero uscire?"):
                self.stop_requested = True
                self.analysis_paused_event.set() # Sblocca se in pausa
                # Dai un po' di tempo al thread per terminare, ma non bloccare troppo la GUI
                if self.analysis_thread:
                    self.analysis_thread.join(timeout=0.5) 
                self.master.destroy()
            else:
                return # Non uscire
        else:
            self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DJAnalyzerApp(root)
    root.mainloop()