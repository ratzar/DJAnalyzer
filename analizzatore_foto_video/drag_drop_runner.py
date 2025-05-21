# drag_drop_runner.py
import tkinter as tk
from tkinter import ttk, messagebox
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

    def setup_ui(self):
        """Crea l'interfaccia minimalista"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Area drag & drop
        self.drop_area = ttk.Label(
            main_frame,
            text="Trascina qui il file Python (.py)",
            relief=tk.SOLID,
            padding=50,
            anchor=tk.CENTER,
            background="#f0f0f0",
            font=('Helvetica', 12)
        )
        self.drop_area.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Console output
        self.console = tk.Text(main_frame, height=8, state='disabled')
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Pulsante stop
        ttk.Button(main_frame, text="Interrompi", command=self.stop_execution).pack(pady=5)
        
        # Variabili di stato
        self.process = None
        self.is_running = False

    def setup_drag_drop(self):
        """Configura il drag & drop"""
        self.root.drop_target_register('DND_Files')
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # Effetti visivi
        self.drop_area.bind('<Enter>', lambda e: self.drop_area.config(background="#e0e0ff"))
        self.drop_area.bind('<Leave>', lambda e: self.drop_area.config(background="#f0f0f0"))

    def on_drop(self, event):
        """Gestisce il file rilasciato"""
        file_path = event.data.strip('{}')  # Rimuove le parentesi graffe su Windows
        
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
        self.drop_area.config(text=f"Esecuzione: {os.path.basename(file_path)}")
        self.log_output(f"▶ Avvio esecuzione: {file_path}\n{'='*50}")
        
        def run():
            try:
                self.process = subprocess.Popen(
                    [sys.executable, file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW  # Non mostra finestra CMD
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
                self.drop_area.config(text="Trascina qui il file Python (.py)")
                self.process = None
        
        threading.Thread(target=run, daemon=True).start()

    def stop_execution(self):
        """Interrompe l'esecuzione corrente"""
        if self.process and self.is_running:
            self.process.terminate()
            self.log_output("\n⏹ Esecuzione interrotta dall'utente\n")
            self.is_running = False
            self.drop_area.config(text="Trascina qui il file Python (.py)")

    def log_output(self, message):
        """Scrive nell'area di output"""
        self.console.config(state='normal')
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.config(state='disabled')
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonFileRunner(root)
    
    # Stile per migliorare l'aspetto
    style = ttk.Style()
    style.configure('TFrame', background='white')
    style.configure('TLabel', background='#f0f0f0', foreground='black')
    style.map('TLabel', background=[('active', '#e0e0ff')])
    
    root.mainloop()