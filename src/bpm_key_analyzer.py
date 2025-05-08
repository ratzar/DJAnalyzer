import os
import librosa
import csv
import json

def analyze_audio(file_path):
    """
    Analizza un file audio per determinare il BPM e la tonalità.
    
    :param file_path: Percorso del file audio da analizzare.
    :return: Un dizionario contenente BPM e tonalità.
    """
    try:
        # Carica il file audio con librosa
        y, sr = librosa.load(file_path)

        # Calcola il BPM
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

        # Calcola la tonalità (key) usando librosa
        chroma = librosa.feature.chroma_cens(y=y, sr=sr)
        key = librosa.key.key(chroma)

        return {"file": os.path.basename(file_path), "bpm": tempo, "key": key}

    except Exception as e:
        print(f"Errore nell'analisi del file {file_path}: {e}")
        return None

def analyze_directory(directory_path):
    """
    Analizza tutti i file audio in una cartella specificata.

    :param directory_path: Percorso della cartella contenente i file audio.
    :return: Una lista di dizionari contenenti i dettagli di BPM e tonalità per ogni brano.
    """
    results = []
    for filename in os.listdir(directory_path):
        if filename.endswith(('.mp3', '.wav')):
            file_path = os.path.join(directory_path, filename)
            result = analyze_audio(file_path)
            if result:
                results.append(result)
    return results

def save_results_to_csv(results, output_file):
    """
    Salva i risultati dell'analisi in un file CSV.

    :param results: Lista di dizionari con i risultati dell'analisi.
    :param output_file: Percorso del file CSV in cui salvare i risultati.
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['file', 'bpm', 'key']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        print(f"Risultati salvati in {output_file}")
    except Exception as e:
        print(f"Errore durante il salvataggio dei risultati: {e}")

def save_results_to_json(results, output_file):
    """
    Salva i risultati dell'analisi in un file JSON.

    :param results: Lista di dizionari con i risultati dell'analisi.
    :param output_file: Percorso del file JSON in cui salvare i risultati.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(results, jsonfile, ensure_ascii=False, indent=4)
        print(f"Risultati salvati in {output_file}")
    except Exception as e:
        print(f"Errore durante il salvataggio dei risultati: {e}")

if __name__ == "__main__":
    # Modifica il percorso della cartella contenente i file audio
    audio_directory = "D:/musica"  # Modifica con il percorso corretto
    output_csv = "output.csv"      # Modifica con il nome del file di output CSV
    output_json = "output.json"    # Modifica con il nome del file di output JSON

    # Analizza la cartella e salva i risultati in CSV e JSON
    results = analyze_directory(audio_directory)
    save_results_to_csv(results, output_csv)
    save_results_to_json(results, output_json)
