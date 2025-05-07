import os
import sys
import traceback
from pathlib import Path

def validate_environment():
    """Verifica fondamentale prima di eseguire lo script"""
    try:
        # 1. Controlla versione Python
        assert sys.version_info >= (3, 8), "Richiede Python 3.8+"
        
        # 2. Verifica cartella dance2
        dance2_path = Path("D:/ToolBox/TidalConvert/dance2")
        if not dance2_path.exists():
            raise FileNotFoundError(f"Cartella non trovata: {dance2_path}")
            
        # 3. Verifica permessi scrittura
        test_file = dance2_path / "permission_test.txt"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            raise PermissionError(f"Nessun permesso scrittura in {dance2_path}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore configurazione: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    if validate_environment():
        print("✅ Ambiente verificato con successo")
        # Qui inserisci il resto del codice
    else:
        print("⚠️ Correggi gli errori prima di procedere")
        sys.exit(1)