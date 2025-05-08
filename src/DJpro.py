import tkinter as tk
from tkinter import filedialog, messagebox

# Funzioni di caricamento file e cartella (già pronte)
def carica_file():
    file_path = filedialog.askopenfilename(title="Carica un brano audio", 
                                           filetypes=[("Tutti i file", "*.*"), 
                                                     ("File Audio", "*.mp3;*.wav")])
    if file_path:
        messagebox.showinfo("File Caricato", f"File caricato: {file_path}")
        return file_path
    else:
        messagebox.showwarning("Errore", "Nessun file selezionato.")
        return None

def carica_cartella():
    cartella_path = filedialog.askdirectory(title="Seleziona una cartella")
    if cartella_path:
        messagebox.showinfo("Cartella Selezionata", f"Cartella selezionata: {cartella_path}")
        return cartella_path
    else:
        messagebox.showwarning("Errore", "Nessuna cartella selezionata.")
        return None

# Funzioni per le operazioni dei vari pulsanti
def analisi_bpm():
    messagebox.showinfo("Analisi BPM", "Eseguiamo l'analisi del BPM")

def quantizzazione():
    messagebox.showinfo("Quantizzazione", "Eseguiamo la quantizzazione del brano")

def analisi_quantizzazione():
    messagebox.showinfo("Analisi Quantizzazione", "Eseguiamo l'analisi della quantizzazione")

def ottimizzazione():
    messagebox.showinfo("Ottimizzazione", "Eseguiamo l'ottimizzazione dei brani")

def analisi_energia():
    messagebox.showinfo("Analisi Energia", "Eseguiamo l'analisi dell'energia del brano")

# Funzione per creare l'interfaccia grafica
def crea_interfaccia():
    window = tk.Tk()
    window.title("DJ Analyzer")
    window.geometry("600x400")  # Impostare le dimensioni della finestra
    
    # Header
    header_label = tk.Label(window, text="DJ Analyzer", font=("Arial", 20))
    header_label.pack(pady=10)
    
    # Pulsante per caricare un file
    btn_carica_file = tk.Button(window, text="Carica File Audio", command=carica_file, width=20)
    btn_carica_file.pack(pady=5)

    # Pulsante per caricare una cartella
    btn_carica_cartella = tk.Button(window, text="Carica Cartella", command=carica_cartella, width=20)
    btn_carica_cartella.pack(pady=5)
    
    # Pulsanti per operazioni varie
    btn_analisi_bpm = tk.Button(window, text="Analisi BPM", command=analisi_bpm, width=20)
    btn_analisi_bpm.pack(pady=5)

    btn_quantizzazione = tk.Button(window, text="Quantizzazione", command=quantizzazione, width=20)
    btn_quantizzazione.pack(pady=5)

    btn_analisi_quantizzazione = tk.Button(window, text="Analisi Quantizzazione", command=analisi_quantizzazione, width=20)
    btn_analisi_quantizzazione.pack(pady=5)

    btn_ottimizzazione = tk.Button(window, text="Ottimizzazione", command=ottimizzazione, width=20)
    btn_ottimizzazione.pack(pady=5)

    btn_analisi_energia = tk.Button(window, text="Analisi Energia", command=analisi_energia, width=20)
    btn_analisi_energia.pack(pady=5)
    
    # Pulsante di chiusura
    btn_close = tk.Button(window, text="Chiudi", command=window.quit, width=20)
    btn_close.pack(pady=20)
    
    # Avvia la finestra principale
    window.mainloop()

# Esegui l'interfaccia
crea_interfaccia()
