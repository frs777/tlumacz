#!/usr/bin/env python3
"""
Skrypt do tłumaczenia plików z TranslateGemma.

Użycie:
    ./transgemma.py plik_zrodlowy plik_wynikowy [jezyk_zrodlowy-jezyk_docelowy]

Przykłady:
    ./transgemma.py test.md test_pl.md en-pl
    ./transgemma.py test.md test_pl.md auto-pl
    ./transgemma.py document.txt document_pl.txt de-pl
    ./transgemma.py input.md output.md   (domyślnie en-pl)

Wymaga:
    - Model TranslateGemma pobrany w ~/Modele/translategemma-4b-it
    - Zainstalowanych zależności: fastapi, uvicorn, transformers, torch
"""

import sys
import time
import signal
import urllib.request
import json
from pathlib import Path

# Ścieżka do modelu
MODEL_PATH = ""  # Ustaw ścieżkę do modelu TranslateGemma przed uruchomieniem
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8001


def check_server():
    """Sprawdź czy serwer już działa."""
    try:
        with urllib.request.urlopen(f"http://{SERVER_HOST}:{SERVER_PORT}/health", timeout=2) as resp:
            return resp.status == 200
    except:
        return False


def start_server():
    """Uruchom serwer TranslateGemma."""
    print("🚀 Uruchamianie serwera TranslateGemma...")
    
    from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig
    
    config = FastAPIServerConfig(
        model_path=MODEL_PATH,
        host=SERVER_HOST,
        port=SERVER_PORT,
        dtype="float32",  # float32 dla CPU
    )
    
    server = TranslateGemmaServer(config)
    
    print("📦 Ładowanie modelu (może zająć ~60s)...")
    start_time = time.time()
    server.load_model()
    print(f"✓ Model załadowany ({time.time()-start_time:.0f}s)")
    
    server.start()
    time.sleep(3)
    
    if check_server():
        print(f"✓ Serwer działa na http://{SERVER_HOST}:{SERVER_PORT}")
    else:
        print("❌ Błąd uruchamiania serwera")
        sys.exit(1)
    
    return server


def translate_file(input_path: str, output_path: str, source_lang: str = "en", target_lang: str = "pl"):
    """Tłumacz plik używając TranslateGemma."""
    from tlumacz.core import Translator, TranslatorConfig
    
    print(f"\n📄 Tłumaczenie: {input_path}")
    print(f"   Język: {source_lang} → {target_lang}")
    
    config = TranslatorConfig(
        base_url=f"http://{SERVER_HOST}:{SERVER_PORT}/v1",
        api_key="none",
        model="translategemma-4b-it",
        target_language="Polish" if target_lang == "pl" else target_lang,
        chat_template="translategemma",
        chunk_size=500,
        cache_enabled=False,
    )
    
    translator = Translator(config)
    
    start_time = time.time()
    translator.translate_file(input_path, output_path)
    elapsed = time.time() - start_time
    
    print(f"✓ Zapisano: {output_path} ({elapsed:.0f}s)")


def main():
    # Parsuj argumenty
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Parsuj języki (np. "en-pl", "de-pl", "auto-pl")
    if len(sys.argv) >= 4:
        langs = sys.argv[3].split("-")
        source_lang = langs[0] if len(langs) > 0 else "en"
        target_lang = langs[1] if len(langs) > 1 else "pl"
    else:
        source_lang = "en"
        target_lang = "pl"
    
    # Sprawdź czy plik wejściowy istnieje
    if not Path(input_path).exists():
        print(f"❌ Plik nie istnieje: {input_path}")
        sys.exit(1)
    
    # Sprawdź czy serwer działa, jeśli nie — uruchom
    server = None
    if not check_server():
        server = start_server()
    else:
        print(f"✓ Serwer już działa na http://{SERVER_HOST}:{SERVER_PORT}")
    
    # Tłumacz plik
    try:
        translate_file(input_path, output_path, source_lang, target_lang)
    except Exception as e:
        print(f"❌ Błąd tłumaczenia: {e}")
        if server:
            server.stop()
        sys.exit(1)
    
    # Zatrzymaj serwer jeśli go uruchomiliśmy
    if server:
        print("\n🛑 Zatrzymywanie serwera...")
        server.stop()
        print("✓ Serwer zatrzymany")
    
    print("\n✅ Gotowe!")


if __name__ == "__main__":
    main()
