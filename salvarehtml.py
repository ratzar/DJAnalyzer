from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import uuid

def save_colored_code(code, filename="formatted_code.html"):
    # Genera stili CSS personalizzati
    formatter = HtmlFormatter(style="monokai", cssclass="highlight", full=True)
    highlighted = highlight(code, PythonLexer(), formatter)
    
    # Template HTML con pulsante di copia
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Codice Colorato</title>
        <style>
            {formatter.get_style_defs()}
            body {{ 
                background: #2a2a2a;
                padding: 20px;
                color: #f8f8f2;
            }}
            .copy-btn {{
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 8px;
                background: #66d9ef;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                color: #000;
            }}
        </style>
    </head>
    <body>
        <button class="copy-btn" onclick="copyCode()">Copia Codice</button>
        {highlighted}
        <script>
            function copyCode() {{
                const code = document.querySelector('.highlight pre').innerText;
                navigator.clipboard.writeText(code);
                alert('Codice copiato!');
            }}
        </script>
    </body>
    </html>
    """
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filename

# Esempio di utilizzo con il codice del KeyFinder
codice = """
class RealKeyFinder:
    def __init__(self):
        self.major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        self.minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        self.notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
   
"""

file_salvato = save_colored_code(codice)
print(f"File salvato come: {file_salvato}")

import os
import platform

# Dopo aver generato il file HTML
html_path = os.path.abspath("formatted_code.html")

# Apri automaticamente il file
if platform.system() == 'Windows':
    os.startfile(html_path)
elif platform.system() == 'Darwin':
    os.system(f'open {html_path}')
else:
    os.system(f'xdg-open {html_path}')

 def analyze_file(self, file_path):
        # ... (il codice completo)