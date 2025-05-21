import os
import json

def carica_stato():
    if os.path.exists("stato_progetto.json"):
        with open("stato_progetto.json", "r") as f:
            return json.load(f)
    return {}

def salva_stato(ultimo_lavoro, prossimi_passi):
    stato = {
        "dipendenze": ["opencv-python", "mediapipe", "pillow"],
        "ultimo_lavoro": ultimo_lavoro,
        "prossimi_passi": prossimi_passi,
        "configurazioni": {
            "soglia_scena": 0.3,
            "intervallo_campionamento": 5
        }
    }
    with open("stato_progetto.json", "w") as f:
        json.dump(stato, f, indent=4)

# Esempio d'uso:
if __name__ == "__main__":
    # All'avvio
    stato = carica_stato()
    if stato:
        print(f"⚡ Riprendiamo da: {stato['ultimo_lavoro']}")
        print(f"🔜 Prossimi passi: {stato['prossimi_passi']}")

    # Alla chiusura
    salva_stato(
        ultimo_lavoro="Implementato rilevamento gesti",
        prossimi_passi="Aggiungere filtro per dimensioni immagini"
    )






import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import mediapipe as mp
from collections import defaultdict

# --- Sistema di Salvataggio Stato ---
STATO_FILE = "stato_progetto.json"

def carica_stato():
    """Carica lo stato precedente da file"""
    if os.path.exists(STATO_FILE):
        try:
            with open(STATO_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salva_stato(**kwargs):
    """Salva lo stato attuale"""
    stato = carica_stato()
    stato.update(kwargs)
    with open(STATO_FILE, "w") as f:
        json.dump(stato, f, indent=4)

# --- Core dell'Applicazione ---
class VideoAnalyzer:
    def __init__(self):
        self.cap = None
        self.video_info = {
            'path': '',
            'name': '',
            'fps': 0,
            'total_frames': 0
        }
        
    def load_video(self, path):
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise ValueError("Impossibile aprire il video")
            
        self.video_info = {
            'path': path,
            'name': os.path.splitext(os.path.basename(path))[0],
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'total_frames': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
        salva_stato(
            ultimo_video=path,
            operazione="load_video"
        )
        return self.video_info

    # ... (altri metodi della classe VideoAnalyzer)

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5
        )
        self.gesture_db = {
            'raised_hands': self._is_raised_hands,
            'heart': self._is_heart_gesture
        }
        
    # ... (altri metodi della classe GestureDetector)

class ThumbnailViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Analyzer Pro - Con Salvataggio Stato")
        self.geometry("1200x800")
        
        # Carica stato precedente
        self.stato = carica_stato()
        if self.stato:
            print(f"⚡ Riprendo da: {self.stato.get('ultima_operazione', 'Nuovo progetto')}")
        
        # Inizializza componenti
        self.analyzer = VideoAnalyzer()
        self.gesture_detector = GestureDetector()
        self.current_folder = self.stato.get("ultima_cartella", "")
        self.thumbnails = []
        self.reference_image = None
        
        # Setup UI
        self._setup_ui()
        
        # Ripristina stato se esiste
        if "ultimo_video" in self.stato:
            try:
                self.analyzer.load_video(self.stato["ultimo_video"])
                if os.path.isdir(self.current_folder):
                    self._load_thumbnails()
            except Exception as e:
                print(f"⚠️ Errore ripristino stato: {e}")

    def _setup_ui(self):
        """Configura l'interfaccia utente"""
        # ... (codice dell'interfaccia uguale al precedente)

    def _on_close(self):
        """Salva lo stato prima di chiudere"""
        salva_stato(
            ultima_cartella=self.current_folder,
            ultimo_video=self.analyzer.video_info.get('path', ''),
            ultima_operazione="Interrotto dall'utente",
            prossimi_passi="Continua analisi video"
        )
        self.destroy()

    # ... (altri metodi della classe ThumbnailViewer)

# --- Punto d'ingresso ---
if __name__ == "__main__":
    app = ThumbnailViewer()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()
