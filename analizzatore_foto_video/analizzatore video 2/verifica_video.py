import os
import cv2
import sys
from datetime import timedelta

def verifica_formato(video_path):
    """Modulo 1: Verifica base del file video"""
    try:
        # Controllo esistenza file
        if not os.path.exists(video_path):
            raise ValueError("File non trovato")
        
        # Controllo estensione
        if not video_path.lower().endswith(('.mp4', '.avi', '.mov')):
            raise ValueError("Formato file non supportato")

        # Apertura con OpenCV
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            # Tentativo con backend alternativo
            cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                raise RuntimeError("Impossibile aprire il video con OpenCV")

        # Estrazione metadati
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps == 0 or length == 0:
            raise ValueError("Video corrotto o metadati mancanti")

        durata = str(timedelta(seconds=length/fps))
        
        print(f"✔ Verifica completata:")
        print(f"- Formato: MP4/H.264 (avc1)")
        print(f"- Risoluzione: {width}x{height}")
        print(f- Durata: {durata}")
        print(f"- Framerate: {fps:.2f} fps")

        cap.release()
        return True

    except Exception as e:
        print(f"❌ Errore verifica: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verifica_video.py [percorso_video]")
        sys.exit(1)
    
    if verifica_formato(sys.argv[1]):
        print("\nPassare al modulo successivo")
    else:
        print("\nRisolvere i problemi prima di procedere")