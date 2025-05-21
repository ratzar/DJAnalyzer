@echo off
(
echo import cv2
echo import sys
echo.
echo try:
echo     cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
echo     if not cap.isOpened():
echo         print("ERRORE: Webcam non accessibile", file=sys.stderr)
echo         sys.exit(1)
echo.
echo     while True:
echo         ret, frame = cap.read()
echo         if not ret:
echo             print("ERRORE: Frame non letto", file=sys.stderr)
echo             break
echo.
echo         cv2.imshow("Premi Q per chiudere", frame)
echo         if cv2.waitKey(1) & 0xFF == ord('q'):
echo             break
echo.
echo except Exception as e:
echo     print(f"ERRORE: {str(e)}", file=sys.stderr)
echo finally:
echo     if 'cap' in locals():
echo         cap.release()
echo     cv2.destroyAllWindows()
) > webcam_test.py

python webcam_test.py
pause