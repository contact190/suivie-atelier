"""
Lanceur autonome pour SuiviPRO - Étape 1 : Réglages Atelier (100% Python Pur)
"""

import sys
import os
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
    try:
        time.sleep(1.2)
        url = f"http://localhost:{port}"
        print(f"\n🌐 Ouverture automatique de l'interface : {url}\n")
        webbrowser.open(url)
    except Exception:
        pass

if __name__ in {"__main__", "__mp_main__"}:
    port = int(os.environ.get("PORT", 8000))
    is_cloud = bool(os.environ.get("RENDER") or os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("PORT"))
    
    print("=" * 65)
    print(f"🚀 SuiviPRO - Réglages Atelier (100% Python Pur - NiceGUI sur port {port})")
    print("=" * 65)
    
    # N'ouvre le navigateur que si on est en local sur Windows
    if not is_cloud and sys.platform.startswith('win'):
        threading.Thread(target=open_browser, daemon=True).start()
        
    ui.run(
        host="0.0.0.0", 
        port=port, 
        title="SuiviPRO - Étape 1 : Réglages", 
        reload=False,
        show=False
    )
