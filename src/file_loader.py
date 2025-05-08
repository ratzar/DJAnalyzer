from tkinter import filedialog, messagebox

def carica_file_audio() -> str | None:
    path = filedialog.askopenfilename(
        title="Carica un brano audio",
        filetypes=[("File Audio", "*.mp3;*.wav"), ("Tutti i file", "*.*")]
    )
    if not path:
        messagebox.showwarning("Errore", "Nessun file selezionato.")
        return None
    return path

def carica_cartella() -> str | None:
    path = filedialog.askdirectory(title="Seleziona una cartella")
    if not path:
        messagebox.showwarning("Errore", "Nessuna cartella selezionata.")
        return None
    return path
