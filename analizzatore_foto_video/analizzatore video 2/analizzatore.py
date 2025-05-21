import os
import cv2
import logging
from datetime import datetime
import numpy as np
import mediapipe as mp
from collections import defaultdict

# Configurazione del logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/error_log.txt',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class VideoAnalyzer:
    def __init__(self):
        self.cap = None
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5
        )
        self.gestures_db = {
            'raised_hands': self._is_raised_hands,
            'heart': self._is_heart_gesture
        }

    def _is_raised_hands(self, landmarks):
        y_coords = [landmark.y for landmark in landmarks.landmark]
        return (max(y_coords) - min(y_coords)) > 0.3

    def _is_heart_gesture(self, landmarks):
        # Implementa la tua logica per il gesto a cuore
        return False

    def analyze_video(self, video_path, output_dir):
        """Analizza video: cambi scena, campionamento frame e rilevamento gesti"""
        try:
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                raise ValueError(f"Impossibile aprire il video: {video_path}")

            fps = self.cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logging.info(f"Inizio analisi: {video_path}")
            print(f"▶ Analisi iniziata (Frames: {total_frames}, FPS: {fps:.1f})")

            scene_changes = self._detect_scenes(output_dir, fps)
            sampled_frames = self._sample_frames(output_dir, fps)
            gestures = self._detect_gestures(output_dir)

            return {
                'scene_changes': len(scene_changes),
                'sampled_frames': len(sampled_frames),
                'gestures_detected': gestures
            }

        except Exception as e:
            logging.error(f"Errore durante l'analisi: {str(e)}", exc_info=True)
            raise
        finally:
            if self.cap:
                self.cap.release()

    def _detect_scenes(self, output_dir, fps, threshold=0.3):
        """Rileva cambi scena usando la differenza tra istogrammi"""
        scene_changes = []
        ret, prev_frame = self.cap.read()
        prev_hist = cv2.calcHist([prev_frame], [0], None, [256], [0,256])
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            curr_hist = cv2.calcHist([frame], [0], None, [256], [0,256])
            similarity = cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_CORREL)

            if similarity < threshold:
                frame_num = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                timestamp = frame_num / fps
                h,m,s = self._convert_timestamp(timestamp)
                filename = f"scene_{h:02d}h{m:02d}m{s:02d}s.jpg"
                cv2.imwrite(os.path.join(output_dir, filename), frame)
                scene_changes.append((frame_num, timestamp, filename))

            prev_hist = curr_hist

        return scene_changes

    def _sample_frames(self, output_dir, fps, interval_sec=5):
        """Campiona frame a intervalli regolari"""
        sampled_frames = []
        interval_frames = int(fps * interval_sec)

        for frame_num in range(0, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)), interval_frames):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            if ret:
                timestamp = frame_num / fps
                h,m,s = self._convert_timestamp(timestamp)
                filename = f"sample_{h:02d}h{m:02d}m{s:02d}s.jpg"
                cv2.imwrite(os.path.join(output_dir, filename), frame)
                sampled_frames.append((frame_num, timestamp, filename))

        return sampled_frames

    def _detect_gestures(self, output_dir):
        """Analizza frame per rilevare gesti specifici"""
        gestures_found = defaultdict(int)
        
        for file in os.listdir(output_dir):
            if file.endswith(('.jpg', '.png')):
                try:
                    img = cv2.imread(os.path.join(output_dir, file))
                    results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    
                    if results.multi_hand_landmarks:
                        for landmarks in results.multi_hand_landmarks:
                            for gesture_name, check in self.gestures_db.items():
                                if check(landmarks):
                                    gestures_found[gesture_name] += 1
                except Exception as e:
                    logging.warning(f"Errore analisi gesti in {file}: {str(e)}")

        return dict(gestures_found)

    def _convert_timestamp(self, seconds):
        """Converti secondi in ore, minuti, secondi"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return int(h), int(m), int(s)

def main():
    print("=== ANALIZZATORE VIDEO ===")
    video_path = input("Percorso video: ").strip('"')
    output_dir = input("Cartella output (creata se non esiste): ").strip('"')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    analyzer = VideoAnalyzer()
    
    try:
        results = analyzer.analyze_video(video_path, output_dir)
        print("\n✅ Analisi completata!")
        print(f"- Cambi scena rilevati: {results['scene_changes']}")
        print(f"- Frame campionati salvati: {results['sampled_frames']}")
        print(f"- Gesti riconosciuti: {results['gestures_detected'] or 'Nessuno'}")
        
    except Exception as e:
        print(f"\n❌ Errore durante l'analisi: {str(e)}")
        print("Controlla logs/error_log.txt per dettagli")
    finally:
        input("\nPremi INVIO per uscire...")

if __name__ == "__main__":
    main()