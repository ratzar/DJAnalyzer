import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    messagebox.showerror("Dipendenza mancante",
        "Installa tkinterdnd2:\n\npip install tkinterdnd2")
    sys.exit(1)

# Flag per aprire nuova console su Windows
CREATE_NEW_CONSOLE = 0x00000010

class ScriptLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("DJAnalyzer Script Launcher")
        # area drag & drop
        self.drop_frame = tk.Label(root, text="⇪ Trascina qui i .py ⇪",
                                   relief="ridge", width=40, height=5)
        self.drop_frame.pack(padx=10, pady=10)
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)

        # pulsante Test All
        tk.Button(root, text="🔍 Test All", command=self.test_all).pack(fill="x", padx=10, pady=5)

        # frame per lista script
        self.list_frame = tk.Frame(root)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # directory degli script: stessa cartella di questo file
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.modules = []
        self.status_labels = {}
        self.load_scripts()

    def load_scripts(self):
        # pulisce lista
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.modules.clear()
        # carica tutti i .py nella directory
        for fname in sorted(os.listdir(self.script_dir)):
            if fname.endswith(".py") and fname != os.path.basename(__file__):
                path = os.path.join(self.script_dir, fname)
                self.add_module(fname, path)

    def add_module(self, name, path):
        frame = tk.Frame(self.list_frame)
        btn = tk.Button(frame, text=name, command=lambda p=path, n=name: self.launch(p,n))
        lbl = tk.Label(frame, text="–", width=2)
        btn.pack(side="left", fill="x", expand=True)
        lbl.pack(side="right")
        frame.pack(fill="x", pady=2)
        self.modules.append({"name": name, "path": path})
        self.status_labels[name] = lbl

    def on_drop(self, event):
        files = self.root.splitlist(event.data)
        for f in files:
            if f.endswith(".py"):
                name = os.path.basename(f)
                if name not in self.status_labels:
                    self.add_module(name, f)

    def launch(self, path, name):
        # avvia script in nuova console (Windows)
        subprocess.Popen(
            [sys.executable, path],
            creationflags=CREATE_NEW_CONSOLE
        )

    def test_all(self):
        report = []
        for mod in self.modules:
            proc = subprocess.run(
                [sys.executable, mod["path"]],
                capture_output=True, text=True,
                creationflags=CREATE_NEW_CONSOLE
            )
            ok = proc.returncode == 0
            self.status_labels[mod["name"]].config(text="✅" if ok else "❌")
            report.append(f"{'✅' if ok else '❌'} {mod['name']}")
        messagebox.showinfo("Risultati Test All", "\n".join(report))

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ScriptLauncher(root)
    root.mainloop()
