# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext
from xml.etree import ElementTree as ET
from cue import rileva_cue  # modulo esterno per rilevamento cue
#from voice import rileva_inizio_voce  # modulo per inizio voce (attualmente disabilitato)

def append_output(widget, text):
    widget.insert(tk.END, text + "\n")
    widget.see(tk.END)

class DJAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        root.title("DJ Analyzer Tool v0.3b")

        self.out_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(self.out_dir, exist_ok=True)

        self.label = tk.Label(root, text="Seleziona un file audio:")
        self.label.pack()

        self.select_button = tk.Button(root, text="Scegli File", command=self.select_file)
        self.select_button.pack()

        self.cue_button = tk.Button(root, text="Cue", command=self.run_cues)
        self.cue_button.pack()

        self.txt = scrolledtext.ScrolledText(root, width=60, height=20)
        self.txt.pack()

    def select_file(self):
        filetypes = (('Audio Files', '*.mp3 *.wav'), ('All files', '*.*'))
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.audio_file = filepath
            append_output(self.txt, f"File selezionato: {filepath}")

    def run_cues(self):
        if not hasattr(self, 'audio_file'):
            append_output(self.txt, "Nessun file selezionato.")
            return

        append_output(self.txt, "Analisi files:")
        append_output(self.txt, "Avvio analisi...")

        cues = rileva_cue(self.audio_file)
        
        # Modifica del percorso di database.xml
        vdj_db_path = "D:\\progetti\\DJAnalyzer\\src\\VirtualDJ_test\\database.xml"
        
        try:
            tree = ET.parse(vdj_db_path)
            root = tree.getroot()
            updated = False

            # Controlliamo se il file audio è già presente nel database
            song_found = False
            for song in root.findall(".//Song"):
                if song.get("FilePath") == self.audio_file:
                    song_found = True
                    # Rimuoviamo i cue esistenti
                    for poi in song.findall("Poi"):
                        song.remove(poi)
                    # Aggiungiamo i nuovi cue
                    for cue in cues:
                        ET.SubElement(song, "Poi", {
                            "Name": cue['label'],
                            "Num": "0",
                            "Type": "cue",
                            "Start": str(cue['time']),
                            "Length": "0"
                        })
                    updated = True
                    break
            
            # Se il file audio non è presente, lo aggiungiamo come nuova traccia
            if not song_found:
                song_elem = ET.SubElement(root, "Song", {
                    "FilePath": self.audio_file,
                    "FileSize": "123456",  # Placeholder, puoi calcolare la dimensione se vuoi
                    "FileDate": str(int(os.path.getmtime(self.audio_file)))  # Placeholder per la data
                })
                for cue in cues:
                    ET.SubElement(song_elem, "Poi", {
                        "Name": cue['label'],
                        "Num": "0",
                        "Type": "cue",
                        "Start": str(cue['time']),
                        "Length": "0"
                    })
                updated = True

            if updated:
                tree.write(vdj_db_path, encoding="UTF-8", xml_declaration=True)
                append_output(self.txt, f"Cue aggiornati in: {vdj_db_path}")
            else:
                append_output(self.txt, "File non trovato nel database di VirtualDJ.")

        except FileNotFoundError:
            append_output(self.txt, "database.xml non trovato. Verifica che VirtualDJ sia installato e chiuso.")
        except Exception as e:
            append_output(self.txt, f"Errore durante l'aggiornamento del database: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DJAnalyzerGUI(root)
    root.mainloop()
