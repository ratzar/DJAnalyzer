import subprocess
import sys
from pathlib import Path

def check_environment():
    """Verifica i requisiti di sistema"""
    checks = [
        ("Python 3.8+", sys.version_info >= (3, 8)),
        ("Cartella dance2", Path("D:/ToolBox/TidalConvert/dance2").exists()),
    ]
    
    print("\n🔍 Verifica ambiente:")
    all_ok = True
    for name, condition in checks:
        status = "✅" if condition else "❌"
        print(f"{status} {name}")
        if not condition:
            all_ok = False
    
    return all_ok

def run_code_checks():
    """Esegue i controlli sul codice"""
    tools = {
        "Sintassi": ["py_compile"],
        "Tipi": ["mypy"],
        "Stile": ["flake8"],
        "Sicurezza": ["bandit"]
    }
    
    print("\n🔍 Verifica codice:")
    for name, module in tools.items():
        try:
            subprocess.run([sys.executable, "-m", *module, "DJAnalyzer_Fixed.py"], check=True)
            print(f"✅ {name}")
        except subprocess.CalledProcessError:
            print(f"❌ {name} (errori trovati)")
        except FileNotFoundError:
            print(f"⚠️ {name} (installa con: pip install {module[0]})")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 DJ Analyzer - Validazione Pre-Esecuzione")
    print("="*50)
    
    env_ok = check_environment()
    
    if env_ok:
        run_code_checks()
        print("\n📌 Passaggi successivi:")
        print("1. Correggi eventuali errori riportati")
        print("2. Rilancia questo script finché tutti i check sono verdi")
        print("3. Esegui il main con: python DJAnalyzer_Fixed.py")
    else:
        print("\n❌ Correggi gli errori dell'ambiente prima di procedere")
    
    input("\nPremi Invio per uscire...")