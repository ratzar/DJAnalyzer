@echo off
:: Verifica che lo script esista
if not exist "analisi_gpu_completo.py" (
    echo Creo lo script analisi...
    (
    echo import cv2
    echo import face_recognition
    echo import torch
    echo from torch.cuda.amp import autocast
    echo. 
    echo def setup_gpu():
    echo     device = torch.device('cuda')
    echo     torch.backends.cudnn.benchmark = True
    echo     print(f"GPU: {torch.cuda.get_device_name(0)}")
    echo     return device
    echo.
    echo def main():
    echo     device = setup_gpu()
    echo     cap = cv2.VideoCapture(0)
    echo     while True:
    echo         ret, frame = cap.read()
    echo         if not ret: break
    echo         cv2.imshow('Premi Q per uscire', frame)
    echo         if cv2.waitKey(1) ^& 