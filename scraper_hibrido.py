"""
scraper_hibrido.py — Scraper VPN con login automático y extracción via CDP
==========================================================================
Flujo:
  1. abrir_y_login()  → Playwright abre Chrome, navega al portal VPN, hace login
  2. (usuario navega manualmente hasta la página de mensajes)
  3. extraer_pagina_actual() → Conecta al Chrome abierto via CDP, lee HTML, extrae mensajes
  4. cerrar_browser()  → Cierra el Chrome

Requiere: playwright instalado + Chrome del sistema
"""

import re
import sys
import os
from datetime import datetime

# Intentar importar playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_DISPONIBLE = True
except ImportError:
    PLAYWRIGHT_DISPONIBLE = False

# Reusar el parser HTML de scraper_requests (sin depender de Playwright)
from scraper_requests import extraer_mensajes_html

# =================================================================
#  CONFIGURACIÓN
# =================================================================

# Chrome del sistema — ajustar según el equipo
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
]

CDP_PORT = 9222
URL_LOGIN = "https://portalvpn.sofse.gob.ar/global-protect/login.esp"


def _encontrar_chrome():
    """Busca el ejecutable de Chrome en las rutas conocidas."""
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    return None


# =================================================================
#  ESTADO GLOBAL DEL BROWSER
# =================================================================

_playwright_instance = None
_browser = None


# =================================================================
#  ABRIR CHROME Y HACER LOGIN
# =================================================================

def abrir_y_login(vpn_user: str, vpn_password: str) -> dict:
    """
    Abre Chrome con debug port, navega al portal VPN y hace login.
    El Chrome queda abierto para que el usuario navegue manualmente.

    Retorna dict con:
      - ok: bool
      - mensaje: str (descripción del resultado)
      - url: str (URL final después del login)
    """
    global _playwright_instance, _browser

    if not PLAYWRIGHT_DISPONIBLE:
        return {
            'ok': False,
            'mensaje': 'Playwright no está instalado. Corré: pip install playwright && playwright install chromium'
        }

    chrome_path = _encontrar_chrome()
    if not chrome_path:
        return {
            'ok': False,
            'mensaje': f'No se encontró Chrome. Rutas buscadas: {CHROME_PATHS}'
        }

    # Cerrar browser anterior si existe
    cerrar_browser()

    try:
        _playwright_instance = sync_playwright().start()
        _browser = _playwright_instance.chromium.launch(
            executable_path=chrome_path,
            headless=False,
            args=[
                f"--remote-debugging-port={CDP_PORT}",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        context = _browser.new_context(
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()

        # Navegar al login
        print(f"🌐 Navegando a {URL_LOGIN}...")
        page.goto(URL_LOGIN, wait_until="networkidle", timeout=30000)

        # Rellenar formulario de login
        print(f"🔑 Ingresando credenciales para '{vpn_user}'...")
        page.fill('input[name="user"]', vpn_user)
        page.fill('input[name="passwd"]', vpn_password)
        page.click('input[name="ok"]')

        # Esperar a que procese el login
        page.wait_for_timeout(4000)

        # Verificar resultado del login
        url_final = page.url
        contenido = page.content()

        # Si sigue en login.esp con el form, falló
        if 'passwd' in contenido and 'Log In' in contenido and 'login.esp' in url_final:
            return {
                'ok': False,
                'mensaje': 'Credenciales VPN incorrectas. Verificá usuario y contraseña.',
                'url': url_final
            }

        # Si hay JS redirect a portal.esp, seguirlo
        match_js = re.search(r'window\.location\s*=\s*"([^"]+)"', contenido)
        if match_js:
            next_path = match_js.group(1)
            if not next_path.startswith('http'):
                next_path = f"https://portalvpn.sofse.gob.ar{next_path}"
            print(f"  ↪ Siguiendo redirect a {next_path}...")
            page.goto(next_path, wait_until="networkidle", timeout=15000)
            url_final = page.url

        print(f"✅ Login exitoso. URL final: {url_final}")
        print(f"   Chrome queda abierto en puerto CDP {CDP_PORT}")
        print(f"   Navegá a la página de mensajes y volvé a la app para extraer.")

        return {
            'ok': True,
            'mensaje': 'Chrome abierto y logueado. Navegá a la página de mensajes de tu línea y después hacé clic en "Extraer mensajes".',
            'url': url_final
        }

    except Exception as e:
        print(f"❌ Error abriendo Chrome: {e}")
        cerrar_browser()
        return {
            'ok': False,
            'mensaje': f'Error al abrir Chrome: {str(e)}'
        }


# =================================================================
#  EXTRAER MENSAJES DE LA PÁGINA ACTUAL
# =================================================================

def extraer_pagina_actual() -> dict:
    """
    Conecta al Chrome abierto via CDP, lee el HTML de la página activa,
    y extrae los mensajes usando el parser HTML existente.

    Retorna dict con:
      - ok: bool
      - mensajes: list (mensajes extraídos)
      - url: str (URL de la página leída)
      - total: int (cantidad de mensajes)
      - mensaje: str (descripción del resultado)
    """
    if not PLAYWRIGHT_DISPONIBLE:
        return {
            'ok': False,
            'mensajes': [],
            'mensaje': 'Playwright no está instalado.'
        }

    try:
        # Conectar al Chrome via CDP
        pw = sync_playwright().start()
        try:
            browser = pw.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        except Exception as e:
            pw.stop()
            return {
                'ok': False,
                'mensajes': [],
                'mensaje': f'No se pudo conectar al Chrome. ¿Está abierto? Error: {str(e)}'
            }

        # Obtener la página activa
        if not browser.contexts or not browser.contexts[0].pages:
            pw.stop()
            return {
                'ok': False,
                'mensajes': [],
                'mensaje': 'No hay páginas abiertas en Chrome.'
            }

        context = browser.contexts[0]
        # Buscar la página con mensajes de SOFSE
        page = None
        for pg in context.pages:
            if 'sofse' in pg.url or 'novedades' in pg.url or 'mensajes' in pg.url:
                page = pg
                break

        # Si no encontramos una página SOFSE, usar la activa
        if not page:
            page = context.pages[-1]  # última pestaña

        url_actual = page.url
        print(f"📄 Leyendo página: {url_actual}")

        # Leer HTML
        html = page.content()

        # Extraer mensajes
        mensajes, fecha_antigua = extraer_mensajes_html(html)

        # Desconectar (sin cerrar el Chrome)
        pw.stop()

        if not mensajes:
            # Verificar si estamos en la página correcta
            if 'login.esp' in url_actual:
                return {
                    'ok': False,
                    'mensajes': [],
                    'url': url_actual,
                    'mensaje': 'Estás en la página de login. Logueate primero y navegá a los mensajes.'
                }
            return {
                'ok': False,
                'mensajes': [],
                'url': url_actual,
                'total': 0,
                'mensaje': f'No se encontraron mensajes en {url_actual}. Asegurate de estar en la página de mensajes.'
            }

        print(f"✅ {len(mensajes)} mensajes extraídos de {url_actual}")

        return {
            'ok': True,
            'mensajes': mensajes,
            'url': url_actual,
            'total': len(mensajes),
            'mensaje': f'{len(mensajes)} mensajes encontrados.'
        }

    except Exception as e:
        print(f"❌ Error extrayendo: {e}")
        return {
            'ok': False,
            'mensajes': [],
            'mensaje': f'Error al leer la página: {str(e)}'
        }


# =================================================================
#  CERRAR BROWSER
# =================================================================

def cerrar_browser():
    """Cierra el Chrome abierto por Playwright."""
    global _playwright_instance, _browser
    try:
        if _browser:
            _browser.close()
    except Exception:
        pass
    _browser = None

    try:
        if _playwright_instance:
            _playwright_instance.stop()
    except Exception:
        pass
    _playwright_instance = None


# =================================================================
#  VERIFICAR ESTADO
# =================================================================

def browser_activo() -> bool:
    """Verifica si hay un Chrome abierto con debug port accesible."""
    if not PLAYWRIGHT_DISPONIBLE:
        return False
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        tiene_paginas = bool(browser.contexts and browser.contexts[0].pages)
        pw.stop()
        return tiene_paginas
    except Exception:
        return False


# =================================================================
#  CLI PARA TESTING
# =================================================================

if __name__ == '__main__':
    import getpass

    print("=" * 50)
    print("  SCRAPER HÍBRIDO — Test local")
    print("=" * 50)

    user = input("Usuario VPN: ").strip()
    pwd = getpass.getpass("Contraseña VPN: ")

    resultado = abrir_y_login(user, pwd)
    print(f"\nResultado login: {resultado}")

    if resultado['ok']:
        input("\n▶️  Navegá a los mensajes en Chrome y presioná ENTER acá...")

        resultado2 = extraer_pagina_actual()
        print(f"\nResultado extracción: {resultado2['mensaje']}")
        if resultado2['ok']:
            print(f"Total mensajes: {resultado2['total']}")
            for m in resultado2['mensajes'][:3]:
                print(f"  - #{m.get('numero_mensaje', '?')}: {m.get('contenido', '')[:80]}...")

        input("\n▶️  Presioná ENTER para cerrar Chrome...")
        cerrar_browser()
