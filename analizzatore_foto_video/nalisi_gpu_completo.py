# gpu_analisi_video.py
import cv2
import face_recognition
import torch
from torch.cuda.amp import autocast

def setup_gpu():
    """Configurazione ottimale per RTX 3060"""
    device = torch.device('cuda')
    torch.backends.cudnn.benchmark = True  # Ottimizza kernel CUDA
    print(f"🚀 GPU attiva: {torch.cuda.get_device_name(0)}")
    print(f"🎮 Memoria disponibile: {torch.cuda.get_device_properties(0).total_memory/1e9:.2f} GB")
    return device

def process_frame_gpu(frame, device):
    """Elaborazione frame con accelerazione GPU"""
    with autocast():  # Mixed precision
        # Converti frame per GPU (BGR -> RGB)
        frame_tensor = torch.from_numpy(frame).to(device).permute(2,0,1).float() / 255.0
        rgb_tensor = frame_tensor[[2,1,0], :, :]  # Canali RGB
        
        # Face detection (sposta su CPU per face_recognition)
        return face_recognition.face_locations(
            rgb_tensor.cpu().numpy().transpose(1,2,0), 
            model="cnn"
        )

def main():
    # 1. Setup GPU
    device = setup_gpu()
    cv2.ocl.setUseOpenCL(True)  # Abilita OpenCL per OpenCV
    
    # 2. Configurazione video
    cap = cv2.VideoCapture(0)  # Webcam
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Full HD
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Riduce latency
    
    try:
        while True:
            # 3. Lettura frame
            ret, frame = cap.read()
            if not ret: break
            
            # 4. Elaborazione GPU
            face_locations = process_frame_gpu(frame, device)
            
            # 5. Visualizzazione (CPU)
            for top, right, bottom, left in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            cv2.imshow('GPU Accelerated - Premi Q per uscire', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # 6. Pulizia risorse
        cap.release()
        cv2.destroyAllWindows()
        torch.cuda.empty_cache()
        print("✅ Risorse liberate")

if __name__ == "__main__":
    main()