from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from datetime import datetime
import re

def save_chat_history(messages, chat_name="Chat", filename=None):
    if not filename:
        safe_name = re.sub(r'[^\w\-_\. ]', '_', chat_name)
        filename = f"{safe_name.replace(' ', '_')}_chat.html"
    
    formatter = HtmlFormatter(style="monokai", full=True)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Chat: {chat_name}</title>
    <style>
        {formatter.get_style_defs()}
        body {{ 
            font-family: 'Segoe UI', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 20px auto;
            padding: 30px;
            background: #1a1a1a;
            color: #e0e0e0;
        }}
        .chat-header {{
            text-align: center;
            border-bottom: 2px solid #66d9ef;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        .message {{
            margin-bottom: 25px;
            padding: 15px;
            border-radius: 8px;
            background: #2a2a2a;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="chat-header">
        <h1>💬 {chat_name}</h1>
        <h3>🗓️ {datetime.now().strftime('%d/%m/%Y %H:%M')}</h3>  <!-- CORRETTO -->
    </div>
    {"".join([f'<div class="message">{msg}</div>' for msg in messages])}
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filename

# Test
if __name__ == "__main__":
    messages = [
        "Umano: Come posso analizzare la tonalità?",
        "AI: Ecco un esempio di codice...",
        "Umano: Grazie! Funziona perfettamente!"
    ]
    save_chat_history(messages, "La Mia Chat Musicale")