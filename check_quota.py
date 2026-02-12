
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key_raw = os.environ.get('GEMINI_API_KEY', '')
api_key = api_key_raw.strip().replace("'", "").replace('"', "").replace('\n', '').replace('\r', '')

# Lista actualizada con el modelo nuevo
models = ["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-2.0-flash-001"]

print(f"🔍 Verificando estado de cuenta con API Key: ...{api_key[-4:]}")
print("-" * 50)

for model in models:
    # Usamos v1beta para los modelos nuevos
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    print(f"Probando {model}...", end=" ")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "hi"}]}]},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ DISPONIBLE (200 OK)")
            print("   ¡Este funciona!")
        elif response.status_code == 429:
            print("❌ CUOTA AGOTADA (429)")
        elif response.status_code == 404:
            print("❓ NO ENCONTRADO (404)")
        else:
            print(f"⚠️ ERROR {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN: {e}")

print("-" * 50)
