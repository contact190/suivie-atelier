"""
Lanceur autonome pour SuiviPRO - Étape 1 : Réglages Atelier (100% Python Pur)
"""

import sys
import webbrowser
import threading
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from nicegui import ui
import app  # Importe l'application NiceGUI configurée

def open_browser():
    time.sleep(1.2)
    url = "http://localhost:8000"
    print(f"\n🌐 Ouverture automatique de l'interface : {url}\n")
    webbrowser.open(url)

if __name__ in {"__main__", "__mp_main__"}:
    print("=" * 65)
    print("🚀 SuiviPRO - Étape 1 : Réglages Atelier (100% Python Pur - NiceGUI)")
    print("=" * 65)
    threading.Thread(target=open_browser, daemon=True).start()
    ui.run(
        host="0.0.0.0", 
        port=8000, 
        title="SuiviPRO - Étape 1 : Réglages", 
        reload=False,
        show=False
    )
