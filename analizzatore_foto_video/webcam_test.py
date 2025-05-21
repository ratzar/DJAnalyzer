import cv2
import sys

try:
    # Prova ad accedere alla webcam (0 = prima webcam disponibile)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("ERRORE: Impossibile accedere alla webcam", file=sys.stderr)
        sys.exit(1)

    while True:
        # Legge il frame dalla webcam
        ret, frame = cap.read()
        if not ret:
            print("ERRORE: Impossibile leggere il frame", file=sys.stderr)
            break

        # Mostra l'immagine in una finestra
        cv2.imshow("Premi Q per chiudere", frame)
        
        # Aspetta 1 millisecondo e controlla se è stato premuto 'Q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"ERRORE: {str(e)}", file=sys.stderr)
finally:
    # Rilascia la webcam e chiude le finestre
    if 'cap' in locals():
        cap.release()
    cv2.destroyAllWindows()