import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import librosa
import numpy as np
import soundfile as sf

# Mappature Camelot
camelot_map = {
    "G#m": "1A", "D#m": "2A", "A#m": "3A", "Fm": "4A",
    "Cm": "5A", "Gm": "6A", "Dm": "7A", "Am": "8A",
    "Em": "9B", "Bm": "10A", "F#m": "11A", "C#m": "12A",
    "G#": "1B", "D#": "2B", "A#": "3B", "F": "4B",
    "C": "5B", "G": "6B", "D": "7B", "A": "8B",
    "E": "9B", "B": "10B", "F#": "11B", "C#": "12B"
}

class AnalysisApp:
    def __init__(self, root):
        # Ensure working directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.root = root
        self.root.title("DJAnalyzer - Analysis")
        self.stop_flag = False

        # Left control panel
        left = tk.Frame(root)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        ttk.Button(left, text="Select Folder", command=self.select_folder).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Analyze", command=self.run_analysis).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Clear", command=self.clear_table).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Cancel", command=self.cancel_analysis).pack(fill=tk.X, pady=2)

        # Results table
        cols = ('file','bpm','key','energy','compatible')
        self.tree = ttk.Treeview(root, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.title())
        self.tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder = folder

    def run_analysis(self):
        if not hasattr(self, 'folder'):
            messagebox.showwarning("Warning","Select a folder first")
            return
        self.stop_flag = False
        mp3s = [f for f in os.listdir(self.folder) if f.lower().endswith('.mp3')]
        results = []
        for fname in mp3s:
            if self.stop_flag: break
            path = os.path.join(self.folder, fname)
            # Load audio
            y, sr = librosa.load(path, sr=None, mono=True)
            # BPM
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo = float(tempo) if isinstance(tempo, np.ndarray) else tempo
            bpm = int(round(tempo))
            # Placeholder key detection (to implement)
            key = 'C'
            camelot = camelot_map.get(key, '')
            # Energy 1-10 via RMS
            rms = np.sqrt(np.mean(y**2))
            energy = int(np.clip(rms*10, 1, 10))
            # Compatible keys (placeholder)
            comp_keys = []
            # Insert in table
            disp = f"{key} ({camelot})"
            self.tree.insert('', tk.END, values=(fname, bpm, disp, energy, ','.join(comp_keys)))
            results.append((fname, fname, bpm, disp, energy, ','.join(comp_keys)))
        # Save CSV
        out_dir = os.path.join(self.folder, 'Results')
        os.makedirs(out_dir, exist_ok=True)
        df = pd.DataFrame(results, columns=['orig_file','file','bpm','key','energy','compatible'])
        csv_path = os.path.join(out_dir,'analysis_results.csv')
        df.to_csv(csv_path, index=False)
        messagebox.showinfo('Analysis', f'Results saved to:\n{csv_path}')

    def clear_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def cancel_analysis(self):
        self.stop_flag = True

if __name__=='__main__':
    root = tk.Tk()
    AnalysisApp(root)
    root.mainloop()
