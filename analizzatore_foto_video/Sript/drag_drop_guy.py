# video_processor_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import threading
import os

class VideoProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizzatore Video AI")
        self.root.geometry("800x600")
        
        # Stile moderno
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        
        self.create_widgets()
        self.process = None

    def create_widgets(self):
        """Crea l'interfaccia grafica"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Area Drag & Drop
        drop_frame = ttk.LabelFrame(main_frame, text="Trascina il video qui", padding="20")
        drop_frame.pack(pady=10, fill=tk.X)
        
        self.drop_label = ttk.Label(drop_frame, text="Nessun file selezionato", foreground="grey")
        self.drop_label.pack()
        
        # Configurazione drag & drop
        drop_frame.bind("<Button-1>", self.browse_file)
        drop_frame.bind("<DragEnter>", self.on_drag_enter)
        drop_frame.bind("<DragLeave>", self.on_drag_leave)
        drop_frame.bind("<B1-Motion>", self.on_drag_motion)
        drop_frame.bind("<Drop>", self.on_drop)

        # Pannello opzioni
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(options_frame, text="Modalità analisi:").grid(row=0, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="faces")
        modes = [("Volti", "faces"), ("Oggetti", "objects"), ("Scene", "scenes")]
        for i, (text, mode) in enumerate(modes):
            ttk.Radiobutton(options_frame, text=text, variable=self.mode_var, value=mode).grid(row=0, column=i+1, padx=5)

        # Output console
        console_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, height=15)
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Avvia Analisi", command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Interrompi", command=self.stop_processing).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Apri Cartella Output", command=self.open_output).pack(side=tk.RIGHT)

    def browse_file(self, event):
        """Apri file dialog"""
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if file_path:
            self.set_file(file_path)

    def on_drag_enter(self, event):
        """Animazione drag enter"""
        self.drop_label.config(text="Rilascia il video qui!", foreground="blue")
        event.widget.config(relief=tk.SUNKEN)

    def on_drag_leave(self, event):
        """Animazione drag leave"""
        self.drop_label.config(text="Trascina il video qui", foreground="grey")
        event.widget.config(relief=tk.RAISED)

    def on_drag_motion(self, event):
        """Gestione movimento drag"""
        pass

    def on_drop(self, event):
        """Gestione file rilasciato"""
        file_path = event.data.strip()
        if os.path.isfile(file_path):
            self.set_file(file_path)
        self.on_drag_leave(event)

    def set_file(self, file_path):
        """Imposta il file da processare"""
        self.file_path = file_path
        self.drop_label.config(text=os.path.basename(file_path), foreground="black")
        self.write_to_console(f"✅ File selezionato: {file_path}")

    def start_processing(self):
        """Avvia l'analisi in un thread separato"""
        if not hasattr(self, 'file_path'):
            self.write_to_console("❌ Nessun file selezionato!")
            return
            
        if self.process and self.process.poll() is None:
            self.write_to_console("⚠ Analisi già in corso!")
            return
            
        mode = self.mode_var.get()
        self.write_to_console(f"🚀 Avvio analisi in modalità {mode}...")
        
        # Comando da eseguire (adatta al tuo script)
        cmd = f"python gpu_analisi_video.py --input {self.file_path} --mode {mode}"
        
        # Esegui in un thread per non bloccare la GUI
        thread = threading.Thread(target=self.run_command, args=(cmd,), daemon=True)
        thread.start()

    def run_command(self, cmd):
        """Esegue il comando e cattura l'output"""
        self.process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        while True:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                break
            if output:
                self.write_to_console(output.strip())
        
        self.write_to_console(f"🔚 Codice uscita: {self.process.returncode}")

    def stop_processing(self):
        """Interrompe l'analisi in corso"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.write_to_console("⏹ Analisi interrotta!")

    def open_output(self):
        """Apre la cartella di output"""
        output_dir = os.path.join(os.path.dirname(__file__), "output_frames")
        os.makedirs(output_dir, exist_ok=True)
        os.startfile(output_dir)

    def write_to_console(self, message):
        """Scrive messaggi nella console"""
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoProcessorApp(root)
    root.mainloop()