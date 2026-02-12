
import os
import requests
from dotenv import load_dotenv

# Forzar recarga de variables de entorno desde el archivo .env actual
load_dotenv(override=True)

openai_key = os.environ.get('OPENAI_API_KEY', '').strip().replace("'", "").replace('"', "")
gemini_key = os.environ.get('GEMINI_API_KEY', '').strip().replace("'", "").replace('"', "")

print(f"--- DIAGNÓSTICO DE CLAVES ---")
if openai_key:
    print(f"🔑 OPENAI_API_KEY detectada: {openai_key[:8]}...{openai_key[-4:]} (Longitud: {len(openai_key)})")
else:
    print(f"❌ OPENAI_API_KEY NO detectada o vacía.")

if gemini_key:
    print(f"🔑 GEMINI_API_KEY detectada: {gemini_key[:8]}...{gemini_key[-4:]} (Longitud: {len(gemini_key)})")
else:
    print(f"❌ GEMINI_API_KEY NO detectada o vacía.")
print("-" * 30)

# --- PRUEBA OPENAI ---
if openai_key:
    print("\n📡 Probando conexión con OpenAI (gpt-4o-mini)...")
    try:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hola"}],
            "max_tokens": 5
        }
        res = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_key}"
            },
            json=payload,
            timeout=10
        )
        if res.status_code == 200:
            print("✅ OpenAI FUNCIONA CORRECTAMENTE.")
            print(f"Respuesta: {res.json()['choices'][0]['message']['content']}")
        else:
            print(f"❌ Error OpenAI ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"❌ Excepción OpenAI: {e}")
else:
    print("⚠️ Saltando prueba OpenAI (sin clave).")

# --- PRUEBA GEMINI ---
if gemini_key:
    print("\n📡 Probando conexión con Gemini (varios modelos)...")
    models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            print(f"   Probando {model}...", end=" ")
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": "Hola"}]}]},
                timeout=5
            )
            if res.status_code == 200:
                print("✅ OK")
            else:
                print(f"❌ Error {res.status_code}")
        except Exception as e:
            print(f"❌ Excepción: {e}")
else:
    print("⚠️ Saltando prueba Gemini (sin clave).")
