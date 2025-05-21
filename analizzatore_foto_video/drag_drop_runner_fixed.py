# drag_drop_runner_fixed.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import sys
import threading

class PythonFileRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Python File Runner")
        self.root.geometry("500x300")
        self.setup_ui()
        self.setup_drag_drop()

        # Variabili di stato
        self.process = None
        self.is_running = False

    def setup_ui(self):
        """Crea l'interfaccia minimalista"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Area drag & drop
        self.drop_area = ttk.Label(
            main_frame,
            text="Trascina qui il file Python (.py) o clicca per selezionare",
            relief=tk.SOLID,
            padding=50,
            anchor=tk.CENTER,
            background="#f0f0f0",
            font=('Helvetica', 12)
        )
        self.drop_area.pack(fill=tk.BOTH, expand=True, pady=10)
        self.drop_area.bind("<Button-1>", self.browse_file)
        
        # Console output
        self.console = tk.Text(main_frame, height=8, state='disabled')
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Pulsante stop
        self.stop_btn = ttk.Button(main_frame, text="Interrompi", command=self.stop_execution, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

    def setup_drag_drop(self):
        """Configura il drag & drop in modo cross-platform"""
        # Per Windows
        if sys.platform == 'win32':
            try:
                from tkinterdnd2 import TkinterDnD
                self.root = TkinterDnD.Tk()  # Ricrea la finestra con supporto DnD
                self.root.title("Python File Runner")
                self.root.geometry("500x300")
                self.setup_ui()  # Ricrea l'interfaccia
                
                self.drop_area.drop_target_register('DND_Files')
                self.drop_area.dnd_bind('<<Drop>>', self.on_drop)
            except ImportError:
                self.drop_area.config(text="Drag&Drop non supportato (installa tkinterdnd2)")
                return
        # Per Linux/macOS
        else:
            self.root.drop_target_register('DND_Files')
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # Effetti visivi
        self.drop_area.bind('<Enter>', lambda e: self.drop_area.config(background="#e0e0ff"))
        self.drop_area.bind('<Leave>', lambda e: self.drop_area.config(background="#f0f0f0"))

    def browse_file(self, event=None):
        """Apre un dialog per selezionare file"""
        if self.is_running:
            messagebox.showwarning("Attenzione", "Interrompere l'esecuzione corrente prima")
            return
            
        file_path = filedialog.askopenfilename(
            title="Seleziona file Python",
            filetypes=[("Python files", "*.py"), ("Tutti i file", "*.*")]
        )
        
        if file_path:
            self.execute_python_file(file_path)

    def on_drop(self, event):
        """Gestisce il file rilasciato"""
        if self.is_running:
            messagebox.showwarning("Attenzione", "Interrompere l'esecuzione corrente prima")
            return
            
        # Gestione multi-piattaforma per i path
        if sys.platform == 'win32':
            file_path = event.data.strip('{}')  # Windows aggiunge parentesi graffe
        else:
            file_path = event.data
            
        if file_path.lower().endswith('.py'):
            self.execute_python_file(file_path)
        else:
            messagebox.showerror("Errore", "Solo file Python (.py) supportati!")

    def execute_python_file(self, file_path):
        """Esegue il file Python in un thread separato"""
        if self.is_running:
            messagebox.showwarning("Attenzione", "Un'operazione è già in corso!")
            return
            
        self.is_running = True
        self.stop_btn.config(state=tk.NORMAL)
        filename = os.path.basename(file_path)
        self.drop_area.config(text=f"Esecuzione: {filename}")
        self.log_output(f"▶ Avvio esecuzione: {filename}\n{'='*50}")
        
        def run():
            try:
                self.process = subprocess.Popen(
                    [sys.executable, file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                while True:
                    output = self.process.stdout.readline()
                    if output == '' and self.process.poll() is not None:
                        break
                    if output:
                        self.log_output(output.strip())
                        
                return_code = self.process.poll()
                status = "✅ Completato" if return_code == 0 else f"❌ Errore (codice {return_code})"
                self.log_output(f"{'='*50}\n{status}\n")
                
            except Exception as e:
                self.log_output(f"❌ Errore critico: {str(e)}\n")
            finally:
                self.is_running = False
                self.stop_btn.config(state=tk.DISABLED)
                self.drop_area.config(text="Trascina qui il file Python (.py) o clicca per selezionare")
                self.process = None
        
        threading.Thread(target=run, daemon=True).start()

    def stop_execution(self):
        """Interrompe l'esecuzione corrente"""
        if self.process and self.is_running:
            self.process.terminate()
            self.log_output("\n⏹ Esecuzione interrotta dall'utente\n")
            self.is_running = False
            self.stop_btn.config(state=tk.DISABLED)

    def log_output(self, message):
        """Scrive nell'area di output"""
        self.console.config(state='normal')
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.config(state='disabled')
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    
    # Stile per migliorare l'aspetto
    style = ttk.Style()
    style.configure('TFrame', background='white')
    style.configure('TLabel', background='#f0f0f0', foreground='black')
    style.map('TLabel', background=[('active', '#e0e0ff')])
    
    app = PythonFileRunner(root)
    root.mainloop()