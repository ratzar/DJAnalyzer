import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import librosa
import numpy as np
import threading

camelot_map = {
    "G#m": "1A", "D#m": "2A", "A#m": "3A", "Fm": "4A",
    "Cm": "5A", "Gm": "6A", "Dm": "7A", "Am": "8A",
    "Em": "9A", "Bm": "10A", "F#m": "11A", "C#m": "12A",
    "G#": "1B", "D#": "2B", "A#": "3B", "F": "4B",
    "C": "5B", "G": "6B", "D": "7B", "A": "8B",
    "E": "9B", "B": "10B", "F#": "11B", "C#": "12B"
}

class DJAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJAnalyzer Improved")
        self.geometry("800x600")

        self.folder_path = tk.StringVar()

        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(frame, text="Folder:").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.folder_path, width=50).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT)
        ttk.Button(frame, text="Analyze", command=self.start_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Clear", command=self.clear_log).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=600, mode='determinate')
        self.progress.pack(padx=10, pady=5)
        self.progress_label = ttk.Label(self, text="Progress: 0/0")
        self.progress_label.pack(padx=10)

        self.log_text = tk.Text(self, wrap=tk.NONE)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def start_analysis(self):
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder")
            return

        for child in self.winfo_children():
            if isinstance(child, ttk.Button):
                child.state(['disabled'])

        threading.Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        files = [f for f in os.listdir(self.folder_path.get()) if f.lower().endswith(('.mp3', '.wav', '.flac'))]
        total = len(files)
        results = []

        self.progress['maximum'] = total

        for count, fname in enumerate(files, 1):
            self.progress['value'] = count
            self.progress_label.config(text=f"Progress: {count}/{total}")
            self.log_text.insert(tk.END, f"Analyzing: {fname}\n")
            self.log_text.see(tk.END)
            self.update_idletasks()

            path = os.path.join(self.folder_path.get(), fname)
            try:
                y, sr = librosa.load(path, sr=None)
                tempo = librosa.beat.tempo(y=y, sr=sr)
                bpm = int(round(tempo[0])) if tempo.size else 0
            except Exception as e:
                self.log_text.insert(tk.END, f"Error analyzing {fname}: {str(e)}\n")
                bpm, y = 0, np.array([])

            energy = float(np.mean(librosa.feature.rms(y=y))) if y.size else 0
            energy_scaled = min(10, max(1, int(np.ceil(energy * 10))))

            key_raw = 'C'
            camelot_code = camelot_map.get(key_raw, '')

            results.append({
                'orig_file': fname,
                'bpm': bpm,
                'key': f"{key_raw} ({camelot_code})",
                'energy': energy_scaled,
                'compatible': ''
            })

        out_folder = os.path.join(self.folder_path.get(), 'Results')
        os.makedirs(out_folder, exist_ok=True)
        df = pd.DataFrame(results)
        csv_path = os.path.join(out_folder, 'analysis_results.csv')
        df.to_csv(csv_path, index=False)

        self.log_text.insert(tk.END, f"Analysis complete. Results saved to {csv_path}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

        messagebox.showinfo("Done", "Analysis complete!")

        for child in self.winfo_children():
            if isinstance(child, ttk.Button):
                child.state(['!disabled'])

if __name__ == "__main__":
    app = DJAnalyzerApp()
    app.mainloop()