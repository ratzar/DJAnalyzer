import os
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import torch
from torchvision import models, transforms
import mediapipe as mp
import face_recognition
from sklearn.neighbors import NearestNeighbors

# Configurazione modelli AI
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Modello per analisi scene
scene_model = models.resnet50(pretrained=True).to(device).eval()
scene_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Modello per estrazione features
feature_extractor = torch.nn.Sequential(*(list(scene_model.children())[:-1])).to(device).eval()

# Inizializzazione MediaPipe per rilevamento mani
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2)

class VideoAnalyzer:
    def __init__(self):
        self.video_path = ""
        self.output_dir = ""
        self.video_name = ""
        self.scene_threshold = 0.3
        self.time_interval = 5  # percentuale
    
    def load_video(self, path):
        self.video_path = path
        self.video_name = os.path.splitext(os.path.basename(path))[0]
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
    def detect_scene_changes(self):
        """Rileva cambi scena e salva fotogrammi chiave"""
        ret, prev_frame = self.cap.read()
        prev_hist = cv2.calcHist([prev_frame], [0], None, [256], [0, 256])
        scene_changes = []
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            curr_hist = cv2.calcHist([frame], [0], None, [256], [0, 256])
            similarity = cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_CORREL)
            
            if similarity < self.scene_threshold:
                frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                timestamp = frame_number / self.fps
                scene_changes.append((frame_number, timestamp))
                self.save_keyframe(frame, timestamp)
            
            prev_hist = curr_hist
        
        return scene_changes
    
    def save_keyframe(self, frame, timestamp):
        """Salva un fotogramma chiave"""
        h, m, s = self.convert_timestamp(timestamp)
        filename = f"{self.video_name}_{h:02d}-{m:02d}-{s:02d}.jpg"
        path = os.path.join(self.output_dir, filename)
        cv2.imwrite(path, frame)
        return path
    
    def sample_frames(self):
        """Campiona fotogrammi a intervalli regolari"""
        interval_frames = int(self.total_frames * (self.time_interval / 100))
        sampled_frames = []
        
        for frame_num in range(0, self.total_frames, interval_frames):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            if ret:
                timestamp = frame_num / self.fps
                path = self.save_keyframe(frame, timestamp)
                sampled_frames.append((frame_num, timestamp, path))
        
        return sampled_frames
    
    def convert_timestamp(self, seconds):
        """Converte secondi in ore, minuti, secondi"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return int(h), int(m), int(s)

class AIAnalyzer:
    @staticmethod
    def analyze_scene(image_path):
        """Analizza una scena con modello ResNet"""
        img = Image.open(image_path)
        img_t = scene_transforms(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            output = scene_model(img_t)
        
        # Decodifica risultati (semplificato)
        _, preds = torch.max(output, 1)
        return preds.item()
    
    @staticmethod
    def detect_gestures(image_path):
        """Rileva gesti con MediaPipe"""
        img = cv2.imread(image_path)
        results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        gestures = []
        if results.multi_hand_landmarks:
            for landmarks in results.multi_hand_landmarks:
                # Analisi semplificata per esempio
                y_coords = [landmark.y for landmark in landmarks.landmark]
                if max(y_coords) - min(y_coords) > 0.3:
                    gestures.append("raised_hands")
                # Aggiungere altri gesti qui
                
        return gestures
    
    @staticmethod
    def extract_features(image_path):
        """Estrae features per ricerca similarità"""
        img = Image.open(image_path)
        img_t = scene_transforms(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            features = feature_extractor(img_t)
        
        return features.cpu().numpy().flatten()
    
    @staticmethod
    def find_similar(reference_path, target_paths, top_k=5):
        """Trova immagini simili"""
        ref_feat = AIAnalyzer.extract_features(reference_path)
        target_feats = [AIAnalyzer.extract_features(p) for p in target_paths]
        
        nbrs = NearestNeighbors(n_neighbors=top_k, algorithm='ball_tree').fit(target_feats)
        distances, indices = nbrs.kneighbors([ref_feat])
        
        return [(target_paths[i], d) for i, d in zip(indices[0], distances[0])]
    
    @staticmethod
    def find_faces(image_path, reference_encodings, threshold=0.6):
        """Trova volti corrispondenti"""
        img = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(img)
        
        for enc in encodings:
            matches = face_recognition.compare_faces(reference_encodings, enc, threshold)
            if any(matches):
                return True
        return False

class ThumbnailViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Analyzer Pro")
        self.geometry("1200x800")
        
        # Variabili di stato
        self.video_analyzer = VideoAnalyzer()
        self.current_folder = ""
        self.thumbnails = []
        self.reference_face = None
        
        # Setup interfaccia
        self.setup_ui()
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame superiore (controlli)
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Pulsanti analisi video
        ttk.Button(control_frame, text="Carica Video", command=self.load_video).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Analizza Scene", command=self.analyze_scenes).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Campiona Fotogrammi", command=self.sample_frames).pack(side=tk.LEFT)
        
        # Pulsanti AI
        ai_frame = ttk.Frame(self)
        ai_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ai_frame, text="Cerca Gesti", command=self.search_gestures).pack(side=tk.LEFT)
        ttk.Button(ai_frame, text="Carica Volto Ref", command=self.load_reference_face).pack(side=tk.LEFT)
        ttk.Button(ai_frame, text="Cerca Volti", command=self.search_faces).pack(side=tk.LEFT)
        ttk.Button(ai_frame, text="Cerca Simili", command=self.search_similar).pack(side=tk.LEFT)
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas per miniature con scrollbar
        self.canvas = tk.Canvas(main_frame)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Frame anteprima
        self.preview_frame = ttk.Frame(self)
    
    def load_video(self):
        """Carica un file video"""
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if path:
            self.video_analyzer.load_video(path)
            output_dir = filedialog.askdirectory(title="Seleziona cartella output")
            if output_dir:
                self.video_analyzer.output_dir = output_dir
                self.current_folder = output_dir
                self.show_message(f"Video caricato: {os.path.basename(path)}")
    
    def analyze_scenes(self):
        """Avvia l'analisi dei cambi scena"""
        if not self.video_analyzer.video_path:
            self.show_message("Prima carica un video!")
            return
            
        scene_changes = self.video_analyzer.detect_scene_changes()
        self.show_message(f"Trovati {len(scene_changes)} cambi scena")
        self.load_thumbnails()
    
    def sample_frames(self):
        """Campiona fotogrammi a intervalli regolari"""
        if not self.video_analyzer.video_path:
            self.show_message("Prima carica un video!")
            return
            
        interval = simpledialog.askinteger("Intervallo", "Inserisci intervallo (%):", 
                                         initialvalue=self.video_analyzer.time_interval)
        if interval:
            self.video_analyzer.time_interval = interval
            sampled = self.video_analyzer.sample_frames()
            self.show_message(f"Salvati {len(sampled)} fotogrammi campionati")
            self.load_thumbnails()
    
    def load_thumbnails(self):
        """Carica le miniature dalla cartella output"""
        if not self.current_folder:
            return
            
        # Pulisci frame esistente
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.thumbnails = []
        valid_exts = ('.jpg', '.jpeg', '.png')
        
        # Carica immagini
        row, col = 0, 0
        max_cols = 5
        
        for file in sorted(os.listdir(self.current_folder)):
            if file.lower().endswith(valid_exts):
                try:
                    path = os.path.join(self.current_folder, file)
                    img = Image.open(path)
                    img.thumbnail((200, 200))
                    
                    photo = ImageTk.PhotoImage(img)
                    self.thumbnails.append((file, photo, path))
                    
                    # Crea elemento griglia
                    frame = ttk.Frame(self.scrollable_frame)
                    frame.grid(row=row, column=col, padx=5, pady=5)
                    
                    label = ttk.Label(frame, image=photo)
                    label.image = photo
                    label.pack()
                    
                    short_name = file[:20] + "..." if len(file) > 20 else file
                    ttk.Label(frame, text=short_name, wraplength=180).pack()
                    
                    label.bind("<Button-1>", lambda e, p=path: self.show_preview(p))
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                        
                except Exception as e:
                    print(f"Errore caricamento {file}: {e}")
    
    def show_preview(self, image_path):
        """Mostra anteprima a dimensione intera"""
        # Implementazione simile all'esempio precedente
        pass
    
    def search_gestures(self):
        """Cerca gesti nelle immagini selezionate"""
        selected = self.get_selected_thumbnails()
        if not selected:
            self.show_message("Seleziona prima delle miniature!")
            return
            
        for path in selected:
            gestures = AIAnalyzer.detect_gestures(path)
            if gestures:
                self.show_message(f"Gesti trovati in {os.path.basename(path)}: {', '.join(gestures)}")
    
    def load_reference_face(self):
        """Carica un volto di riferimento"""
        path = filedialog.askopenfilename(filetypes=[("Immagini", "*.jpg *.jpeg *.png")])
        if path:
            ref_image = face_recognition.load_image_file(path)
            self.reference_face = face_recognition.face_encodings(ref_image)
            self.show_message("Volto di riferimento caricato!")
    
    def search_faces(self):
        """Cerca il volto di riferimento"""
        if not self.reference_face:
            self.show_message("Prima carica un volto di riferimento!")
            return
            
        selected = self.get_selected_thumbnails()
        if not selected:
            self.show_message("Seleziona prima delle miniature!")
            return
            
        for path in selected:
            if AIAnalyzer.find_faces(path, self.reference_face):
                self.show_message(f"Volto trovato in {os.path.basename(path)}")
    
    def search_similar(self):
        """Cerca immagini simili"""
        path = filedialog.askopenfilename(filetypes=[("Immagini", "*.jpg *.jpeg *.png")])
        if not path:
            return
            
        all_images = [t[2] for t in self.thumbnails]
        similar = AIAnalyzer.find_similar(path, all_images)
        
        # Mostra risultati
        result_window = tk.Toplevel(self)
        result_window.title("Risultati ricerca similarità")
        
        for i, (img_path, distance) in enumerate(similar[:5]):
            img = Image.open(img_path)
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)
            
            frame = ttk.Frame(result_window)
            frame.pack(padx=5, pady=5)
            
            label = ttk.Label(frame, image=photo)
            label.image = photo
            label.pack(side=tk.LEFT)
            
            info = f"{os.path.basename(img_path)}\nDistanza: {distance:.2f}"
            ttk.Label(frame, text=info).pack(side=tk.LEFT, padx=10)
    
    def get_selected_thumbnails(self):
        """Restituisce i percorsi delle miniature selezionate"""
        # Implementazione base (può essere estesa per selezione multipla)
        return [t[2] for t in self.thumbnails]  # Per ora tutte
    
    def show_message(self, text):
        """Mostra un messaggio all'utente"""
        messagebox.showinfo("Info", text)

if __name__ == "__main__":
    app = ThumbnailViewer()
    app.mainloop()