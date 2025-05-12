# DJAnalyzer - Programma completo (Analisi BPM, Chiave, Energia, Spettro)
# Versione con correzioni per caricamento file singolo e logica try-except migliorata

import os
import threading # Importato ma non ancora usato per threading UI, lo faremo dopo
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
CAMELOT_MAP = { # Corretto il nome da CAMELT_MAP a CAMELOT_MAP per coerenza
    "Abm": "1A", "Ebm": "2A", "Bbm": "3A", "Fm": "4A", "Cm": "5A", "Gm": "6A", "Dm": "7A", "Am": "8A",
    "Em": "9A", "Bm": "10A", "F#m": "11A", "C#m": "12A",
    "B": "1B", "F#": "2B", "C#": "3B", "G#": "4B", "D#": "5B", "A#": "6B",
    "E": "7B", "A": "8B", "D": "9B", "G": "10B", "C": "11B", "F": "12B"
    # Aggiunte le chiavi enarmoniche mancanti per una migliore copertura,
    # es. G#m è Abm, D#m è Ebm, ecc. per le minori.
    # Per le maggiori: G# è Ab, D# è Eb, A# è Bb.
    # Assicurati che l'output di analyze_key produca queste notazioni o adatta la mappa.
    # Per ora, la mappa attuale copre le notazioni più comuni con i diesis.
    # Se il tuo algoritmo di chiave produce bemolle, questa mappa andrà estesa.
}

PITCH_MAP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def analyze_key_internal(y, sr): # Rinominata per chiarezza, ora riceve y, sr
    """
    Analizza la chiave armonica.
    ATTENZIONE: La logica per determinare Maggiore/minore è ancora semplificata e da migliorare!
    """
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr) # Usiamo CQT per potenziale migliore stabilità tonale
    chroma_mean = chroma.mean(axis=1)
    
    # Trova il picco più forte nel cromagramma per la nota radice
    pitch_class_idx = chroma_mean.argmax()
    key_raw = PITCH_MAP[pitch_class_idx]

    # Euristica semplice per Maggiore/minore (DA MIGLIORARE!)
    # Confronta l'energia della terza minore vs terza maggiore rispetto alla radice
    # Terza minore: (radice + 3 semitoni) % 12
    # Terza maggiore: (radice + 4 semitoni) % 12
    third_minor_strength = chroma_mean[(pitch_class_idx + 3) % 12]
    third_major_strength = chroma_mean[(pitch_class_idx + 4) % 12]

    # Un'altra euristica comune è confrontare con template di chiavi maggiori/minori
    # Per ora, usiamo la semplice forza della terza.
    # Se la terza minore è più forte (o simile, in alcuni casi) della terza maggiore,
    # potrebbe essere minore. Questo è molto grezzo.
    is_minor = third_minor_strength > third_major_strength 
    # Potresti voler aggiungere una soglia o una logica più complessa qui.

    key_label = key_raw + ('m' if is_minor else '')
    camelot = CAMELOT_MAP.get(key_label, 'N/A') # Valore di default se la chiave non è nella mappa
    return key_label, camelot

# --- Modulo: BPM Analyzer ---
def analyze_bpm_internal(y, sr): # Rinominata per chiarezza, ora riceve y, sr
    tempo_array = librosa.beat.tempo(y=y, sr=sr) # tempo() restituisce un array
    bpm = int(round(tempo_array[0])) if tempo_array.size > 0 else 0
    return bpm

# --- Modulo: Energy Analyzer ---
def analyze_energy_internal(y): # Rinominata per chiarezza, ora riceve y
    rms = librosa.feature.rms(y=y)
    # Se rms è vuoto (es. file audio molto corto o silenzioso), np.mean darà un warning e NaN
    energy = float(np.mean(rms)) if rms.size > 0 and np.all(np.isfinite(rms)) else 0.0
    
    # Scala l'energia a un valore intero tra 1 e 10
    # Questa scalatura è arbitraria e potrebbe necessitare di aggiustamenti
    if energy == 0.0:
        scaled_energy = 1
    else:
        # Esempio di scalatura logaritmica per gestire meglio grandi range di RMS
        # log_energy = np.log10(energy * 1000 + 1) # Aggiungo 1 per evitare log(0), scalo per avere valori positivi
        # scaled_energy = min(10, max(1, int(np.ceil(log_energy * 2.5)))) # Ajusta il moltiplicatore
        # Per ora usiamo la tua scalatura originale
        scaled_energy = min(10, max(1, int(np.ceil(energy * 20))))

    color = energy_to_color(scaled_energy)
    return scaled_energy, color

def energy_to_color(value):
    palette = {
        1: "Gray", 2: "Blue", 3: "Cyan", 4: "Green", 5: "Lime",
        6: "Yellow", 7: "Orange", 8: "Red", 9: "Magenta", 10: "White"
    }
    return palette.get(value, "Gray")

# --- Modulo: Compatibility Checker ---
def find_compatible_keys(camelot_key): # Rinominata per chiarezza
    if not camelot_key or camelot_key == 'N/A':
        return []
    try:
        num_str = camelot_key[:-1]
        letter = camelot_key[-1]
        
        if not num_str.isdigit() or letter not in ('A', 'B'):
            return [] # Formato Camelot non valido

        num = int(num_str)
        
        compatible = [
            f"{num}{letter}",  # Stessa chiave
            f"{ (num % 12) + 1 }{letter}",  # Chiave successiva (dominante)
            f"{ (num - 2 + 12) % 12 + 1 }{letter}",  # Chiave precedente (sottodominante), gestisce il wrap around
            f"{num}{'A' if letter == 'B' else 'B'}"  # Relativa maggiore/minore
        ]
        # Rimuovi duplicati se num è 12 (es. 12+1 -> 1, 12-2+12 -> 11)
        return sorted(list(set(compatible))) # Ordina e rimuovi duplicati
    except Exception as e:
        print(f"Errore in find_compatible_keys per {camelot_key}: {e}")
        return []

# --- Interfaccia Grafica ---
class DJAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJAnalyzer v0.2")
        self.geometry("1000x800")
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.paused_analysis = False # Rinominata per chiarezza
        self.current_file_label = tk.StringVar(value="In attesa di analisi...") # Rinominata
        self.setup_ui()
        self.image_ref = None # Per mantenere un riferimento all'immagine nello spettro

    def setup_ui(self):
        # Frame per i controlli di input/output
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="Cartella Input:").pack(side=tk.LEFT)
        ttk.Entry(control_frame, textvariable=self.input_folder, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(control_frame, text="Sfoglia Input", command=self.browse_input).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Cartella Output:").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Entry(control_frame, textvariable=self.output_folder, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(control_frame, text="Sfoglia Output", command=self.browse_output).pack(side=tk.LEFT, padx=5)

        # Frame per i pulsanti di azione
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(action_frame, text="Avvia Analisi", command=self.start_analysis_thread).pack(side=tk.LEFT, padx=5) # Modificato per usare thread
        self.pause_button = ttk.Button(action_frame, text="Pausa Analisi", command=self.toggle_pause_analysis, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(self, textvariable=self.current_file_label, font=("Arial", 10), foreground="blue").pack(pady=(0, 5), fill=tk.X, padx=10)

        # Treeview per i risultati
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scrollbar_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(tree_frame, 
                                 columns=("File", "BPM", "Key", "Camelot", "Compatibili", "Energia", "Colore"), 
                                 show="headings", 
                                 yscrollcommand=tree_scrollbar_y.set,
                                 xscrollcommand=tree_scrollbar_x.set)
        
        self.tree.heading("File", text="File")
        self.tree.column("File", width=250, minwidth=150)
        self.tree.heading("BPM", text="BPM")
        self.tree.column("BPM", width=60, anchor=tk.CENTER)
        self.tree.heading("Key", text="Key")
        self.tree.column("Key", width=80, anchor=tk.CENTER)
        self.tree.heading("Camelot", text="Camelot")
        self.tree.column("Camelot", width=80, anchor=tk.CENTER)
        self.tree.heading("Compatibili", text="Compatibili")
        self.tree.column("Compatibili", width=150)
        self.tree.heading("Energia", text="Energia")
        self.tree.column("Energia", width=70, anchor=tk.CENTER)
        self.tree.heading("Colore", text="Colore Energia")
        self.tree.column("Colore", width=100, anchor=tk.CENTER)
        
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_scrollbar_y.config(command=self.tree.yview)
        tree_scrollbar_x.config(command=self.tree.xview)

        # Frame per lo Spettro
        self.spectrum_display_frame = ttk.LabelFrame(self, text="Spettro Audio") # Rinominato
        self.spectrum_display_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5, ipady=5)
        self.spectrum_canvas = tk.Canvas(self.spectrum_display_frame, bg="black", height=200) # Rinominato
        self.spectrum_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def browse_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def toggle_pause_analysis(self): # Rinominata
        self.paused_analysis = not self.paused_analysis
        self.pause_button.config(text="Riprendi Analisi" if self.paused_analysis else "Pausa Analisi")

    def start_analysis_thread(self):
        input_dir = self.input_folder.get()
        output_dir = self.output_folder.get()

        if not input_dir or not output_dir:
            messagebox.showerror("Errore", "Seleziona sia la cartella di Input che quella di Output.")
            return
        
        if not os.path.isdir(input_dir):
            messagebox.showerror("Errore", "La cartella di Input non è valida.")
            return
        if not os.path.isdir(output_dir):
            # Prova a crearla se non esiste
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"Cartella di Output creata: {output_dir}")
            except OSError as e:
                messagebox.showerror("Errore", f"Impossibile creare la cartella di Output: {e}")
                return

        # Disabilita il pulsante Avvia e abilita Pausa
        # Dovrai riabilitare Avvia e disabilitare Pausa quando il thread finisce
        # Questo è un semplice esempio, una gestione più robusta dello stato dei pulsanti è necessaria
        self.pause_button.config(state=tk.NORMAL) 
        # Potresti voler disabilitare anche il pulsante "Avvia Analisi" qui
        # self.start_button.config(state=tk.DISABLED) # Se avessi un riferimento al pulsante

        self.tree.delete(*self.tree.get_children()) # Pulisce la tabella
        self.paused_analysis = False # Resetta lo stato di pausa
        self.pause_button.config(text="Pausa Analisi")

        # Esegui l'analisi in un thread separato per non bloccare la GUI
        # Per ora, per semplicità e per testare le correzioni al caricamento file,
        # la lascio nel thread principale. IL THREADING VERRÀ IMPLEMENTATO SUCCESSIVAMENTE.
        # Se lo esegui ora con molti file, la GUI si bloccherà.
        # self.analysis_thread = threading.Thread(target=self.run_full_analysis, args=(input_dir, output_dir), daemon=True)
        # self.analysis_thread.start()
        self.run_full_analysis(input_dir, output_dir) # CHIAMATA DIRETTA PER ORA

    def run_full_analysis(self, input_dir, output_dir): # Rinominata
        """Esegue l'analisi completa dei file audio."""
        supported_extensions = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")
        files_to_analyze = []
        for root_dir, _, files in os.walk(input_dir):
            for f in files:
                if f.lower().endswith(supported_extensions):
                    files_to_analyze.append(os.path.join(root_dir, f))
        
        if not files_to_analyze:
            messagebox.showinfo("Info", "Nessun file audio supportato trovato nella cartella di input.")
            self.current_file_label.set("Nessun file da analizzare.")
            self.pause_button.config(state=tk.DISABLED)
            return

        results_data = [] # Rinominata
        
        for i, file_full_path in enumerate(files_to_analyze):
            # Gestione Pausa (semplice, per ora ferma solo l'aggiunta di nuovi file)
            # Una pausa reale in un thread richiederebbe un evento di threading.
            while self.paused_analysis:
                self.update_idletasks() # Permette alla GUI di rimanere reattiva
                self.after(100) # Aspetta un po' prima di ricontrollare

            file_name_only = os.path.basename(file_full_path)
            self.current_file_label.set(f"Analizzando ({i+1}/{len(files_to_analyze)}): {file_name_only}")
            self.update_idletasks()

            y_audio, sr_audio = None, None
            bpm_val, key_label_val, camelot_val, energy_val, color_val = 0, 'N/A', 'N/A', 1, "Gray"
            compatible_list = []

            try:
                print(f"DEBUG: Caricamento file: {file_full_path}")
                y_audio, sr_audio = librosa.load(file_full_path, sr=None) # Carica l'intero file
            except Exception as e:
                print(f"Errore nel caricamento di {file_name_only}: {e}")
                row_error = (file_name_only, "Errore Caricamento", "N/A", "N/A", "", "N/A", "N/A")
                self.tree.insert("", "end", values=row_error)
                results_data.append(dict(zip(self.tree["columns"], row_error)))
                self.show_spectrum_error(file_name_only) # Mostra un errore nello spettro
                continue

            # Analisi BPM
            try:
                bpm_val = analyze_bpm_internal(y_audio, sr_audio)
            except Exception as e:
                print(f"Errore BPM in {file_name_only}: {e}")
                bpm_val = 0 

            # Analisi Chiave
            try:
                key_label_val, camelot_val = analyze_key_internal(y_audio, sr_audio)
            except Exception as e:
                print(f"Errore chiave in {file_name_only}: {e}")
                key_label_val, camelot_val = 'N/A', 'N/A'

            # Analisi Energia
            try:
                energy_val, color_val = analyze_energy_internal(y_audio)
            except Exception as e:
                print(f"Errore energia in {file_name_only}: {e}")
                energy_val, color_val = 1, "Gray"
            
            # Chiavi Compatibili
            try:
                compatible_list = find_compatible_keys(camelot_val)
            except Exception as e:
                print(f"Errore compatibilità per {camelot_val} in {file_name_only}: {e}")
                compatible_list = []

            print(f"  Risultati per {file_name_only}: BPM: {bpm_val}, Key: {key_label_val}, Camelot: {camelot_val}, Energia: {energy_val} - Colore: {color_val}")

            row_values = (
                file_name_only, bpm_val, key_label_val, camelot_val, 
                ', '.join(compatible_list), energy_val, color_val
            )
            self.tree.insert("", "end", values=row_values)
            self.tree.yview_moveto(1.0) 
            results_data.append(dict(zip(self.tree["columns"], row_values)))

            # Mostra lo spettro solo se non siamo in modalità "pausa" per lo spettro (se implementata)
            # Per ora, la pausa generale ferma la visualizzazione dello spettro per nuovi file.
            if y_audio is not None: # Assicurati che l'audio sia stato caricato
                 self.display_spectrum(y_audio, sr_audio, file_name_only)


        # Salvataggio CSV
        if results_data:
            output_csv_file = os.path.join(output_dir, 'DJAnalyzer_analisi.csv')
            try:
                pd.DataFrame(results_data).to_csv(output_csv_file, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Completato", f"Analisi completata!\n{len(files_to_analyze)} file processati.\nRisultati salvati in: {output_csv_file}")
            except Exception as e:
                messagebox.showerror("Errore Salvataggio", f"Errore durante il salvataggio del file CSV: {e}")
        else:
            messagebox.showinfo("Info", "Nessun dato da salvare.")
            
        self.current_file_label.set(f"Analisi completata. {len(files_to_analyze)} file processati.")
        self.pause_button.config(state=tk.DISABLED)
        # Riabilita il pulsante Avvia qui, se lo avevi disabilitato
        # self.start_button.config(state=tk.NORMAL)

    def display_spectrum(self, y, sr, track_title="Spettro Audio"): # Rinominata e accetta y, sr
        try:
            # Calcola lo spettrogramma
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
            
            # Crea la figura matplotlib
            fig, ax = plt.subplots(figsize=(self.spectrum_canvas.winfo_width()/100, self.spectrum_canvas.winfo_height()/100), dpi=100)
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', cmap='magma', ax=ax)
            ax.set_title(track_title, fontsize=10)
            ax.tick_params(axis='both', which='major', labelsize=8)
            fig.tight_layout(pad=0.1) # Riduci il padding

            # Salva la figura in un buffer di memoria
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.05) # Aggiusta padding
            plt.close(fig) # Chiudi la figura per liberare memoria
            buf.seek(0)
            
            # Apri l'immagine con PIL e ridimensionala per adattarla al canvas
            img = Image.open(buf)
            canvas_width = self.spectrum_canvas.winfo_width()
            canvas_height = self.spectrum_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1: # Assicurati che il canvas abbia dimensioni valide
                img = img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            # Converti l'immagine PIL in PhotoImage di Tkinter
            self.image_ref = ImageTk.PhotoImage(img) # Salva un riferimento!
            
            # Mostra l'immagine sul canvas
            self.spectrum_canvas.delete("all")
            self.spectrum_canvas.create_image(0, 0, anchor='nw', image=self.image_ref)
            
        except Exception as e:
            print(f"Errore nella visualizzazione dello spettro per {track_title}: {e}")
            self.show_spectrum_error(f"Errore spettro: {track_title}")

    def show_spectrum_error(self, message="Errore visualizzazione spettro"):
        try:
            self.spectrum_canvas.delete("all")
            canvas_width = self.spectrum_canvas.winfo_width()
            canvas_height = self.spectrum_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                self.spectrum_canvas.create_text(
                    canvas_width / 2, canvas_height / 2,
                    text=message, fill="red", font=("Arial", 10), anchor=tk.CENTER
                )
        except Exception as e:
            print(f"Errore in show_spectrum_error: {e}")


if __name__ == '__main__':
    app = DJAnalyzerApp()
    app.mainloop()