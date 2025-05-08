import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QSlider, QPushButton, 
                           QFrame, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QFont, QLinearGradient
import librosa
import sounddevice as sd
import rtmidi
import os
from collections import deque

# ====================== [CORE ENGINE] ======================
class AudioMixer:
    def __init__(self):
        self.sample_rate = 44100
        self.buffer_size = 1024
        self.stream = None
        self.decks = {
            'A': {'audio': None, 'pos': 0, 'vol': 0.8, 'playing': False, 'pitch': 1.0},
            'B': {'audio': None, 'pos': 0, 'vol': 0.8, 'playing': False, 'pitch': 1.0}
        }
        self.crossfader = 0.5
        self.master_vol = 0.8
        
    def start(self):
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.buffer_size,
            channels=2,
            dtype='float32',
            callback=self._audio_callback
        )
        self.stream.start()

    def _audio_callback(self, outdata, frames, time, status):
        mix = np.zeros((frames, 2))
        
        for deck in ['A', 'B']:
            if self.decks[deck]['audio'] is not None and self.decks[deck]['playing']:
                start = int(self.decks[deck]['pos'])
                end = int(start + frames * self.decks[deck]['pitch'])
                
                chunk = self._get_audio_chunk(deck, start, end, frames)
                mix += chunk * (self.decks[deck]['vol'] * self.master_vol * (1.0 if deck == 'A' else self.crossfader))
                
                self.decks[deck]['pos'] = end % len(self.decks[deck]['audio'])

        outdata[:] = np.clip(mix, -1, 1)

    def _get_audio_chunk(self, deck, start, end, frames):
        if self.decks[deck]['pitch'] != 1.0:
            return librosa.effects.time_stretch(
                self.decks[deck]['audio'][start:end],
                self.decks[deck]['pitch']
            )
        chunk = self.decks[deck]['audio'][start:end]
        return np.pad(chunk, ((0, frames - len(chunk)), 'constant') if len(chunk) < frames else chunk

    def load_track(self, deck, path):
        try:
            audio, _ = librosa.load(path, sr=self.sample_rate, mono=False)
            self.decks[deck]['audio'] = audio.T
            return audio[0]  # Mono per waveform
        except Exception as e:
            self._show_error(f"Errore caricamento traccia: {str(e)}")
            return None

    def _show_error(self, message):
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setText(message)
        error_box.setWindowTitle("Errore")
        error_box.exec_()

# ====================== [HARDWARE CONTROLLER] ======================
class MIDIController:
    MAPPINGS = {
        'Mixmeister': {
            0x10: ('A', 'play'),
            0x11: ('A', 'cue'),
            0x20: ('A', 'jog'),
            0x30: ('A', 'pitch'),
            0x40: ('master', 'crossfader')
        },
        'DDJ-400': {}
    }

    def __init__(self, audio_mixer):
        self.mixer = audio_mixer
        self.midi_in = rtmidi.MidiIn()
        self.current_device = None

    def connect(self):
        ports = self.midi_in.get_ports()
        for name, mapping in self.MAPPINGS.items():
            if any(name in port for port in ports):
                self.midi_in.open_port(ports.index(next(p for p in ports if name in p)))
                self.midi_in.set_callback(self._handle_midi)
                self.current_device = name
                return True
        return False

    def _handle_midi(self, event, data=None):
        msg, _ = event
        if self.current_device in self.MAPPINGS:
            mapping = self.MAPPINGS[self.current_device].get(msg[1])
            if mapping:
                deck, control = mapping
                value = msg[2] / 127.0  # Normalizza

                if control == 'play':
                    self.mixer.decks[deck]['playing'] = value > 0.5
                elif control == 'pitch':
                    self.mixer.decks[deck]['pitch'] = 1.0 + (value - 0.5)
                elif control == 'crossfader':
                    self.mixer.crossfader = value

# ====================== [INTERFACCIA] ======================
class DJInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIXMASTER PRO")
        self.setGeometry(100, 100, 1000, 500)
        
        # Inizializza sistemi
        self.mixer = AudioMixer()
        self.mixer.start()
        
        self.controller = MIDIController(self.mixer)
        if not self.controller.connect():
            print("Nessun controller MIDI rilevato - Modalità standalone")
        
        self.waveforms = {'A': deque(maxlen=44100), 'B': deque(maxlen=44100)}
        self._init_ui()
        self._start_update_loop()

    def _init_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet("background: #121212;")
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Deck A
        self.deck_a = self._create_deck("DECK A", 'A')
        layout.addWidget(self.deck_a)
        
        # Mixer Center
        mixer_center = self._create_mixer_center()
        layout.addWidget(mixer_center)
        
        # Deck B
        self.deck_b = self._create_deck("DECK B", 'B')
        layout.addWidget(self.deck_b)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def _create_deck(self, name, deck_id):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #181818;
                border-radius: 8px;
                border: 1px solid #333;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Titolo
        title = QLabel(name)
        title.setStyleSheet("""
            QLabel {
                color: #1a8cff;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)
        
        # Waveform
        self.waveform = QLabel()
        self.waveform.setFixedHeight(120)
        self.waveform.setStyleSheet("background: #000000; border-radius: 4px;")
        layout.addWidget(self.waveform)
        
        # Controlli
        controls = QHBoxLayout()
        
        load_btn = QPushButton("CARICA")
        load_btn.setStyleSheet("""
            QPushButton {
                background: #424242;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #616161;
            }
        """)
        load_btn.clicked.connect(lambda: self._load_track(deck_id))
        
        play_btn = QPushButton("PLAY")
        play_btn.setCheckable(True)
        play_btn.setStyleSheet("""
            QPushButton {
                background: #1976D2;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:checked {
                background: #0D47A1;
            }
        """)
        play_btn.clicked.connect(lambda checked, d=deck_id: self.toggle_play(d))  # Modificato
        
        controls.addWidget(load_btn)
        controls.addWidget(play_btn)
        layout.addLayout(controls)
        
        frame.setLayout(layout)
        return frame

    def toggle_play(self, deck_id):
        """Inverte lo stato di play della deck specificata"""
        self.mixer.decks[deck_id]['playing'] = not self.mixer.decks[deck_id]['playing']

    def _create_mixer_center(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #181818;
                border-radius: 8px;
                border: 1px solid #333;
                min-width: 150px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Crossfader
        crossfader = QSlider(Qt.Horizontal)
        crossfader.setRange(0, 100)
        crossfader.setValue(50)
        crossfader.valueChanged.connect(
            lambda v: setattr(self.mixer, 'crossfader', v/100))
        crossfader.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF5722, stop:0.5 #9C27B0, stop:1 #2196F3);
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                margin: -5px 0;
                background: white;
                border-radius: 10px;
            }
        """)
        layout.addWidget(crossfader)
        
        # Pitch controls
        pitch_layout = QHBoxLayout()
        
        for deck in ['A', 'B']:
            pitch_slider = QSlider(Qt.Vertical)
            pitch_slider.setRange(-50, 50)
            pitch_slider.valueChanged.connect(
                lambda v, d=deck: self._set_pitch(d, v))
            pitch_layout.addWidget(pitch_slider)
        
        layout.addLayout(pitch_layout)
        layout.addStretch()
        
        frame.setLayout(layout)
        return frame

    def _set_pitch(self, deck, value):
        self.mixer.decks[deck]['pitch'] = 1.0 + (value / 100)

    def _load_track(self, deck):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Carica traccia su {deck}",
            os.path.expanduser("~/Music"),
            "File audio (*.mp3 *.wav *.ogg *.flac)"
        )
        
        if path:
            audio = self.mixer.load_track(deck, path)
            if audio is not None:
                self.waveforms[deck].extend(audio[:44100])

    def _start_update_loop(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_ui)
        self.timer.start(30)  # ~33 FPS

    def _update_ui(self):
        # Aggiorna waveform
        for deck in ['A', 'B']:
            if self.mixer.decks[deck]['audio'] is not None:
                pos = int(self.mixer.decks[deck]['pos'])
                chunk = self.mixer.decks[deck]['audio'][pos:pos+100]
                if len(chunk) > 0:
                    self.waveforms[deck].extend(chunk)
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Disegna waveform deck A
        if len(self.waveforms['A']) > 10:
            self._draw_waveform(painter, self.waveforms['A'], 50, 150, 400, 120, QColor(0, 150, 255))
        
        # Disegna waveform deck B
        if len(self.waveforms['B']) > 10:
            self._draw_waveform(painter, self.waveforms['B'], 550, 150, 400, 120, QColor(255, 50, 150))

    def _draw_waveform(self, painter, data, x, y, w, h, color):
        painter.setPen(color)
        center_y = y + h // 2
        
        for i in range(w):
            idx = int(i / w * len(data))
            if idx < len(data):
                value = data[idx]
                y_pos = int(value * (h / 2))
                painter.drawLine(x + i, center_y - y_pos, x + i, center_y + y_pos)

    def closeEvent(self, event):
        self.mixer.stream.stop()
        event.accept()

# ====================== [AVVIO] ======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Stile globale
    app.setStyleSheet("""
        QMainWindow {
            background: #121212;
        }
        QLabel {
            color: #f8f9fa;
            font-family: 'Arial';
        }
    """)
    
    window = DJInterface()
    window.show()
    sys.exit(app.exec_())