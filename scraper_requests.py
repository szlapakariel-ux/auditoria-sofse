"""
scraper_requests.py — Scraper SOFSE sin Playwright
====================================================
Usa requests + BeautifulSoup para loguear al VPN y extraer mensajes.
No requiere navegador, funciona en Render.

USO desde código:
    from scraper_requests import scrape_san_martin, ScraperLoginError, ScraperError
    mensajes = scrape_san_martin('mi_usuario', 'mi_pass', fecha_inicio, fecha_fin)

USO desde terminal (para testing):
    python scraper_requests.py --usuario mi_usuario --password mi_pass --inicio 24/02/2026
"""

import re
import sys
import json
import time
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlencode

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =================================================================
#  CONFIGURACIÓN
# =================================================================

URL_LOGIN        = "https://portalvpn.sofse.gob.ar/global-protect/login.esp"
URL_BASE         = "https://portalvpn.sofse.gob.ar/https/novedades.sofse.gob.ar"
URL_MENSAJES     = f"{URL_BASE}/mensajes"
URL_SET_AREA     = f"{URL_BASE}/areas/set_area"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9',
}

LINEAS = {
    "roca":         {"id": 23,  "nombre": "Línea Roca"},
    "belgrano_sur": {"id": 107, "nombre": "Línea Belgrano Sur"},
    "san_martin":   {"id": 555, "nombre": "Línea San Martín"},
    "mitre":        {"id": 556, "nombre": "Línea Mitre"},
    "sarmiento":    {"id": 557, "nombre": "Línea Sarmiento"},
    "costa":        {"id": 558, "nombre": "Tren de la Costa"},
}


# =================================================================
#  EXCEPCIONES
# =================================================================

class ScraperLoginError(Exception):
    """Credenciales VPN incorrectas o portal inaccesible"""
    pass

class ScraperError(Exception):
    """Error general durante el scraping"""
    pass


# =================================================================
#  EXTRACCIÓN DE MENSAJES DESDE HTML
#  (copiado de scraper_vpn.py para no depender de Playwright)
# =================================================================

def extraer_mensajes_html(html, fecha_inicio=None, fecha_fin=None):
    """
    Extrae todos los campos de los panel-mensaje del HTML.
    Retorna (lista_mensajes, fecha_mas_antigua_encontrada_en_esta_pagina)
    """
    soup = BeautifulSoup(html, 'html.parser')
    mensajes = []
    fecha_mas_antigua = None

    paneles = soup.find_all('div', class_='panel-mensaje')

    for panel in paneles:
        try:
            id_mensaje = panel.get('data-id_mensaje', '')

            titulo = panel.find('h3', class_='panel-title')
            titulo_txt = titulo.get_text(strip=True) if titulo else ''

            fecha_str = hora_str = fecha_hora = ''
            fecha_obj = None

            match_fh = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})', titulo_txt)
            if match_fh:
                fecha_str = match_fh.group(1)
                hora_str  = match_fh.group(2)
                fecha_hora = f"{fecha_str} {hora_str}"
                try:
                    fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                    if fecha_mas_antigua is None or fecha_obj < fecha_mas_antigua:
                        fecha_mas_antigua = fecha_obj
                except Exception:
                    pass

            if fecha_inicio and fecha_fin and fecha_obj:
                if fecha_obj.date() < fecha_inicio.date():
                    continue
                if fecha_obj.date() > fecha_fin.date():
                    continue

            numero_mensaje = ''
            m_num = re.search(r'#(\d+)', titulo_txt)
            if m_num:
                numero_mensaje = m_num.group(1)

            linea = ''
            span_linea = panel.find('span', class_='hidden-sm')
            if span_linea:
                linea = span_linea.get_text(strip=True)

            criticidad = ''
            lbl = panel.find('span', class_='label-criticidad')
            if lbl:
                criticidad = lbl.get_text(strip=True)

            tipificacion = estado_msg = ''
            inputs = panel.find_all('input', class_='form-control')
            for inp in inputs:
                val = inp.get('value', '')
                if any(k in val for k in ['DEMORA', 'CANCELACIÓN', 'REDUCIDO', 'SUSPENDIDO', 'CANCELACION']):
                    tipificacion = val
                if val in ['Nuevo', 'Modificación', 'Baja', 'Modificacion']:
                    estado_msg = val

            contenido = ''
            textarea = panel.find('textarea', class_='form-control')
            if textarea:
                contenido = textarea.get_text(strip=True)

            operador = ''
            div_op = panel.find('div', style=lambda x: x and 'font-size: 11px' in x)
            if div_op:
                operador = div_op.get_text(strip=True).replace('Operador: ', '').strip()

            grupos = []
            sel_grupos = panel.find('select', class_='selector-js')
            if sel_grupos:
                for opt in sel_grupos.find_all('option', selected=True):
                    grupos.append(opt.get_text(strip=True))

            estado_sms = estado_email = ''
            for badge in panel.find_all('span', class_='badge'):
                txt = badge.get_text(strip=True)
                if 'SMS' in txt.upper():
                    estado_sms = 'Enviado' if 'enviado' in txt.lower() else 'Pendiente'
                if 'MAIL' in txt.upper():
                    estado_email = 'Enviado' if 'enviado' in txt.lower() else 'Pendiente'

            mensajes.append({
                "id_mensaje":     id_mensaje,
                "numero_mensaje": numero_mensaje,
                "fecha":          fecha_str,
                "hora":           hora_str,
                "fecha_hora":     fecha_hora,
                "linea":          linea,
                "criticidad":     criticidad,
                "tipificacion":   tipificacion,
                "estado":         estado_msg,
                "contenido":      contenido,
                "operador":       operador,
                "grupos":         grupos,
                "estado_sms":     estado_sms,
                "estado_email":   estado_email,
            })

        except Exception:
            continue

    return mensajes, fecha_mas_antigua


# =================================================================
#  LOGIN AL VPN
# =================================================================

def login_vpn(vpn_user: str, vpn_password: str) -> requests.Session:
    """
    Loguea al portal GlobalProtect VPN con usuario y contraseña.
    Retorna una requests.Session autenticada.
    Lanza ScraperLoginError si falla.
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False  # El VPN usa certificados internos

    try:
        # Paso 1: GET login page para obtener CSRF token y cookies iniciales
        r = session.get(URL_LOGIN, timeout=20)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, 'html.parser')

        # Extraer CSRF token
        csrf_input = soup.find('input', {'name': 'csrf-token'})
        csrf_token = csrf_input['value'] if csrf_input else ''

        # Extraer otros campos ocultos del formulario
        form_data = {
            'prot':       '3',
            'server':     '',
            'inputStr':   '',
            'action':     'getsoftware',
            'csrf-token': csrf_token,
            'user':       vpn_user,
            'passwd':     vpn_password,
            'ok':         'Log In',
        }

        # Paso 2: POST con credenciales
        r2 = session.post(URL_LOGIN, data=form_data, timeout=30, allow_redirects=True)
        r2.raise_for_status()

        # Verificar si el login fue exitoso
        # Si falla, el portal vuelve a mostrar el form de login
        if 'passwd' in r2.text and 'Log In' in r2.text:
            # Intentar detectar mensaje de error específico
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            error_div = soup2.find('div', class_='error') or soup2.find('span', class_='error')
            error_msg = error_div.get_text(strip=True) if error_div else 'Credenciales incorrectas'
            raise ScraperLoginError(error_msg)

        print(f"✅ Login VPN exitoso para '{vpn_user}'")
        return session

    except ScraperLoginError:
        raise
    except requests.exceptions.ConnectionError:
        raise ScraperLoginError("No se pudo conectar al portal VPN. Verificá tu conexión a internet.")
    except requests.exceptions.Timeout:
        raise ScraperLoginError("El portal VPN no respondió (timeout). Intentá de nuevo.")
    except Exception as e:
        raise ScraperLoginError(f"Error inesperado al conectar al VPN: {e}")


# =================================================================
#  CAMBIAR ÁREA / LÍNEA
# =================================================================

def set_area(session: requests.Session, area_id: int) -> bool:
    """Cambia el área activa (línea) en el sistema SOFSE."""
    try:
        url = f"{URL_SET_AREA}/{area_id}"
        r = session.get(url, timeout=20, allow_redirects=True)
        return r.status_code < 400
    except Exception as e:
        print(f"⚠️  Error cambiando área: {e}")
        return False


# =================================================================
#  OBTENER PÁGINA DE MENSAJES CON FILTRO DE FECHA
# =================================================================

def get_pagina_mensajes(session: requests.Session, fecha_inicio: datetime,
                         pagina_url: str = None) -> tuple:
    """
    Obtiene una página de mensajes con filtro de fecha aplicado.
    En la primera página aplica el filtro via POST.
    Para páginas subsiguientes usa la URL de paginación.

    Retorna (html, next_url)
    - html: contenido HTML de la página
    - next_url: URL de la siguiente página, o None si no hay más
    """
    try:
        if pagina_url:
            # Página 2, 3, etc. — navegar directamente
            r = session.get(pagina_url, timeout=30)
        else:
            # Primera página — obtener el form y aplicar filtro
            r = session.get(URL_MENSAJES, timeout=30)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, 'html.parser')

            # Extraer campos ocultos del form de filtros
            form_data = {}
            form = soup.find('form')
            if form:
                for inp in form.find_all('input', type='hidden'):
                    name = inp.get('name', '')
                    val  = inp.get('value', '')
                    if name:
                        form_data[name] = val

            # Agregar filtro de fecha: campo="Fecha", operador="Mayor o igual"
            # El form usa un array de filtros: filtros[0][campo], filtros[0][op], filtros[0][valor]
            # Intentamos con la estructura más común de Rails/SOFSE
            form_data.update({
                'filtros[0][campo]':   'fecha',
                'filtros[0][op]':      'gte',
                'filtros[0][valor]':   fecha_inicio.strftime('%d/%m/%Y'),
                'buscar':              '1',
            })

            # Intentar POST del filtro
            action_url = form.get('action', URL_MENSAJES) if form else URL_MENSAJES
            if action_url and not action_url.startswith('http'):
                action_url = urljoin(URL_BASE, action_url)

            r = session.post(action_url or URL_MENSAJES, data=form_data, timeout=30)

        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')

        # Buscar link de siguiente página
        next_url = None
        next_link = soup.find('a', rel='next')
        if not next_link:
            # Buscar en paginación Bootstrap: li.next:not(.disabled) > a
            li_next = soup.find('li', class_='next')
            if li_next and 'disabled' not in (li_next.get('class') or []):
                next_link = li_next.find('a')

        if next_link and next_link.get('href'):
            href = next_link['href']
            if href.startswith('http'):
                next_url = href
            else:
                next_url = urljoin(URL_MENSAJES, href)

        return html, next_url

    except Exception as e:
        raise ScraperError(f"Error obteniendo mensajes: {e}")


# =================================================================
#  SCRAPER PRINCIPAL DE UNA LÍNEA
# =================================================================

def scrape_linea(vpn_user: str, vpn_password: str,
                 linea_key: str, fecha_inicio: datetime, fecha_fin: datetime,
                 max_paginas: int = 10) -> list:
    """
    Scrapea todos los mensajes de una línea en el rango de fechas indicado.
    Hace login, cambia área, y pagina hasta alcanzar la fecha límite.
    """
    if linea_key not in LINEAS:
        raise ScraperError(f"Línea '{linea_key}' no reconocida. Opciones: {list(LINEAS.keys())}")

    linea_info = LINEAS[linea_key]
    print(f"\n{'='*50}")
    print(f"📍 {linea_info['nombre']}")
    print(f"   Rango: {fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}")
    print(f"{'='*50}")

    # Login
    session = login_vpn(vpn_user, vpn_password)

    # Cambiar área
    if not set_area(session, linea_info['id']):
        raise ScraperError(f"No se pudo cambiar al área {linea_info['nombre']}")

    time.sleep(0.5)

    # Paginar
    todos = []
    pagina = 1
    next_url = None
    parar = False

    while not parar and pagina <= max_paginas:
        print(f"   📄 Página {pagina}...", end=' ', flush=True)

        if pagina == 1:
            html, next_url = get_pagina_mensajes(session, fecha_inicio)
        else:
            html, next_url = get_pagina_mensajes(session, fecha_inicio, pagina_url=next_url)

        # Extraer SIN filtro para trackear fecha más antigua
        _, fecha_antigua = extraer_mensajes_html(html)
        # Extraer CON filtro para quedarnos solo con el rango
        mensajes_pag, _ = extraer_mensajes_html(html, fecha_inicio, fecha_fin)

        print(f"{len(mensajes_pag)} mensajes", end='')

        if fecha_antigua:
            print(f" | más antiguo: {fecha_antigua.strftime('%d/%m/%Y')}", end='')
            if fecha_antigua.date() < fecha_inicio.date():
                parar = True
                print(" ✅ alcanzó fecha límite")
            else:
                print()
        else:
            print()
            if not mensajes_pag:
                print(f"   ⚠️  Sin mensajes en página {pagina}")
                break

        todos.extend(mensajes_pag)

        if parar or not next_url:
            if not parar:
                print(f"   ⏹️  Sin más páginas.")
            break

        pagina += 1
        time.sleep(0.3)  # Cortesía al servidor

    # Deduplicar
    vistos = set()
    unicos = []
    for m in todos:
        key = m.get('id_mensaje') or m.get('numero_mensaje')
        if key and key not in vistos:
            vistos.add(key)
            unicos.append(m)
        elif not key:
            unicos.append(m)

    # Asegurar linea correcta
    for m in unicos:
        if not m.get('linea'):
            m['linea'] = linea_info['nombre']

    print(f"   ✅ TOTAL {linea_info['nombre']}: {len(unicos)} mensajes únicos")
    return unicos


# =================================================================
#  FUNCIÓN PRINCIPAL PARA SAN MARTÍN (usada por el backend)
# =================================================================

def scrape_san_martin(vpn_user: str, vpn_password: str,
                      fecha_inicio: datetime, fecha_fin: datetime) -> list:
    """
    Scrapea mensajes de la Línea San Martín en el rango de fechas.
    Usada por el endpoint POST /api/scraping/san-martin del backend.

    Retorna lista de dicts con campos:
        id_mensaje, numero_mensaje, fecha, hora, fecha_hora,
        linea, criticidad, tipificacion, estado, contenido,
        operador, grupos, estado_sms, estado_email
    """
    return scrape_linea(
        vpn_user=vpn_user,
        vpn_password=vpn_password,
        linea_key='san_martin',
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


# =================================================================
#  CLI PARA TESTING LOCAL
# =================================================================

if __name__ == '__main__':
    # UTF-8 en Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description='Scraper SOFSE via requests (sin browser)')
    parser.add_argument('--usuario',  required=True, help='Usuario VPN')
    parser.add_argument('--password', required=True, help='Contraseña VPN')
    parser.add_argument('--linea',    default='san_martin',
                        help='Línea a scrapear (default: san_martin)')
    parser.add_argument('--inicio',   help='Fecha inicio DD/MM/YYYY (default: hoy)')
    parser.add_argument('--fin',      help='Fecha fin DD/MM/YYYY (default: hoy)')
    args = parser.parse_args()

    hoy = datetime.now()
    fecha_inicio = datetime.strptime(args.inicio, '%d/%m/%Y') if args.inicio else hoy
    fecha_fin    = datetime.strptime(args.fin,    '%d/%m/%Y') if args.fin    else hoy

    try:
        mensajes = scrape_linea(
            vpn_user=args.usuario,
            vpn_password=args.password,
            linea_key=args.linea,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        if mensajes:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            salida = f"mensajes_requests_{ts}.json"
            with open(salida, 'w', encoding='utf-8') as f:
                json.dump(mensajes, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Guardado: {salida} ({len(mensajes)} mensajes)")
            print("\n📋 Preview primer mensaje:")
            print(json.dumps(mensajes[0], ensure_ascii=False, indent=2))
        else:
            print("\n⚠️  No se encontraron mensajes en el rango indicado.")

    except ScraperLoginError as e:
        print(f"\n❌ Error de login: {e}")
        sys.exit(1)
    except ScraperError as e:
        print(f"\n❌ Error de scraping: {e}")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n❌ Error inesperado: {e}")
        traceback.print_exc()
        sys.exit(1)
