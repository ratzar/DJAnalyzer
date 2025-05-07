import numpy as np
import librosa

# Mappa degli indici di pitch class a nomi di chiavi
KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F',
        'F#', 'G', 'G#', 'A', 'A#', 'B']

class HarmonicAnalyzer:
    """
    Rileva la chiave armonica basandosi su chroma features.
    """

    def rileva_chiave(self, path: str) -> str:
        # Carica file (campionamento originale)
        y, sr = librosa.load(path, sr=None, mono=True)

        # Estrai Chroma (costante-Q)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        # Somma energia per ciascuna pitch class
        chroma_sum = np.mean(chroma, axis=1)
        # Chiave come indice del massimo
        key_idx = int(np.argmax(chroma_sum))
        return KEYS[key_idx]

# funzione di comodo per import diretto
def rileva_chiave(path: str) -> str:
    return HarmonicAnalyzer().rileva_chiave(path)
