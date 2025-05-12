from pygments import highlight
from pygments.lexers import PythonLexer, MarkdownLexer
from pygments.formatters import HtmlFormatter
import uuid

def save_chat_history(messages, filename="chat_history.html"):
    formatter = HtmlFormatter(style="monokai", full=True)
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Storia della Chat - Progetto Harmony Detective</title>
        <style>
            {styles}
            body {{ 
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #1e1e1e;
                color: #d4d4d4;
            }}
            .message {{ 
                margin-bottom: 30px;
                border-left: 3px solid #66d9ef;
                padding-left: 10px;
            }}
            .code-block {{ 
                background: #2d2d2d;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .diagram {{ 
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .save-btn {{
                background: #66d9ef;
                color: black;
                padding: 10px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <h1>Chat del Progetto Harmony Detective</h1>
        <button class="save-btn" onclick="saveAsPDF()">Salva come PDF</button>
        {content}
        <script>
            function saveAsPDF() {{
                window.print();
            }}
        </script>
    </body>
    </html>
    """.format(
        styles=formatter.get_style_defs(),
        content="\n".join([format_message(msg) for msg in messages])
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filename

def format_message(msg):
    if "```" in msg:
        # Estrae e formatta il codice
        code = msg.split("```")[1]
        if code.startswith("python"):
            code = code[6:].strip()
            highlighted = highlight(code, PythonLexer(), HtmlFormatter())
            return f'<div class="message"><div class="code-block">{highlighted}</div></div>'
        elif code.startswith("mermaid"):
            diagram = code[7:].strip()
            return f'''
            <div class="message">
                <div class="mermaid">
                    {diagram}
                </div>
            </div>
            '''
    return f'<div class="message">{msg}</div>'

# Simula la cronologia della chat (sostituisci con la conversazione reale)
chat_messages = [
    "Umano: Come posso rilevare la tonalità di una canzone?",
    "AI: ```python\nprint('Hello World')\n```",
    "Umano: Fantastico! E i diagrammi?",
    "AI: ```mermaid\ngraph TD\nA[Start] --> B{Decision}\nB -->|Yes| C[OK]\n```"
]

file_salvato = save_chat_history(chat_messages)
print(f"Chat salvata in: {file_salvato}")