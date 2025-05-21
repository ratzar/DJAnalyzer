# VIDEOANALYZER_AI_PRO v3.5 - VERSIONE DEFINITIVA
import os
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from datetime import timedelta
import threading
from PIL import Image, ImageTk
import numpy as np
from ultralytics import YOLO
import logging

class VideoAnalyzerAI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Analyzer AI PRO v3.5")
        self.root.geometry("1200x800")
        
        # Configurazione logging
        self.setup_logging()
        
        try:
            # Inizializzazione modelli
            self.log("Caricamento modelli AI...")
            self.ai_models = self._load_models()
            self.yolo_classes = self._get_yolo_classes()
            
            # Variabili di stato
            self.video_path = ""
            self.output_folders = {
                "scene": "1_Cambi_Scena",
                "interval": "2_Frame_Intervalli", 
                "ai": "3_Rilevamenti_AI"
            }
            self._create_folders()
            
            # UI
            self.setup_ui()
            self.log("Applicazione inizializzata con successo")
            
        except Exception as e:
            self.log(f"ERRORE INIZIALE: {str(e)}")
            messagebox.showerror("Errore Critico", f"Avvio fallito:\n{str(e)}")
            self.root.destroy()

    def setup_logging(self):
        """Configura il sistema di logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='video_analyzer.log',
            filemode='w'
        )
        self.logger = logging.getLogger()

    def log(self, message):
        """Scrive nei log e nella console"""
        self.logger.info(message)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.status_var.set(message[:50])  # Anteprima nella barra di stato
        self.root.update()

    def _load_models(self):
        """Carica i modelli disponibili con fallback"""
        models = {}
        try:
            models["Oggetti (YOLOv8n)"] = YOLO("yolov8n.pt")
            try:
                models["Volti (YOLOv8-face)"] = YOLO("yolov8n-face.pt")
            except:
                self.log("Modello facciale non trovato, uso solo YOLOv8n")
        except Exception as e:
            raise RuntimeError(f"Impossibile caricare i modelli: {str(e)}")
        return models

    def _get_yolo_classes(self):
        """Restituisce le classi base"""
        return [
            'person', 'bicycle', 'car', 'motorcycle', 
            'bus', 'truck', 'dog', 'cat'
        ]

    def _create_folders(self):
        """Crea le cartelle di output"""
        for folder in self.output_folders.values():
            os.makedirs(folder, exist_ok=True)

    def setup_ui(self):
        """Configura l'interfaccia utente"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Pannello controlli
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Pulsanti principali
        ttk.Button(control_frame, text="🎥 CARICA VIDEO", 
                  command=self.load_video).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="🔍 ANALISI SCENE", 
                  command=self.start_scene_analysis).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="⏱ INTERVALLO", 
                  command=self.set_interval).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="🤖 SELEZIONA CLASSI", 
                  command=self.show_class_selection).grid(row=0, column=3, padx=5)
        
        # Anteprima video
        self.preview_label = ttk.Label(main_frame, background="black")
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Console log
        self.log_text = tk.Text(main_frame, height=10, state="disabled", 
                              bg="#121212", fg="white", font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Barra stato
        self.status_var = tk.StringVar(value="Pronto")
        ttk.Label(main_frame, textvariable=self.status_var, 
                 relief=tk.SUNKEN).pack(fill=tk.X)

    def load_video(self):
        """Carica un file video"""
        try:
            path = filedialog.askopenfilename(
                filetypes=[("Video", "*.mp4 *.avi *.mov"), ("Tutti i file", "*.*")]
            )
            if path:
                self.video_path = path
                self.log(f"Video caricato: {os.path.basename(path)}")
                self.show_first_frame()
        except Exception as e:
            self.log(f"ERRORE durante il caricamento: {str(e)}")

    def show_first_frame(self):
        """Mostra il primo fotogramma"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img.thumbnail((900, 500))
                    self.current_preview = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=self.current_preview)
                cap.release()
        except Exception as e:
            self.log(f"ERRORE anteprima: {str(e)}")

    # ... (aggiungere qui le altre funzioni: show_class_selection, start_ai_analysis, etc.)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = VideoAnalyzerAI(root)
        root.mainloop()
    except Exception as e:
        with open("error.log", "w") as f:
            f.write(f"CRASH REPORT:\n{str(e)}")
        messagebox.showerror("Errore Fatale", f"Si è verificato un errore irreversibile:\n{str(e)}\nControlla error.log")