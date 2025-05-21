import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import mediapipe as mp
from collections import defaultdict

# 1. SISTEMA DI SALVATAGGIO AUTOMATICO
STATO_FILE = "stato_progetto.json"

def carica_stato():
    """Carica lo stato da file JSON"""
    if os.path.exists(STATO_FILE):
        try:
            with open(STATO_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salva_stato(**kwargs):
    """Salva lo stato corrente"""
    stato = carica_stato()
    stato.update(kwargs)
    with open(STATO_FILE, "w") as f:
        json.dump(stato, f, indent=4)

# 2. ANALISI VIDEO (TUTTE LE FUNZIONI ORIGINALI)
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
        """Carica video con controlli di errore"""
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise ValueError(f"Impossibile aprire il video: {path}")
        
        self.video_info = {
            'path': path,
            'name': os.path.splitext(os.path.basename(path))[0],
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'total_frames': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
        salva_stato(ultimo_video=path)
        return self.video_info

    def detect_scene_changes(self, output_dir, threshold=0.3):
        """Rileva cambi scena con istogrammi"""
        scene_changes = []
        ret, prev_frame = self.cap.read()
        prev_hist = cv2.calcHist([prev_frame], [0], None, [256], [0, 256])
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            curr_hist = cv2.calcHist([frame], [0], None, [256], [0, 256])
            similarity = cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_CORREL)
            
            if similarity < threshold:
                frame_num = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                timestamp = frame_num / self.video_info['fps']
                h, m, s = self._convert_timestamp(timestamp)
                filename = f"{self.video_info['name']}_{h:02d}-{m:02d}-{s:02d}.jpg"
                cv2.imwrite(os.path.join(output_dir, filename), frame)
                scene_changes.append((frame_num, timestamp, filename))
            
            prev_hist = curr_hist
        
        salva_stato(ultima_analisi_scene=len(scene_changes))
        return scene_changes

    def sample_frames(self, output_dir, interval_percent=5):
        """Campiona frame a intervalli regolari"""
        interval_frames = int(self.video_info['total_frames'] * (interval_percent / 100))
        sampled_frames = []
        
        for frame_num in range(0, self.video_info['total_frames'], interval_frames):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            if ret:
                timestamp = frame_num / self.video_info['fps']
                h, m, s = self._convert_timestamp(timestamp)
                filename = f"{self.video_info['name']}_sample_{h:02d}-{m:02d}-{s:02d}.jpg"
                cv2.imwrite(os.path.join(output_dir, filename), frame)
                sampled_frames.append((frame_num, timestamp, filename))
        
        salva_stato(ultimo_campionamento=len(sampled_frames))
        return sampled_frames

    def _convert_timestamp(self, seconds):
        """Formatta ore, minuti, secondi"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return int(h), int(m), int(s)

# 3. ANALISI IMMAGINI (GESTI + VOLTI)
class ImageAnalyzer:
    def __init__(self):
        # Inizializza modelli MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5
        )
        
        self.mp_face = mp.solutions.face_detection
        self.face_detector = self.mp_face.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.5
        )
        
        # Database gesti personalizzabile
        self.gesture_db = {
            'raised_hands': self._is_raised_hands,
            'heart': self._is_heart_gesture
        }
    
    def detect_gestures(self, image_path):
        """Rileva gesti dalle immagini"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossibile leggere l'immagine: {image_path}")
            
        results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        detected = []
        
        if results.multi_hand_landmarks:
            for landmarks in results.multi_hand_landmarks:
                for name, check in self.gesture_db.items():
                    if check(landmarks):
                        detected.append(name)
        
        return list(set(detected))
    
    def detect_faces(self, image_path):
        """Conta i volti nell'immagine"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossibile leggere l'immagine: {image_path}")
            
        results = self.face_detector.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return len(results.detections) if results.detections else 0
    
    # Logica per i gesti
    def _is_raised_hands(self, landmarks):
        y_coords = [landmark.y for landmark in landmarks.landmark]
        return (max(y_coords) - min(y_coords)) > 0.3
        
    def _is_heart_gesture(self, landmarks):
        # Implementa la tua logica per il gesto a cuore
        return False

# 4. INTERFACCIA GRAFICA COMPLETA
class VideoAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizzatore Video/Foto Pro")
        self.geometry("1200x800")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Carica stato precedente
        self.stato = carica_stato()
        
        # Inizializza analizzatori
        self.video_analyzer = VideoAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        self.current_folder = self.stato.get("ultima_cartella", "")
        self.thumbnails = []
        
        # Setup UI
        self._setup_ui()
        
        # Ripristina sessione
        self._restore_session()
    
    def _setup_ui(self):
        """Configura l'interfaccia utente"""
        # Pannello controlli
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Pulsanti video
        ttk.Button(control_frame, text="📁 Carica Video", 
                  command=self._load_video).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="🎬 Analizza Scene", 
                  command=self._analyze_scenes).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏱ Campiona Frame", 
                  command=self._sample_frames).pack(side=tk.LEFT)
        
        # Pulsanti analisi
        analysis_frame = ttk.Frame(self)
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(analysis_frame, text="👐 Cerca Gesti", 
                  command=self._search_gestures).pack(side=tk.LEFT)
        ttk.Button(analysis_frame, text="👤 Cerca Volti", 
                  command=self._search_faces).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_frame, text="🔍 Cerca Simili", 
                  command=self._search_similar).pack(side=tk.LEFT)
        
        # Area visualizzazione
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind("<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
    
    def _restore_session(self):
        """Ripristina l'ultima sessione"""
        if "ultimo_video" in self.stato:
            try:
                self.video_analyzer.load_video(self.stato["ultimo_video"])
                if os.path.isdir(self.current_folder):
                    self._load_thumbnails()
                messagebox.showinfo("Stato Ripristinato", 
                    f"Ripresa analisi video: {os.path.basename(self.stato['ultimo_video'])}")
            except Exception as e:
                messagebox.showerror("Errore Ripristino", str(e))
    
    def _load_video(self):
        """Carica un nuovo video"""
        path = filedialog.askopenfilename(filetypes=[
            ("Video", "*.mp4 *.avi *.mov *.mkv")
        ])
        
        if path:
            try:
                self.video_analyzer.load_video(path)
                output_dir = filedialog.askdirectory(title="Seleziona cartella output")
                if output_dir:
                    self.current_folder = output_dir
                    salva_stato(ultima_cartella=output_dir)
                    messagebox.showinfo("Successo", 
                        f"Video caricato: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Errore", str(e))
    
    def _analyze_scenes(self):
        """Avvia analisi cambi scena"""
        if not self._check_ready():
            return
            
        try:
            scenes = self.video_analyzer.detect_scene_changes(self.current_folder)
            self._load_thumbnails()
            messagebox.showinfo("Completato", 
                f"Trovati {len(scenes)} cambi scena. Frame salvati in:\n{self.current_folder}")
        except Exception as e:
            messagebox.showerror("Errore Analisi", str(e))
    
    def _sample_frames(self):
        """Campiona frame a intervalli"""
        if not self._check_ready():
            return
            
        interval = simpledialog.askinteger(
            "Intervallo Campionamento", 
            "Inserisci intervallo (% durata video):",
            initialvalue=5
        )
        
        if interval:
            try:
                samples = self.video_analyzer.sample_frames(self.current_folder, interval)
                self._load_thumbnails()
                messagebox.showinfo("Completato", 
                    f"Salvati {len(samples)} frame campione")
            except Exception as e:
                messagebox.showerror("Errore Campionamento", str(e))
    
    def _search_gestures(self):
        """Cerca gesti nelle immagini"""
        if not self._check_thumbnails():
            return
            
        results = defaultdict(list)
        
        for file, _, path in self.thumbnails:
            try:
                gestures = self.image_analyzer.detect_gestures(path)
                for gesture in gestures:
                    results[gesture].append(file)
            except Exception as e:
                print(f"Errore analisi {file}: {e}")
                
        if not results:
            messagebox.showinfo("Risultati", "Nessun gesto riconosciuto")
        else:
            result_text = "\n".join(
                f"{gesture}: {len(files)} immagini" 
                for gesture, files in results.items()
            )
            messagebox.showinfo("Gesti Riconosciuti", result_text)
    
    def _search_faces(self):
        """Conta i volti nelle immagini"""
        if not self._check_thumbnails():
            return
            
        total_faces = 0
        for file, _, path in self.thumbnails:
            try:
                total_faces += self.image_analyzer.detect_faces(path)
            except Exception as e:
                print(f"Errore analisi {file}: {e}")
        
        messagebox.showinfo("Risultati Volti", 
            f"Trovati {total_faces} volti nel totale delle immagini")
    
    def _search_similar(self):
        """Cerca immagini simili (template matching)"""
        if not self._check_thumbnails():
            return
            
        query_path = filedialog.askopenfilename(
            title="Seleziona immagine di riferimento",
            filetypes=[("Immagini", "*.jpg *.jpeg *.png")]
        )
        
        if not query_path:
            return
            
        try:
            query_img = cv2.imread(query_path, cv2.IMREAD_GRAYSCALE)
            if query_img is None:
                raise ValueError("Impossibile leggere l'immagine di riferimento")
            
            matches = []
            threshold = 0.8  # Soglia di similarità
            
            for file, _, path in self.thumbnails:
                target_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                res = cv2.matchTemplate(query_img, target_img, cv2.TM_CCOEFF_NORMED)
                if np.max(res) >= threshold:
                    matches.append(file)
            
            if not matches:
                messagebox.showinfo("Risultati", "Nessuna corrispondenza trovata")
            else:
                messagebox.showinfo("Immagini Simili", 
                    f"Trovate {len(matches)} corrispondenze:\n- " + "\n- ".join(matches))
        except Exception as e:
            messagebox.showerror("Errore Ricerca", str(e))
    
    def _load_thumbnails(self):
        """Carica miniature nella griglia"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.thumbnails = []
        
        if not os.path.isdir(self.current_folder):
            return
            
        row, col = 0, 0
        max_cols = 5
        
        for file in sorted(os.listdir(self.current_folder)):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    path = os.path.join(self.current_folder, file)
                    img = Image.open(path)
                    img.thumbnail((200, 200))
                    
                    photo = ImageTk.PhotoImage(img)
                    self.thumbnails.append((file, photo, path))
                    
                    frame = ttk.Frame(self.scrollable_frame)
                    frame.grid(row=row, column=col, padx=5, pady=5)
                    
                    label = ttk.Label(frame, image=photo)
                    label.image = photo
                    label.pack()
                    
                    ttk.Label(frame, text=file[:15] + ('...' if len(file) > 15 else '')).pack()
                    
                    label.bind("<Button-1>", lambda e, p=path: self._show_preview(p))
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                except Exception as e:
                    print(f"Errore caricamento {file}: {e}")
    
    def _show_preview(self, image_path):
        """Mostra anteprima a dimensione intera"""
        preview = tk.Toplevel(self)
        preview.title("Anteprima")
        
        try:
            img = Image.open(image_path)
            img.thumbnail((800, 600))
            photo = ImageTk.PhotoImage(img)
            
            ttk.Label(preview, image=photo).pack()
            ttk.Label(preview, text=os.path.basename(image_path)).pack()
        except Exception as e:
            messagebox.showerror("Errore Anteprima", str(e))
    
    def _check_ready(self):
        """Verifica se il video è caricato"""
        if not self.video_analyzer.cap:
            messagebox.showwarning("Attenzione", "Carica prima un video!")
            return False
        if not self.current_folder:
            messagebox.showwarning("Attenzione", "Seleziona una cartella di output!")
            return False
        return True
    
    def _check_thumbnails(self):
        """Verifica se ci sono miniature da analizzare"""
        if not self.thumbnails:
            messagebox.showwarning("Attenzione", "Nessuna immagine da analizzare!")
            return False
        return True
    
    def _on_close(self):
        """Salva lo stato prima di chiudere"""
        salva_stato(
            ultima_operazione="Chiusura manuale",
            timestamp=datetime.now().isoformat()
        )
        self.destroy()

if __name__ == "__main__":
    app = VideoAnalyzerApp()
    app.mainloop()