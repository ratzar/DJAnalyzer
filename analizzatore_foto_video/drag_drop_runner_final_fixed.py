# drag_drop_runner_final_fixed.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import sys
import threading
import queue
import time
from datetime import datetime

class PythonFileRunner:
    def __init__(self):
        # Creazione della finestra principale
        self.root = tk.Tk()
        self.root.title("Python File Runner")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Variabili di stato
        self.process = None
        self.is_running = False
        self.output_queue = queue.Queue()
        self.current_file = ""
        
        self.setup_ui()
        self.setup_drag_drop()
        self.setup_styles()
        
        # Avvia il controllo periodico della coda
        self.root.after(100, self.check_queue)

    def setup_ui(self):
        """Crea l'interfaccia utente"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Pannello superiore
        top_panel = ttk.Frame(main_frame)
        top_panel.pack(fill=tk.X, pady=5)
        
        # Pulsante apri file
        ttk.Button(top_panel, text="Apri file", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        
        # Pulsante pulisci console
        ttk.Button(top_panel, text="Pulisci", command=self.clear_console).pack(side=tk.LEFT, padx=5)
        
        # Pulsante stop
        self.stop_btn = ttk.Button(top_panel, text="Interrompi", command=self.stop_execution, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)
        
        # Area drag & drop
        self.drop_area = ttk.Label(
            main_frame,
            text="Trascina qui file Python (.py) o clicca 'Apri file'",
            relief=tk.SOLID,
            padding=40,
            anchor=tk.CENTER,
            font=('Helvetica', 12)
        )
        self.drop_area.pack(fill=tk.BOTH, expand=False, pady=10)
        self.drop_area.bind("<Button-1>", lambda e: self.browse_file())
        
        # Etichetta stato
        self.status_label = ttk.Label(main_frame, text="Pronto", anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)
        
        # Console output
        console_frame = ttk.Frame(main_frame)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console = tk.Text(
            console_frame,
            wrap=tk.WORD,
            state='disabled',
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        
        # Configurazione tag per colori
        self.console.tag_config('error', foreground='#ff6b6b')
        self.console.tag_config('warning', foreground='#feca57')
        self.console.tag_config('info', foreground='#48dbfb')
        self.console.tag_config('success', foreground='#1dd1a1')
        self.console.tag_config('output', foreground='#d4d4d4')
        
        y_scroll = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=self.console.yview)
        self.console.configure(yscrollcommand=y_scroll.set)
        
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_styles(self):
        """Configura gli stili dell'interfaccia"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('.', background='#333', foreground='white')
        style.configure('TFrame', background='#333')
        style.configure('TLabel', background='#444', foreground='white')
        style.configure('TButton', padding=5, background='#555', foreground='white')
        style.map('TButton',
            background=[('active', '#666'), ('disabled', '#333')],
            foreground=[('active', 'white'), ('disabled', '#777')]
        )
        
        self.drop_area.config(background='#444')
        self.status_label.config(background='#333', foreground='#aaa')

    def setup_drag_drop(self):
        """Configura il drag & drop"""
        try:
            if sys.platform == 'win32':
                from tkinterdnd2 import TkinterDnD
                # Usiamo TkinterDnD solo per l'area di drop
                self.drop_area.drop_target_register(TkinterDnD.DND_FILES)
                self.drop_area.dnd_bind('<<Drop>>', self.on_drop)
            else:
                self.root.drop_target_register('DND_Files')
                self.root.dnd_bind('<<Drop>>', self.on_drop)
            
            # Effetti visivi
            self.drop_area.bind('<Enter>', lambda e: self.drop_area.config(background='#555'))
            self.drop_area.bind('<Leave>', lambda e: self.drop_area.config(background='#444'))
        except ImportError:
            self.log_output("⚠ tkinterdnd2 non installato (usa il pulsante 'Apri file')", 'warning')
        except Exception as e:
            self.log_output(f"⚠ Drag&Drop non disponibile: {str(e)}", 'warning')

    def browse_file(self):
        """Apre un dialog per selezionare file"""
        if self.is_running:
            messagebox.showwarning("Attenzione", "Interrompere l'esecuzione corrente prima")
            return
            
        files = filedialog.askopenfilenames(
            title="Seleziona file Python",
            filetypes=[("Python files", "*.py"), ("Tutti i file", "*.*")]
        )
        
        if files:
            self.execute_files(files)

    def on_drop(self, event):
        """Gestisce i file rilasciati"""
        if self.is_running:
            messagebox.showwarning("Attenzione", "Interrompere l'esecuzione corrente prima")
            return
            
        files = []
        if sys.platform == 'win32':
            files = [f.strip('{}') for f in event.data.split()]
        else:
            files = [event.data]
            
        py_files = [f for f in files if f.lower().endswith('.py')]
        
        if py_files:
            self.execute_files(py_files)
        else:
            self.log_output("❌ Nessun file Python (.py) trovato tra i file rilasciati", 'error')

    def execute_files(self, file_paths):
        """Esegue una lista di file Python in sequenza"""
        if not file_paths:
            return
            
        threading.Thread(target=self._run_files_sequentially, args=(file_paths,), daemon=True).start()

    def _run_files_sequentially(self, file_paths):
        """Esegue i file uno dopo l'altro"""
        for file_path in file_paths:
            if not self.is_running:  # Solo se non è stato richiesto lo stop
                self.execute_python_file(file_path)
                time.sleep(0.5)

    def execute_python_file(self, file_path):
        """Esegue un singolo file Python"""
        self.current_file = file_path
        self.is_running = True
        
        # Aggiorna l'interfaccia dal thread principale
        self.root.after(0, self._update_ui_running, os.path.basename(file_path))
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output(f"[{timestamp}] ▶ Avvio: {os.path.basename(file_path)}\n{'='*60}", 'info')
        
        try:
            self.process = subprocess.Popen(
                [sys.executable, file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                shell=False
            )
            
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    if 'Traceback' in output or 'Error' in output or 'Exception' in output:
                        self.log_output(output.strip(), 'error')
                    else:
                        self.log_output(output.strip(), 'output')
            
            return_code = self.process.poll()
            
            if return_code == 0:
                status = "✅ Esecuzione completata con successo"
                self.log_output(f"{'='*60}\n{status}\n", 'success')
            else:
                status = f"❌ Esecuzione fallita (codice: {return_code})"
                self.log_output(f"{'='*60}\n{status}\n", 'error')
                
        except Exception as e:
            error_msg = f"❌ Errore critico durante l'esecuzione: {str(e)}"
            self.log_output(f"{error_msg}\n", 'error')
        finally:
            self.is_running = False
            self.process = None
            self.root.after(0, self._update_ui_ready)

    def _update_ui_running(self, filename):
        """Aggiorna l'UI quando un file è in esecuzione"""
        self.stop_btn.config(state=tk.NORMAL)
        self.drop_area.config(text=f"Esecuzione: {filename}")
        self.status_label.config(text=f"Esecuzione: {filename}")

    def _update_ui_ready(self):
        """Aggiorna l'UI quando pronta"""
        self.stop_btn.config(state=tk.DISABLED)
        self.drop_area.config(text="Trascina qui file Python (.py) o clicca 'Apri file'")
        self.status_label.config(text=f"Pronto - Ultimo file: {os.path.basename(self.current_file)}")

    def check_queue(self):
        """Controlla periodicamente la coda per aggiornare la console"""
        while not self.output_queue.empty():
            message, tag = self.output_queue.get_nowait()
            self._log_output_safe(message, tag)
        self.root.after(100, self.check_queue)

    def _log_output_safe(self, message, tag='output'):
        """Scrive nell'area di output in modo thread-safe"""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n", tag)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def log_output(self, message, tag='output'):
        """Metodo pubblico per loggare output (thread-safe)"""
        self.output_queue.put((message, tag))

    def stop_execution(self):
        """Interrompe l'esecuzione corrente"""
        if self.process and self.is_running:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_output(f"[{timestamp}] ⏹ Esecuzione interrotta dall'utente: {os.path.basename(self.current_file)}", 'warning')
            self.is_running = False
            self.process = None
            self._update_ui_ready()

    def clear_console(self):
        """Pulisce la console di output"""
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)

    def run(self):
        """Avvia l'applicazione"""
        self.root.mainloop()

if __name__ == "__main__":
    # Creazione e avvio dell'applicazione
    app = PythonFileRunner()
    app.run()