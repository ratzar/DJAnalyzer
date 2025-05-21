import os
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from datetime import timedelta
import threading
from PIL import Image, ImageTk
import numpy as np

class VideoAnalyzerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Analyzer AI PRO")
        self.root.geometry("1100x800")
        
        # Configurazione AI (placeholder per YOLO/TensorFlow)
        self.ai_models = {
            "Volti": cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
            "Auto": None,  # Sostituire con modello reale
            "Oggetti generici": None
        }
        
        # Variabili di stato
        self.video_path = ""
        self.output_folder = "Video_Analysis_Output"
        self.scene_threshold = 25.0
        self.frame_interval = 5
        self.current_ai_model = None
        
        # Interfaccia
        self.setup_ui()
        os.makedirs(self.output_folder, exist_ok=True)

    def setup_ui(self):
        """Configurazione interfaccia avanzata"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Pannello superiore (controlli)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Pulsanti principali
        ttk.Button(control_frame, text="🎬 CARICA VIDEO", command=self.load_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔍 ANALISI SCENE", command=self.start_scene_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏱ INTERVALLO", command=self.set_interval).pack(side=tk.LEFT, padx=5)
        
        # Menu a tendina per AI
        self.ai_var = tk.StringVar()
        ai_menu = ttk.OptionMenu(control_frame, self.ai_var, "Scegli AI...", *self.ai_models.keys())
        ai_menu.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🤖 AVVIA AI", command=self.start_ai_analysis).pack(side=tk.LEFT, padx=5)
        
        # Anteprima video
        self.video_preview = ttk.Label(main_frame, background="black")
        self.video_preview.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Console di log avanzata
        self.log_console = tk.Text(main_frame, height=12, state="disabled", bg="#121212", fg="white")
        self.log_console.pack(fill=tk.BOTH)
        
        # Barra stato
        self.status_bar = ttk.Label(main_frame, text="Pronto", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X)

    def log(self, message):
        """Log avanzato con timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_console.config(state="normal")
        self.log_console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_console.see(tk.END)
        self.log_console.config(state="disabled")
        self.status_bar.config(text=message)
        self.root.update()

    def load_video(self):
        """Caricamento video con gestione errori"""
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.avi *.mov"), ("Tutti i file", "*.*")]
        )
        if self.video_path:
            self.log(f"Video caricato: {os.path.basename(self.video_path)}")
            self.show_first_frame()

    def show_first_frame(self):
        """Anteprima del primo fotogramma"""
        cap = cv2.VideoCapture(self.video_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((900, 500))
                self.current_preview = ImageTk.PhotoImage(img)
                self.video_preview.config(image=self.current_preview)
            cap.release()

    def set_interval(self):
        """Impostazione intervallo per cattura"""
        interval = simpledialog.askinteger(
            "Intervallo cattura",
            "Secondi tra i frame:",
            minvalue=1,
            maxvalue=60,
            initialvalue=self.frame_interval
        )
        if interval:
            self.frame_interval = interval
            self.log(f"Intervallo impostato a {interval} secondi")
            self.start_interval_capture()

    # ================= ANALISI SCENE =================
    def start_scene_analysis(self):
        if not self.check_video_loaded():
            return
        threading.Thread(target=self.analyze_scenes, daemon=True).start()

    def analyze_scenes(self):
        """Rilevamento avanzato cambi scena"""
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        prev_frame = None
        scene_count = 0
        
        self.log("Avvio analisi cambi scena...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Elaborazione frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_frame is not None:
                frame_diff = cv2.absdiff(gray, prev_frame)
                diff_score = np.mean(frame_diff)
                
                if diff_score > self.scene_threshold:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                    self.save_analysis_result(frame, timestamp, f"SCENA_{scene_count}")
                    scene_count += 1
                    self.log(f"Cambio scena #{scene_count} a {timedelta(seconds=timestamp)}")
            
            prev_frame = gray
        
        cap.release()
        self.log(f"ANALISI SCENE COMPLETATA! Trovati {scene_count} cambi.")

    # ================= MODALITÀ INTERVALLO =================
    def start_interval_capture(self):
        if not self.check_video_loaded():
            return
        threading.Thread(target=self.capture_at_intervals, daemon=True).start()

    def capture_at_intervals(self):
        """Cattura fotogrammi a intervalli regolari"""
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_skip = int(fps * self.frame_interval)
        count = 0
        saved_count = 0
        
        self.log(f"Avvio cattura ogni {self.frame_interval}s...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if count % frame_skip == 0:
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                self.save_analysis_result(frame, timestamp, f"INTERVALLO_{saved_count}")
                saved_count += 1
                self.log(f"Salvato frame a {timedelta(seconds=timestamp)}")
            
            count += 1
        
        cap.release()
        self.log(f"INTERVALLO COMPLETATO! Salvati {saved_count} frame.")

    # ================= MODALITÀ AI =================
    def start_ai_analysis(self):
        if not self.check_video_loaded():
            return
            
        model_name = self.ai_var.get()
        if model_name not in self.ai_models:
            messagebox.showerror("Errore", "Selezionare un modello AI valido!")
            return
            
        self.current_ai_model = self.ai_models[model_name]
        threading.Thread(target=self.run_ai_analysis, daemon=True).start()

    def run_ai_analysis(self):
        """Analisi con modello AI (esempio: rilevamento volti)"""
        cap = cv2.VideoCapture(self.video_path)
        found_objects = 0
        
        self.log(f"Avvio analisi AI: {self.ai_var.get()}...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Esempio con Haar Cascade (sostituire con modello reale)
            if self.ai_var.get() == "Volti":
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.current_ai_model.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                    self.save_analysis_result(frame, timestamp, f"AI_VOLTO_{found_objects}")
                    found_objects += 1
                    self.log(f"Trovato volto a {timedelta(seconds=timestamp)}")
        
        cap.release()
        self.log(f"AI COMPLETATA! Trovati {found_objects} oggetti.")

    # ================= FUNZIONI COMUNI =================
    def check_video_loaded(self):
        if not self.video_path:
            messagebox.showerror("Errore", "Nessun video caricato!")
            return False
        return True

    def save_analysis_result(self, frame, timestamp, prefix):
        """Salva i risultati con naming avanzato"""
        time_str = str(timedelta(seconds=timestamp)).replace(":", "-")
        filename = f"{prefix}_T-{time_str}.jpg"
        output_path = os.path.join(self.output_folder, filename)
        
        # Disegna timestamp sul frame
        cv2.putText(frame, f"Time: {timedelta(seconds=timestamp)}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imwrite(output_path, frame)

    def open_output_folder(self):
        if os.path.exists(self.output_folder):
            os.startfile(os.path.abspath(self.output_folder))
        else:
            self.log("ERRORE: Cartella non trovata!")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAnalyzerPro(root)
    root.mainloop()