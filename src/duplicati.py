# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import defaultdict
import re
import time

class DuplicateFileRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Rimuovi Duplicati File Audio")

        # Elementi dell'interfaccia
        self.label = tk.Label(root, text="Seleziona una cartella per cercare i duplicati:")
        self.label.pack()

        self.select_button = tk.Button(root, text="Scegli Cartella", command=self.select_folder)
        self.select_button.pack()

        self.remove_button = tk.Button(root, text="Rimuovi Duplicati", command=self.remove_duplicates, state=tk.DISABLED)
        self.remove_button.pack()

        self.save_button = tk.Button(root, text="Salva Lista Duplicati", command=self.save_duplicates, state=tk.DISABLED)
        self.save_button.pack()

        self.txt = tk.Text(root, width=80, height=20)
        self.txt.pack()

        self.duplicate_files = defaultdict(list)

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Seleziona la cartella")
        if folder_path:
            self.folder_path = folder_path
            self.txt.delete(1.0, tk.END)
            self.txt.insert(tk.END, f"Cartella selezionata: {folder_path}\n")
            self.find_duplicates(folder_path)
            self.remove_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)

    def find_duplicates(self, folder_path):
        self.duplicate_files.clear()
        audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
        for root_dir, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(audio_extensions):
                    file_path = os.path.join(root_dir, file)
                    base_name = self.get_base_name(file)
                    file_size = os.path.getsize(file_path)
                    key = (base_name, file_size)
                    self.duplicate_files[key].append(file_path)

        self.txt.insert(tk.END, f"\nTotale gruppi di duplicati trovati: {sum(len(v) > 1 for v in self.duplicate_files.values())}\n")
        self.display_duplicates()

    def get_base_name(self, file_name):
        # Nuovo sistema avanzato per la pulizia dei nomi
        file_name = file_name.rsplit('.', 1)[0]  # Rimuove l'estensione
        patterns = [
            r'\s*[\(\{\[].*?[\)\}\]]\s*',  # Rimuove contenuto tra parentesi
            r'\s*-?\s*(Remix|Extended|Radio Edit|Club Mix|Acoustic|Live|Version|Mix|Edit|Dub|Bootleg|Instrumental|Cover|Master|Re-?edit)',
            r'\s*[_-]\s*'
        ]
        for pattern in patterns:
            file_name = re.sub(pattern, '', file_name, flags=re.IGNORECASE)
        return file_name.strip().lower()

    def display_duplicates(self):
        self.txt.insert(tk.END, "\nFile duplicati trovati:\n")
        found = False
        
        for (base_name, _), paths in self.duplicate_files.items():
            if len(paths) > 1:
                found = True
                self.txt.insert(tk.END, f"\n▶ {base_name.title()}:\n")
                for path in paths:
                    mtime = time.ctime(os.path.getmtime(path))
                    self.txt.insert(tk.END, f"  • {os.path.basename(path)} \n   ↳ {path}\n   ↳ Ultima modifica: {mtime}\n")

        if not found:
            self.txt.insert(tk.END, "Nessun duplicato trovato!\n")

    def save_duplicates(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    for (base_name, _), paths in self.duplicate_files.items():
                        if len(paths) > 1:
                            f.write(f"Gruppo: {base_name.title()}\n")
                            for path in paths:
                                f.write(f"  - {path}\n")
                            f.write("\n")
                messagebox.showinfo("Successo", "Lista salvata correttamente!")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{str(e)}")

    def remove_duplicates(self):
        confirmation = messagebox.askyesno(
            "Conferma",
            "Vuoi davvero eliminare tutti i duplicati?\n"
            "Verrà mantenuta solo la PRIMA versione di ogni file."
        )
        
        if confirmation:
            deleted_count = 0
            for (base_name, _), paths in self.duplicate_files.items():
                if len(paths) > 1:
                    for path in paths[1:]:
                        try:
                            os.remove(path)
                            deleted_count += 1
                            self.txt.insert(tk.END, f"Eliminato: {os.path.basename(path)}\n")
                        except Exception as e:
                            self.txt.insert(tk.END, f"Errore eliminazione {path}: {str(e)}\n")
            messagebox.showinfo("Risultato", f"Operazione completata!\nFile eliminati: {deleted_count}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateFileRemover(root)
    root.mainloop()