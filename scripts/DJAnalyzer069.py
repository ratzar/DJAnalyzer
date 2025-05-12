# All'inizio del tuo DJAnalyzerXXX.py
import numpy as np
import librosa
# from scipy.stats import mode # Rimosso se non usato

class EfficientAdvancedKeyDetector: # Nome cambiato per distinguerla
    def __init__(self):
        self.major_profile = np.array([5.0, 2.0, 3.5, 2.1, 4.5, 4.0, 2.3, 4.9, 2.4, 3.7, 2.2, 3.0])
        self.minor_profile = np.array([5.0, 2.7, 3.5, 5.4, 2.5, 3.5, 2.5, 4.8, 4.0, 2.7, 3.3, 3.2])
        
        self.notes_major = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.notes_minor = ['Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm']

        self.TRAD_TO_CAMELOT_MAP = {
            'C': '8B', 'C#': '3B', 'D': '10B', 'D#': '5B', 'E': '12B', 'F': '7B',
            'F#': '2B', 'G': '9B', 'G#': '4B', 'A': '11B', 'A#': '6B', 'B': '1B',
            'Am': '8A', 'A#m': '3A', 'Bm': '10A', 'Cm': '5A', 'C#m': '12A', 'Dm': '7A',
            'D#m': '2A', 'Em': '9A', 'Fm': '4A', 'F#m': '11A', 'Gm': '6A', 'G#m': '1A'
        }

    def _extract_chroma_profile(self, y, sr):
        y_harmonic = librosa.effects.harmonic(y, margin=8)
        # Usiamo CENS come suggerito dal nuovo codice
        chroma_cens_features = librosa.feature.chroma_cens(y=y_harmonic, sr=sr)
        return np.mean(chroma_cens_features, axis=1)

    def _detect_bass_note_chroma_idx(self, y, sr):
        # Uso del CQT per il basso, come nel nuovo codice
        # Potremmo voler usare la y originale qui, non y_harmonic, per il basso
        try:
            cqt = np.abs(librosa.cqt(y, sr=sr, fmin=librosa.note_to_hz('C1'), n_bins=36, bins_per_octave=12)) # Assicura 12 bin per ottava
            bass_chroma_energy = np.zeros(12)
            for i in range(12):
                # Somma energia per ogni chroma attraverso le ottave coperte da n_bins=36 (3 ottave)
                bass_chroma_energy[i] = np.sum(cqt[i:cqt.shape[0]:12, :])
            return np.argmax(bass_chroma_energy)
        except Exception as e:
            print(f"Errore nel rilevamento nota di basso: {e}")
            return 0 # Default a C se fallisce

    def _match_key(self, chroma_profile, bass_note_idx):
        # Logica di matching "a peso" (preferibile alla forzatura)
        scores = []
        for i in range(12): # Per ogni possibile tonica (C, C#, ..., B)
            shifted_major_profile = np.roll(self.major_profile, -i)
            major_corr = np.corrcoef(chroma_profile, shifted_major_profile)[0, 1]
            
            shifted_minor_profile = np.roll(self.minor_profile, -i)
            minor_corr = np.corrcoef(chroma_profile, shifted_minor_profile)[0, 1]
            
            scores.append({'tonic_idx': i, 'type': 'major', 'score': major_corr})
            scores.append({'tonic_idx': i, 'type': 'minor', 'score': minor_corr})

        bass_weight = 0.3 
        for score_info in scores:
            tonic_idx = score_info['tonic_idx']
            key_type = score_info['type']
            
            # Se la tonica della chiave candidata (maggiore o minore) corrisponde alla nota di basso
            if tonic_idx == bass_note_idx:
                score_info['score'] += bass_weight

        best_score_info = max(scores, key=lambda x: x['score'])
        best_tonic_idx = best_score_info['tonic_idx']
        best_type = best_score_info['type']

        if best_type == 'major':
            return self.notes_major[best_tonic_idx]
        else:
            return self.notes_minor[best_tonic_idx]

    def analyze_audio_data(self, y, sr): # Ora prende y, sr come input
        try:
            chroma_profile = self._extract_chroma_profile(y, sr)
            bass_note_idx = self._detect_bass_note_chroma_idx(y, sr)
            traditional_key = self._match_key(chroma_profile, bass_note_idx)
            camelot_key = self.TRAD_TO_CAMELOT_MAP.get(traditional_key, "N/A")
            return traditional_key, camelot_key
        except Exception as e:
            print(f"Errore in EfficientAdvancedKeyDetector.analyze_audio_data: {e}")
            import traceback
            traceback.print_exc()
            return "N/A", "N/A"

# --- Integrazione in DJAnalyzerApp ---
# class DJAnalyzerApp:
#     def __init__(self, master):
#         # ...
#         self.key_detector = EfficientAdvancedKeyDetector() # Usa la nuova classe
#         # ...

#     def analyze_file_and_queue_results(self, file_path):
#         filename = os.path.basename(file_path)
#         print(f"THREAD: Caricamento {file_path}")
#         try:
#             y, sr = librosa.load(file_path, duration=60, mono=True, sr=None) # Carica UNA VOLTA
            
#             # BPM
#             tempo_array = librosa.beat.tempo(y=y, sr=sr, aggregate=None)
#             bpm = int(np.median(tempo_array))

#             # CHIAVE
#             key_str, camelot_code = self.key_detector.analyze_audio_data(y, sr) # Passa y, sr
            
#             camelot_color_name = CAMELOT_COLOR_MAP.get(camelot_code, "white")
#             compatible_keys_str = "N/A"
#             if camelot_code != "N/A":
#                 compatible_keys = self.find_compatible_keys(camelot_code)
#                 compatible_keys_str = ", ".join(compatible_keys)

#             # ENERGIA
#             scaled_energy, energy_color_name = self.analyze_energy(y, sr) # Passa y, sr

#             result_data = {
#                 "File": filename, "BPM": bpm, "Key": key_str, 
#                 "Camelot": camelot_code, "Compatibili": compatible_keys_str,
#                 "Energia": scaled_energy,
#                 "_camelot_color_tag": camelot_color_name,
#                 "_energy_color_tag": f"energy_{ENERGY_COLORS.get(scaled_energy, 'grey')}"
#             }
#             self.result_queue.put(("data", result_data))
#             # del y, sr # Opzionale, Python dovrebbe gestire la memoria
#         except Exception as e:
#             # ... gestione errore ...