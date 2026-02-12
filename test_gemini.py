
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key_raw = os.environ.get('GEMINI_API_KEY', '')
# Limpieza de clave
api_key = api_key_raw.strip().replace("'", "").replace('"', "").replace('\n', '').replace('\r', '')

print(f"🔑 Clave leída: ...{api_key[-6:] if len(api_key)>6 else '???'}")

# Lista de modelos técnicos a probar
models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-pro",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "gemini-2.0-flash-exp", 
]

print("\n--- INICIO DE DIAGNÓSTICO DE MODELOS ---")

success_model = None

# Primero intentamos listar modelos disponibles para esta clave
try:
    url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    resp = requests.get(url_list, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print("\n📋 Modelos disponibles para tu clave:")
        for m in data.get('models', []):
            name = m.get('name', '').replace('models/', '')
            print(f"  - {name}")
            # Si encontramos uno de la lista preferida, lo marcamos
            if "gemini-1.5-flash" in name:
                success_model = name
    else:
        print(f"\n⚠️ No se pudo listar modelos. Error {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"\n⚠️ Error al intentar listar modelos: {e}")

print("\n--- PRUEBA DE GENERACIÓN (GenerateContent) ---")

# Probamos generación con cada uno por si acaso
for model in models_to_test:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    print(f"\nTesting: {model} ...", end=" ")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{"text": "Responde solo OK"}]
                }]
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ FUNCIONA!")
            success_model = model
            break
        else:
            print(f"❌ Error {response.status_code}")
            # print(f"   {response.text[:100]}")
    except Exception as e:
        print(f"❌ Excepción: {e}")

if success_model:
    print(f"\n🎉 ¡ENCONTRADO! El modelo que debes usar es: {success_model}")
else:
    print("\n💀 Ningún modelo funcionó. Verifica la clave API o la facturación del proyecto.")
