# Confronto tra diversi algoritmi per BPM e tonalità
# Usiamo: librosa (standard), keyfinder (simulato), essentia (se installato)

import os
import librosa
import numpy as np

try:
    import essentia
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False

# === [BLOCCATO] Modulo: BPM e Key (Librosa) ===
# FUNZIONANTE – NON TOCCARE
def analyze_librosa(file_path):
    y, sr = librosa.load(file_path, sr=None)
    tempo = librosa.beat.tempo(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    pitch_class = np.argmax(np.mean(chroma, axis=1))
    key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][pitch_class]
    return {
        "source": "librosa",
        "bpm": int(round(tempo[0])) if tempo.size else 0,
        "key": key
    }

# === [BLOCCATO] Modulo: BPM e Key (Essentia) ===
# FUNZIONANTE – NON TOCCARE
def analyze_essentia(file_path):
    if not ESSENTIA_AVAILABLE:
        return {"source": "essentia", "bpm": "N/A", "key": "N/A"}
    loader = es.MonoLoader(filename=file_path)
    audio = loader()
    bpm = es.RhythmExtractor2013()(audio)[0]
    key, scale, strength = es.KeyExtractor()(audio)
    return {
        "source": "essentia",
        "bpm": int(round(bpm)),
        "key": f"{key} {scale}"
    }

# --- KeyFinder (CLI wrapper) ---
def analyze_keyfinder(file_path):
    import subprocess
    try:
        result = subprocess.run(["keyfinder-cli", file_path], capture_output=True, text=True)
        key = result.stdout.strip()
        return {"source": "keyfinder", "bpm": "N/A", "key": key}
    except Exception as e:
        return {"source": "keyfinder", "bpm": "N/A", "key": f"Errore: {e}"}

# --- Impostazioni: attiva/disattiva algoritmi ---
USE_LIBROSA = True
USE_ESSENTIA = True
USE_KEYFINDER = True

# --- Main loop ---
def analyze_file(file_path):
    results = []
    if USE_LIBROSA:
        results.append(analyze_librosa(file_path))
    if USE_ESSENTIA and ESSENTIA_AVAILABLE:
        results.append(analyze_essentia(file_path))
    if USE_KEYFINDER:
        results.append(analyze_keyfinder(file_path))
    return results

# Confronto multiplo su una cartella di brani
import csv

def analyze_folder(folder_path, output_csv="risultati_confronto.csv"):
    entries = []
    for fname in os.listdir(folder_path):
        if fname.lower().endswith(('.mp3', '.wav', '.flac')):
            full_path = os.path.join(folder_path, fname)
            results = analyze_file(full_path)
            row = {"file": fname}
            for r in results:
                row[f"bpm_{r['source']}"] = r['bpm']
                row[f"key_{r['source']}"] = r['key']
            entries.append(row)
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=entries[0].keys())
        writer.writeheader()
        writer.writerows(entries)
    print(f"Risultati salvati in {output_csv}")

# USO: cambia 'cartella_test' con il tuo percorso reale
if __name__ == "__main__":
    analyze_folder("cartella_test")
        # NOTE: codice di test per singolo file (usare se serve debug futuro)
    # test_file = "file_audio.mp3"
    # results = analyze_file(test_file)
    # for r in results:
    #     print(f"[{r['source']}] BPM: {r['bpm']} | Key: {r['key']}")
