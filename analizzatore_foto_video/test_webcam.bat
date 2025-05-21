@echo off
echo import cv2 > test.py
echo cap = cv2.VideoCapture(0) >> test.py
echo while True: >> test.py
echo     ret, frame = cap.read() >> test.py
echo     cv2.imshow('Test', frame) >> test.py
echo     if cv2.waitKey(1) & 0xFF == ord('q'): break >> test.py
echo cap.release() >> test.py
echo cv2.destroyAllWindows() >> test.py
python test.py
pause