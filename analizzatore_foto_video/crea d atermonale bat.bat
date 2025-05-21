@echo off
(
echo import cv2
echo import face_recognition
echo import torch
echo from torch.cuda.amp import autocast
echo.
echo def setup_gpu():
echo     device = torch.device('cuda')
echo     torch.backends.cudnn.benchmark = True
echo     print(f"🚀 GPU attiva: {torch.cuda.get_device_name(0)}")
echo     return device
echo.
echo def main():
echo     device = setup_gpu()
echo     cap = cv2.VideoCapture(0)
echo     try:
echo         while True:
echo             ret, frame = cap.read()
echo             if not ret: break
echo             frame_tensor = torch.from_numpy(frame).to(device).permute(2,0,1).float() / 255.0
echo             rgb_tensor = frame_tensor[[2,1,0], :, :]
echo             face_locations = face_recognition.face_locations(
echo                 rgb_tensor.cpu().numpy().transpose(1,2,0), 
echo                 model="cnn"
echo             )
echo             for top, right, bottom, left in face_locations:
echo                 cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
echo             cv2.imshow('Analisi GPU - Premi Q per uscire', frame)
echo             if cv2.waitKey(1) & 0xFF == ord('q'): break
echo     finally:
echo         cap.release()
echo         cv2.destroyAllWindows()
echo         torch.cuda.empty_cache()
echo.
echo if __name__ == "__main__":
echo     main()
) > analisi_gpu.py

echo ✅ File Python creato correttamente!
python analisi_gpu.py
pause