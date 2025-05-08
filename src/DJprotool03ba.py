# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext
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
        base_name = os.path.splitext(os.path.basename(self.audio_file))[0]
        out_path = os.path.join(self.out_dir, f"{base_name}_cues.xml")

        with open(out_path, 'w') as f:
            f.write("<cues>\n")
            for cue in cues:
                f.write(f"  <cue time=\"{cue['time']}\" label=\"{cue['label']}\" />\n")
            f.write("</cues>\n")

        append_output(self.txt, f"Fine. Risultati in: {out_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DJAnalyzerGUI(root)
    root.mainloop()
