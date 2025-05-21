import os
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import timedelta
import threading
from PIL import Image, ImageTk
import time

class VideoAnalyzerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Analyzer Pro")
        self.root.geometry("900x700")
        self.root.configure(bg="#2e2e2e")
        
        # Variabili di stato
        self.video_path = ""
        self.output_folder = ""
        self.capture_interval = 5  # Default: 5 secondi
        self.is_playing = False
        
        # Configurazione stile
        self.setup_styles()
        
        # Frame principale
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Pannello superiore (controlli)
        self.setup_control_panel()
        
        # Pannello video
        self.setup_video_panel()
        
        # Console di log
        self.setup_log_panel()
    
    def setup_styles(self):
        """Configura gli stili per l'interfaccia"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#2e2e2e")
        self.style.configure("TButton", font=('Helvetica', 10), padding=5)
        self.style.map("TButton",
            background=[("active", "#45a049"), ("!disabled", "#4CAF50")],
            foreground=[("!disabled", "white")]
        )
    
    def setup_control_panel(self):
        """Pannello con pulsanti di controllo"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Pulsante Carica Video
        btn_load = ttk.Button(
            control_frame, 
            text="1. CARICA VIDEO", 
            command=self.load_video
        )
        btn_load.grid(row=0, column=0, padx=5)
        
        # Pulsante Cartella Output
        btn_output = ttk.Button(
            control_frame,
            text="2. CARTELLA OUTPUT",
            command=self.set_output_folder
        )
        btn_output.grid(row=0, column=1, padx=5)
        
        # Pulsanti Analisi
        btn_scene = ttk.Button(
            control_frame,
            text="3A. CAMBIO SCENA",
            command=lambda: self.start_analysis("scene_change")
        )
        btn_scene.grid(row=0, column=2, padx=5)
        
        btn_search = ttk.Button(
            control_frame,
            text="3B. CERCA OGGETTO",
            command=lambda: self.start_analysis("object_search")
        )
        btn_search.grid(row=0, column=3, padx=5)
        
        btn_interval = ttk.Button(
            control_frame,
            text="3C. INTERVALLO FOTO",
            command=self.set_capture_interval
        )
        btn_interval.grid(row=0, column=4, padx=5)
        
        # Pulsante Play/Pause
        self.btn_play = ttk.Button(
            control_frame,
            text="▶ PLAY",
            command=self.toggle_play
        )
        self.btn_play.grid(row=0, column=5, padx=5)
    
    def setup_video_panel(self):
        """Pannello per l'anteprima video"""
        video_frame = ttk.Frame(self.main_frame)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.lbl_video = ttk.Label(video_frame, background="black")
        self.lbl_video.pack(fill=tk.BOTH, expand=True)
        
        # Slider per la velocità
        speed_frame = ttk.Frame(video_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(speed_frame, text="Velocità:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=1.0)
        ttk.Scale(
            speed_frame,
            from_=0.1,
            to=4.0,
            variable=self.speed_var,
            command=self.update_speed
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
    
    def setup_log_panel(self):
        """Console per i log e i risultati"""
        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def load_video(self):
        """Carica un file video"""
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.avi *.mov")]
        )
        if self.video_path:
            self.log(f"Video caricato: {os.path.basename(self.video_path)}")
            self.preview_video()
    
    def set_output_folder(self):
        """Imposta la cartella di output"""
        self.output_folder = filedialog.askdirectory()
        if self.output_folder:
            self.log(f"Cartella output: {self.output_folder}")
    
    def set_capture_interval(self):
        """Imposta l'intervallo per la cattura"""
        interval = simpledialog.askinteger(
            "Intervallo cattura",
            "Inserisci intervallo (secondi):",
            parent=self.root,
            minvalue=1,
            maxvalue=60,
            initialvalue=self.capture_interval
        )
        if interval:
            self.capture_interval = interval
            self.log(f"Intervallo impostato: {interval}s")
    
    def toggle_play(self):
        """Avvia/ferma la riproduzione"""
        if not self.video_path:
            messagebox.showerror("Errore", "Caricare prima un video!")
            return
        
        self.is_playing = not self.is_playing
        self.btn_play.config(text="⏸ PAUSA" if self.is_playing else "▶ PLAY")
        
        if self.is_playing:
            threading.Thread(target=self.play_video, daemon=True).start()
    
    def play_video(self):
        """Riproduce il video in un thread separato"""
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = int(1000 / (fps * self.speed_var.get()))
        
        while self.is_playing and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Converti frame per tkinter
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = ImageTk.PhotoImage(image=img)
            
            # Aggiorna l'anteprima
            self.lbl_video.config(image=img)
            self.lbl_video.image = img
            
            time.sleep(delay / 1000)
        
        cap.release()
        self.is_playing = False
        self.btn_play.config(text="▶ PLAY")
    
    def update_speed(self, val):
        """Aggiorna la velocità di riproduzione"""
        if hasattr(self, 'speed_var'):
            self.log(f"Velocità modificata: {float(val):.1f}x")
    
    def start_analysis(self, mode):
        """Avvia l'analisi selezionata"""
        if not self.video_path:
            messagebox.showerror("Errore", "Caricare prima un video!")
            return
        if not self.output_folder:
            messagebox.showerror("Errore", "Impostare una cartella di output!")
            return
        
        self.log(f"\nAvvio analisi: {mode.upper()}")
        
        if mode == "scene_change":
            threading.Thread(target=self.detect_scene_changes, daemon=True).start()
        elif mode == "object_search":
            self.search_objects()
        else:
            threading.Thread(target=self.capture_at_intervals, daemon=True).start()
    
    def detect_scene_changes(self):
        """Rileva i cambi di scena"""
        # Implementazione semplificata
        cap = cv2.VideoCapture(self.video_path)
        prev_frame = None
        threshold = 30.0  # Soglia per il cambio scena
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            curr_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            curr_frame = cv2.GaussianBlur(curr_frame, (5, 5), 0)
            
            if prev_frame is not None:
                diff = cv2.absdiff(curr_frame, prev_frame)
                diff_mean = diff.mean()
                
                if diff_mean > threshold:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                    self.log(f"Cambio scena a {timedelta(seconds=timestamp)}")
                    self.save_frame(frame, timestamp)
            
            prev_frame = curr_frame
        
        cap.release()
        self.log("Analisi completata!")
    
    def capture_at_intervals(self):
        """Cattura fotogrammi a intervalli regolari"""
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * self.capture_interval)
        count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if count % frame_interval == 0:
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                self.save_frame(frame, timestamp)
                self.log(f"Salvato frame a {timedelta(seconds=timestamp)}")
            
            count += 1
        
        cap.release()
        self.log(f"Catturati {count // frame_interval} fotogrammi!")
    
    def save_frame(self, frame, timestamp):
        """Salva un fotogramma con timestamp"""
        if not self.output_folder:
            return
        
        time_str = str(timedelta(seconds=timestamp)).replace(":", "-")
        filename = f"frame_{time_str}.jpg"
        path = os.path.join(self.output_folder, filename)
        cv2.imwrite(path, frame)
    
    def search_objects(self):
        """Cerca oggetti (placeholder per AI)"""
        self.log("Funzionalità di ricerca con AI - DA IMPLEMENTARE")
        messagebox.showinfo("Info", "Questa funzionalità richiede l'integrazione con un modello AI (YOLO, TensorFlow, ecc.)")
    
    def preview_video(self):
        """Mostra il primo fotogramma come anteprima"""
        cap = cv2.VideoCapture(self.video_path)
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = ImageTk.PhotoImage(image=img)
            self.lbl_video.config(image=img)
            self.lbl_video.image = img
        cap.release()
    
    def log(self, message):
        """Aggiunge un messaggio alla console"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

if __name__ == "__main__":
    from tkinter import simpledialog
    root = tk.Tk()
    app = VideoAnalyzerPro(root)
    root.mainloop()