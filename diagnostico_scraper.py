"""
diagnostico_scraper.py — Diagnóstico paso a paso del scraper VPN
=================================================================
Corre esto localmente para ver exactamente qué está pasando.

USO:
    .venv\Scripts\python.exe diagnostico_scraper.py
"""

import sys
import io
import re
import json
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings()

# ========== CONFIGURAR AQUÍ ==========
VPN_USER     = input("Usuario VPN: ").strip()
VPN_PASSWORD = input("Contraseña VPN: ").strip()
FECHA_HOY    = datetime.now().strftime("%d/%m/%Y")
# =====================================

URL_LOGIN    = "https://portalvpn.sofse.gob.ar/global-protect/login.esp"
URL_BASE     = "https://portalvpn.sofse.gob.ar/https/novedades.sofse.gob.ar"
URL_MENSAJES = f"{URL_BASE}/mensajes"
URL_SET_AREA = f"{URL_BASE}/areas/set_area"
AREA_SAN_MARTIN = 555

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
}

print("\n" + "="*60)
print("  DIAGNÓSTICO SCRAPER SOFSE VPN")
print(f"  Usuario: {VPN_USER}")
print(f"  Fecha: {FECHA_HOY}")
print("="*60)

session = requests.Session()
session.headers.update(HEADERS)
session.verify = False

# ── PASO 1: GET login page ──────────────────────────────────────
print("\n[PASO 1] GET login page...")
r = session.get(URL_LOGIN, timeout=20)
print(f"  Status: {r.status_code}")
print(f"  Cookies: {dict(session.cookies)}")

soup = BeautifulSoup(r.text, 'html.parser')
csrf_input = soup.find('input', {'name': 'csrf-token'})
csrf_token = csrf_input['value'] if csrf_input else ''
print(f"  CSRF token: '{csrf_token[:20]}...' " if csrf_token else "  CSRF token: NO ENCONTRADO ⚠️")

# ── PASO 2: POST login ──────────────────────────────────────────
print("\n[PASO 2] POST login con credenciales...")
form_data = {
    'prot': '3', 'server': '', 'inputStr': '',
    'action': 'getsoftware',
    'csrf-token': csrf_token,
    'user': VPN_USER,
    'passwd': VPN_PASSWORD,
    'ok': 'Log In',
}
r2 = session.post(URL_LOGIN, data=form_data, timeout=30, allow_redirects=True)
print(f"  Status: {r2.status_code}")
print(f"  URL final: {r2.url}")
print(f"  Cookies post-login: {list(session.cookies.keys())}")

# Verificar si login fue exitoso
if 'passwd' in r2.text and 'Log In' in r2.text:
    soup2 = BeautifulSoup(r2.text, 'html.parser')
    error_div = soup2.find('div', class_='error') or soup2.find('span', class_='error')
    error_msg = error_div.get_text(strip=True) if error_div else 'Sin mensaje de error específico'
    print(f"  ❌ LOGIN FALLÓ: {error_msg}")
    print(f"  Primeros 500 chars de respuesta:")
    print(f"  {r2.text[:500]}")
    sys.exit(1)
else:
    print(f"  ✅ Login exitoso")
    print(f"  Snippet respuesta: {r2.text[:200]}")

# ── PASO 3: Cambiar área San Martín ────────────────────────────
print(f"\n[PASO 3] Cambiar área a San Martín (id={AREA_SAN_MARTIN})...")
r3 = session.get(f"{URL_SET_AREA}/{AREA_SAN_MARTIN}", timeout=20, allow_redirects=True)
print(f"  Status: {r3.status_code}")
print(f"  URL final: {r3.url}")
print(f"  Snippet: {r3.text[:200]}")

# ── PASO 4: GET mensajes SIN filtro ────────────────────────────
print(f"\n[PASO 4] GET {URL_MENSAJES} (sin filtro)...")
r4 = session.get(URL_MENSAJES, timeout=30, allow_redirects=True)
print(f"  Status: {r4.status_code}")
print(f"  URL final: {r4.url}")

soup4 = BeautifulSoup(r4.text, 'html.parser')
paneles = soup4.find_all('div', class_='panel-mensaje')
print(f"  Paneles de mensajes encontrados: {len(paneles)}")

if len(paneles) == 0:
    print("\n  ⚠️  SIN PANELES — guardando HTML para inspección...")
    with open('debug_mensajes_sin_filtro.html', 'w', encoding='utf-8') as f:
        f.write(r4.text)
    print("  Guardado: debug_mensajes_sin_filtro.html")
    print(f"  Título de la página: {soup4.find('title')}")
    print(f"  Snippet del body: {r4.text[1000:2000]}")
else:
    # Mostrar primeros 3 mensajes
    print(f"\n  Primeros mensajes encontrados:")
    for i, panel in enumerate(paneles[:3]):
        titulo = panel.find('h3', class_='panel-title')
        id_msg = panel.get('data-id_mensaje', 'sin-id')
        titulo_txt = titulo.get_text(strip=True) if titulo else 'sin título'
        contenido_ta = panel.find('textarea', class_='form-control')
        contenido_txt = contenido_ta.get_text(strip=True)[:80] if contenido_ta else 'sin contenido'
        print(f"  [{i+1}] id={id_msg} | {titulo_txt[:60]}")
        print(f"       contenido: {contenido_txt}")

# ── PASO 5: Inspeccionar form de filtros ───────────────────────
print(f"\n[PASO 5] Inspeccionando form de filtros...")
forms = soup4.find_all('form')
print(f"  Forms encontrados: {len(forms)}")
for i, form in enumerate(forms):
    action = form.get('action', 'sin action')
    method = form.get('method', 'GET')
    inputs = [(inp.get('name',''), inp.get('type',''), inp.get('value','')[:30])
              for inp in form.find_all('input')]
    selects = [(sel.get('name',''), [o.get_text(strip=True) for o in sel.find_all('option')][:5])
               for sel in form.find_all('select')]
    print(f"  Form {i+1}: action='{action}' method='{method}'")
    print(f"    Inputs: {inputs[:8]}")
    print(f"    Selects: {selects[:4]}")

# ── PASO 6: Intentar filtro de fecha ───────────────────────────
print(f"\n[PASO 6] Intentar POST con filtro de fecha >= {FECHA_HOY}...")

# Extraer campos ocultos del primer form
form_filtro_data = {}
if forms:
    for inp in forms[0].find_all('input', type='hidden'):
        n = inp.get('name', '')
        v = inp.get('value', '')
        if n:
            form_filtro_data[n] = v

form_filtro_data.update({
    'filtros[0][campo]': 'fecha',
    'filtros[0][op]': 'gte',
    'filtros[0][valor]': FECHA_HOY,
    'buscar': '1',
})
print(f"  Datos del POST: {form_filtro_data}")

action_url = forms[0].get('action', URL_MENSAJES) if forms else URL_MENSAJES
if action_url and not action_url.startswith('http'):
    from urllib.parse import urljoin
    action_url = urljoin(URL_BASE, action_url)

r5 = session.post(action_url or URL_MENSAJES, data=form_filtro_data, timeout=30)
print(f"  Status: {r5.status_code}")
print(f"  URL final: {r5.url}")

soup5 = BeautifulSoup(r5.text, 'html.parser')
paneles5 = soup5.find_all('div', class_='panel-mensaje')
print(f"  Paneles post-filtro: {len(paneles5)}")

if paneles5:
    print(f"  Primeros mensajes post-filtro:")
    for i, panel in enumerate(paneles5[:3]):
        titulo = panel.find('h3', class_='panel-title')
        titulo_txt = titulo.get_text(strip=True) if titulo else 'sin título'
        match_fh = re.search(r'(\d{2}/\d{2}/\d{4})', titulo_txt)
        fecha_msg = match_fh.group(1) if match_fh else 'sin fecha'
        print(f"  [{i+1}] fecha={fecha_msg} | {titulo_txt[:60]}")
else:
    print("  ⚠️  Sin paneles post-filtro. Guardando HTML...")
    with open('debug_mensajes_filtrado.html', 'w', encoding='utf-8') as f:
        f.write(r5.text)
    print("  Guardado: debug_mensajes_filtrado.html")

# ── RESUMEN ─────────────────────────────────────────────────────
print("\n" + "="*60)
print("  RESUMEN DEL DIAGNÓSTICO")
print("="*60)
print(f"  Login: {'✅ OK' if '✅' in 'Login exitoso' else '❌ FALLÓ'}")
print(f"  Área San Martín: status={r3.status_code}")
print(f"  Mensajes sin filtro: {len(paneles)}")
print(f"  Mensajes con filtro: {len(paneles5)}")
if len(paneles) == 0:
    print("\n  💡 PROBLEMA: No se están encontrando paneles de mensajes.")
    print("     Revisá debug_mensajes_sin_filtro.html para ver qué devuelve el servidor.")
elif len(paneles5) == 0 and len(paneles) > 0:
    print("\n  💡 PROBLEMA: El filtro no está funcionando correctamente.")
    print("     Revisá debug_mensajes_filtrado.html para ver la respuesta del servidor.")
    print("     Puede que el form_data necesite campos diferentes.")
