
import os
import librosa
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import datetime
import numpy as np
import soundfile as sf
from threading import Thread
import traceback

# Controllo dipendenze
def check_dependencies():
    required = ['librosa', 'pydub', 'simpleaudio']
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        raise ImportError(f"Installa i pacchetti mancanti: pip install {' '.join(missing)}")

class AudioAnalyzer:
    def __init__(self):
        self.output_folder = ''
        self.diagnostic_file = os.path.join(os.path.dirname(__file__), 'diagnostic_log.txt')

    def log_diagnostic(self, msg):
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.diagnostic_file, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")

    def analyze_audio(self, path):
        self.log_diagnostic(f"Inizio analisi: {path}")
        try:
            y, sr = librosa.load(path, mono=True)
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            bpm_val = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
            bpm = round(bpm_val, 2)
            key = 'N/A'
            try:
                y30 = y[:sr * 30]
                chroma = librosa.feature.chroma_cqt(y=y30, sr=sr)
                avg = np.mean(chroma, axis=1)
                root = int(np.argmax(avg))
                notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
                key = notes[root] + 'm'
            except Exception as e:
                self.log_diagnostic(f"Key detection skipped: {e}")
            beat_times = librosa.frames_to_time(beats, sr=sr)
            self.log_diagnostic(f"Analisi completata: BPM={bpm}, Key={key}")
            return {'success': True, 'bpm': bpm, 'key': key, 'beat_times': beat_times, 'waveform': y, 'sr': sr}
        except Exception as e:
            err = str(e)
            self.log_diagnostic(f"Errore analisi: {err}\n" + traceback.format_exc())
            return {'success': False, 'error': err}

class DJAnalyzerGUI:
    def __init__(self, root):
        check_dependencies()
        self.root = root
        self.analyzer = AudioAnalyzer()
        self._init_diagnostic()
        self._build_gui()

    def _init_diagnostic(self):
        with open(self.analyzer.diagnostic_file, 'w', encoding='utf-8') as f:
            f.write('=== DIAGNOSTIC LOG ===\n')
            f.write('Avvio: {}\n\n'.format(datetime.datetime.now()))

    def _build_gui(self):
        self.root.title('DJ Analyzer')
        self.root.geometry('900x600')
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        for txt, cmd in [
            ('Seleziona Cartella', self.select_folder),
            ('Analizza', self.analyze),
            ('Quantizza', self.quantize),
            ('Genera Cue', self.generate_cue),
            ('Ottimizza Playlist', self.optimize_playlist)
        ]:
            ttk.Button(btn_frame, text=txt, command=cmd).pack(side=tk.LEFT, padx=5)

        cols = ('file', 'bpm', 'key')
        self.tree = ttk.Treeview(frame, columns=cols, show='headings')
        for c, t in zip(cols, ['File', 'BPM', 'Key']):
            self.tree.heading(c, text=t)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        log_frame = ttk.Frame(frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log = scrolledtext.ScrolledText(log_frame, height=8)
        self.log.pack(fill=tk.BOTH, expand=True)

    def select_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.input_folder = d
            self.analyzer.output_folder = d
            self.log.insert(tk.END, f"Cartella: {d}\n")

    def analyze(self):
        if not hasattr(self, 'input_folder'):
            messagebox.showerror('Errore', 'Nessuna cartella selezionata')
            return
        self.tree.delete(*self.tree.get_children())
        self.log.insert(tk.END, 'Avvio analisi...\n')

        def worker():
            for fname in os.listdir(self.input_folder):
                if not fname.lower().endswith(('.mp3', '.wav')):
                    continue
                self.log.insert(tk.END, f"Analizzo: {fname}\n")
                self.log.see(tk.END)
                path = os.path.join(self.input_folder, fname)
                res = self.analyzer.analyze_audio(path)
                if res['success']:
                    bpm_str = f"{res['bpm']:.2f}"
                    base, ext = os.path.splitext(fname)
                    new_name = f"{base} [{bpm_str}]{ext}"
                    new_path = os.path.join(self.input_folder, new_name)
                    if not os.path.exists(new_path):
                        os.rename(path, new_path)
                        display = new_name
                    else:
                        display = fname
                    self.tree.insert('', tk.END, values=(display, bpm_str, res['key']))
                    self.log.insert(tk.END, f"Fatto: {display}: {bpm_str} BPM, Key={res['key']}\n")
                else:
                    self.log.insert(tk.END, f"⚠️ Errore analisi {fname}: {res['error']}\n")
                self.log.see(tk.END)
            self.log.insert(tk.END, 'Analisi completata.\n')
        Thread(target=worker, daemon=True).start()

    def quantize(self):
        if not hasattr(self, 'input_folder'):
            messagebox.showerror('Errore', 'Nessuna cartella selezionata')
            return
        qdir = os.path.join(self.input_folder, 'quantized')
        os.makedirs(qdir, exist_ok=True)

        def worker():
            for f in os.listdir(self.input_folder):
                if f.lower().endswith(('.mp3', '.wav')):
                    p = os.path.join(self.input_folder, f)
                    r = self.analyzer.analyze_audio(p)
                    if not r['success']:
                        continue
                    yq = librosa.effects.time_stretch(y=r['waveform'], rate=1.0)
                    sf.write(os.path.join(qdir, f), yq, r['sr'])
                    self.log.insert(tk.END, f"Quantizzato {f}\n")
            messagebox.showinfo('Fine', 'Quantizzazione completata')
        Thread(target=worker, daemon=True).start()

    def generate_cue(self):
        if not hasattr(self, 'input_folder'):
            messagebox.showerror('Errore', 'Seleziona prima la cartella di input')
            return
        cue_dir = os.path.join(self.input_folder, 'cue')
        os.makedirs(cue_dir, exist_ok=True)

        def worker_cue():
            for fname in os.listdir(self.input_folder):
                if not fname.lower().endswith(('.mp3', '.wav')):
                    continue
                self.log.insert(tk.END, f"Generazione cue per: {fname}\n")
                self.log.see(tk.END)
                path = os.path.join(self.input_folder, fname)
                res = self.analyzer.analyze_audio(path)
                if not res['success']:
                    self.log.insert(tk.END, f"⚠️ Skipped cue {fname}\n")
                    continue
                base, _ = os.path.splitext(fname)
                xml_path = os.path.join(cue_dir, base + '.vdjcue.xml')
                try:
                    with open(xml_path, 'w', encoding='utf-8') as f:
                        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                        f.write('<vdj xmlns="http://www.virtualdj.com/">\n')
                        f.write(f'  <song name="{base}">\n')
                        for i, t in enumerate(res['beat_times'][:8], start=1):
                            f.write(f'    <poi pos="{t:.3f}" type="cue" name="Cue{i}" color="0"/>\n')
                        f.write('  </song>\n')
                        f.write('</vdj>\n')
                    self.log.insert(tk.END, f"✓ Cue VDJ creati per {fname}\n")
                except Exception as e:
                    self.log.insert(tk.END, f"⚠️ Errore cue {fname}: {e}\n")
                self.log.see(tk.END)
            messagebox.showinfo('Cue', 'Generazione VDJ Cue completata')

        Thread(target=worker_cue, daemon=True).start()

    def optimize_playlist(self):
        messagebox.showinfo('Opt', 'Non implementato')

if __name__ == '__main__':
    root = tk.Tk()
    DJAnalyzerGUI(root)
    root.mainloop()
