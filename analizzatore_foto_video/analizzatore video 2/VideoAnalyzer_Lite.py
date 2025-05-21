import os
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import timedelta
import threading
from PIL import Image, ImageTk
import time

class VideoAnalyzerLite:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Analyzer LITE")
        self.root.geometry("900x650")
        
        # Variabili di stato
        self.video_path = ""
        self.output_folder = "output_frames"
        self.capture_interval = 5  # secondi
        self.is_playing = False
        
        # Crea cartella output
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Interfaccia
        self.setup_ui()

    def setup_ui(self):
        """Configurazione interfaccia semplificata"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Pulsanti principali
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="CARICA VIDEO", command=self.load_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ANALIZZA SCENE", command=self.analyze_scenes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="INTERVALLO FOTO", command=self.set_interval).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="APRI CARTELLA", command=self.open_output).pack(side=tk.LEFT, padx=5)
        
        # Anteprima video
        self.lbl_video = ttk.Label(main_frame, background="black")
        self.lbl_video.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Console log
        self.log_text = tk.Text(main_frame, height=8, state="disabled", bg="black", fg="white")
        self.log_text.pack(fill=tk.BOTH)
        
        # Barra di stato
        self.status_var = tk.StringVar(value="Pronto")
        ttk.Label(main_frame, textvariable=self.status_var).pack(side=tk.LEFT)

    def log(self, message):
        """Scrive nella console"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.status_var.set(message)
        self.root.update()

    def load_video(self):
        """Carica un file video"""
        self.video_path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi")])
        if self.video_path:
            self.log(f"Caricato: {os.path.basename(self.video_path)}")
            self.show_first_frame()

    def show_first_frame(self):
        """Mostra il primo fotogramma"""
        cap = cv2.VideoCapture(self.video_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((800, 450))
                self.current_frame = ImageTk.PhotoImage(img)
                self.lbl_video.config(image=self.current_frame)
            cap.release()

    def set_interval(self):
        """Imposta intervallo cattura"""
        interval = simpledialog.askinteger("Intervallo", "Secondi tra i frame:", minvalue=1, maxvalue=60)
        if interval:
            self.capture_interval = interval
            self.log(f"Intervallo impostato: {interval}s")

    def analyze_scenes(self):
        """Avvia l'analisi delle scene"""
        if not self.video_path:
            messagebox.showerror("Errore", "Carica prima un video!")
            return
            
        threading.Thread(target=self._analyze_scenes, daemon=True).start()

    def _analyze_scenes(self):
        """Rileva cambi scena (core)"""
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        prev_frame = None
        threshold = 30.0
        scene_count = 0
        
        self.log("Analisi scene iniziata...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Elaborazione frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5,5), 0)
            
            if prev_frame is not None:
                diff = cv2.absdiff(gray, prev_frame)
                diff_mean = diff.mean()
                
                if diff_mean > threshold:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                    self.save_frame(frame, timestamp)
                    scene_count += 1
                    self.log(f"Scena {scene_count} a {timedelta(seconds=timestamp)}")
            
            prev_frame = gray
        
        cap.release()
        self.log(f"Analisi completata! Trovate {scene_count} scene.")

    def save_frame(self, frame, timestamp):
        """Salva frame con timestamp"""
        time_str = f"{int(timestamp//3600):02d}-{int((timestamp%3600)//60):02d}-{int(timestamp%60):02d}"
        path = os.path.join(self.output_folder, f"scene_{time_str}.jpg")
        cv2.imwrite(path, frame)

    def open_output(self):
        """Apre la cartella output"""
        if os.path.exists(self.output_folder):
            os.startfile(self.output_folder)
        else:
            messagebox.showerror("Errore", "Cartella non trovata!")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAnalyzerLite(root)
    root.mainloop()