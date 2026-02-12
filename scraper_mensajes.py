"""
Script para extraer mensajes desde la página de SOFSE usando web scraping
Autor: Ariel - SOFSE Yunex/Constitución
Fecha: Diciembre 2024
Versión 3 - Optimizada con filtro por fecha y todas las líneas
"""

import sys
import io

# Forzar UTF-8 en consola Windows para evitar error con emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import time

# =================================================================
#                         CONFIGURACIÓN
# =================================================================
URL_BASE = "https://novedades.sofse.gob.ar"
URL_MENSAJES = "https://novedades.sofse.gob.ar/mensajes"

AREAS_MENSAJES = {
    23: "Línea Roca",
    107: "Línea Belgrano Sur",
    555: "Línea San Martín",
    556: "Línea Mitre",
    557: "Línea Sarmiento",
    558: "Tren de la Costa"
}

# =================================================================
#                         FUNCIONES
# =================================================================


def extraer_mensajes_de_html(html_content, fecha_inicio=None, fecha_fin=None, limit=None):
    """
    Extrae los datos de mensajes desde el HTML
    Si se pasan fechas, filtra por rango [fecha_inicio, fecha_fin] (objetos datetime)
    Retorna lista de mensajes y la fecha del mensaje más antiguo encontrado (para saber si seguir scrolleando)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    mensajes = []
    fecha_mas_antigua = None
    
    # Buscar todos los paneles de mensajes
    paneles = soup.find_all('div', class_='panel-mensaje')
    
    # print(f"\n📊 Analizando {len(paneles)} mensajes en HTML...")
    
    for panel in paneles:
        if limit and len(mensajes) >= limit:
            break
        try:
            # Extraer ID del mensaje
            id_mensaje = panel.get('data-id_mensaje')
            
            # Extraer título (fecha, hora y número)
            titulo = panel.find('h3', class_='panel-title')
            titulo_texto = titulo.get_text(strip=True) if titulo else ""
            
            # Parsear fecha
            fecha_obj = None
            if titulo_texto:
                match_fecha_hora = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})', titulo_texto)
                if match_fecha_hora:
                    fecha_str = match_fecha_hora.group(1)
                    hora_str = match_fecha_hora.group(2)
                    try:
                        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                        # Actualizar fecha más antigua vista
                        if fecha_mas_antigua is None or fecha_obj < fecha_mas_antigua:
                            fecha_mas_antigua = fecha_obj
                    except:
                        pass

            # Filtrar por rango de fechas
            if fecha_inicio and fecha_fin and fecha_obj:
                # Normalizar horas para comparar solo fechas
                f_msg = fecha_obj.date()
                f_ini = fecha_inicio.date()
                f_fin = fecha_fin.date()
                
                if f_msg < f_ini:
                    # Mensaje más viejo que el inicio, lo ignoramos (y nos sirve de señal para parar scroll)
                    continue
                if f_msg > f_fin:
                    # Mensaje futuro (raro, pero posible), lo ignoramos
                    continue
            
            # ... (Resto de la extracción igual) ...
            
            # Parsear datos restantes
            fecha = fecha_str if 'fecha_str' in locals() else ""
            hora = hora_str if 'hora_str' in locals() else ""
            fecha_hora = f"{fecha} {hora}"
            
            # Buscar número de mensaje
            numero_mensaje = ""
            match_numero = re.search(r'#(\d+)', titulo_texto)
            if match_numero:
                 numero_mensaje = match_numero.group(1)

            # Extraer línea
            linea = ""
            span_linea = panel.find('span', class_='hidden-sm')
            if span_linea:
                linea = span_linea.get_text(strip=True)
            
            # Extraer criticidad
            criticidad = ""
            label_criticidad = panel.find('span', class_='label-criticidad')
            if label_criticidad:
                criticidad = label_criticidad.get_text(strip=True)
            
            # Extraer tipificación
            tipificacion = ""
            inputs = panel.find_all('input', class_='form-control')
            for input_field in inputs:
                value = input_field.get('value', '')
                if 'DEMORA' in value or 'CANCELACIÓN' in value or 'REDUCIDO' in value:
                    tipificacion = value
                    break
            
            # Extraer estado
            estado = ""
            for input_field in inputs:
                value = input_field.get('value', '')
                if value in ['Nuevo', 'Modificación', 'Baja']:
                    estado = value
                    break
            
            # Extraer contenido
            contenido = ""
            textarea = panel.find('textarea', class_='form-control')
            if textarea:
                contenido = textarea.get_text(strip=True)
            
            # Extraer operador
            operador = ""
            div_operador = panel.find('div', style=lambda x: x and 'font-size: 11px' in x)
            if div_operador:
                operador = div_operador.get_text(strip=True).replace('Operador: ', '')
            
            # Extraer grupos
            grupos = []
            select_grupos = panel.find('select', class_='selector-js')
            if select_grupos:
                for option in select_grupos.find_all('option', selected=True):
                    grupos.append(option.get_text(strip=True))
            
            # Extraer estado SMS y Email
            estado_sms = ""
            estado_email = ""
            badges = panel.find_all('span', class_='badge')
            for badge in badges:
                texto = badge.get_text(strip=True)
                if 'SMS' in texto.upper():
                    if 'Enviado' in texto or 'ENVIADO' in texto: estado_sms = "Enviado"
                    elif 'Pendiente' in texto or 'PENDIENTE' in texto: estado_sms = "Pendiente"
                if 'EMAIL' in texto.upper() or 'MAIL' in texto.upper():
                    if 'Enviado' in texto or 'ENVIADO' in texto: estado_email = "Enviado"
                    elif 'Pendiente' in texto or 'PENDIENTE' in texto: estado_email = "Pendiente"
            
            mensaje = {
                "id_mensaje": id_mensaje,
                "numero_mensaje": numero_mensaje,
                "fecha": fecha,
                "hora": hora,
                "fecha_hora": fecha_hora,
                "linea": linea,
                "criticidad": criticidad,
                "tipificacion": tipificacion,
                "estado": estado,
                "contenido": contenido,
                "operador": operador,
                "grupos": grupos,
                "estado_sms": estado_sms,
                "estado_email": estado_email
            }
            
            mensajes.append(mensaje)
            
        except Exception as e:
            # print(f"❌ Error procesando mensaje individual: {e}")
            continue
    
    return mensajes, fecha_mas_antigua


def obtener_mensajes_linea(page, area_id, nombre_linea, fecha_inicio=None, fecha_fin=None):
    """
    Obtiene mensajes de una línea específica filtrados por rango de fechas [inicio, fin]
    Realiza SCROLL automático hasta encontrar mensajes anteriores a fecha_inicio.
    """
    print(f"\n➡️ {nombre_linea}...")
    
    # Si no se pasan fechas, usar default (hoy)
    if not fecha_inicio:
        fecha_inicio = datetime.now()
    if not fecha_fin:
        fecha_fin = datetime.now()

    # Cambiar a la línea específica
    try:
        url_set = f"{URL_BASE}/areas/set_area/{area_id}"
        
        # Intentar navegar
        try:
            page.goto(url_set, wait_until="domcontentloaded", timeout=30000)
        except Exception as nav_error:
            if "login" in page.url.lower():
                print(f"   ⚠️ Sesión expirada. Reloguear...")
                # Lógica simple de espera
                page.wait_for_timeout(60000)
                page.goto(url_set, wait_until="domcontentloaded", timeout=30000)
            else:
                raise nav_error
        
        time.sleep(0.5)
        page.goto(URL_MENSAJES, wait_until="domcontentloaded", timeout=30000)
        time.sleep(1)
        page.wait_for_selector('.panel-mensaje', timeout=10000)
        
        # SCROLL INFINITO HASTA FECHA
        print(f"   📜 Scrolleando hasta encontrar mensajes del {fecha_inicio.strftime('%d/%m/%Y')}...")
        
        mensajes_recolectados = []
        fecha_mas_antigua_html = datetime.now()
        
        max_scrolls = 200 # Límite de seguridad
        scrolls = 0
        previous_height = 0
        
        while scrolls < max_scrolls:
            # Obtener contenido actual
            html_content = page.content()
            mensajes_temp, fecha_mas_antigua_html = extraer_mensajes_de_html(html_content, None, None, limit=None) # Extraer todo para ver fechas
            
            # Verificar fecha más antigua visible
            if fecha_mas_antigua_html:
                # print(f"      [Scroll {scrolls}] Más antiguo visible: {fecha_mas_antigua_html.strftime('%d/%m/%Y')}")
                if fecha_mas_antigua_html.date() < fecha_inicio.date():
                    print("   ✅ Se alcanzaron mensajes anteriores a la fecha de inicio.")
                    break
            
            # Scroll
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000) # Esperar carga dinámica
            
            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                # Fin de página
                print("   ⚠️ Fin de página alcanzado.")
                break
            previous_height = current_height
            scrolls += 1
            
            if scrolls % 10 == 0:
                print(f"      ... scrolleando ({scrolls} veces)")

        # Extracción FINAL con filtro
        html_content = page.content()
        mensajes, _ = extraer_mensajes_de_html(html_content, fecha_inicio, fecha_fin)
        
        # Agregar info de línea y area
        for m in mensajes:
            m['linea'] = nombre_linea
            m['area_id'] = area_id
        
        print(f"   ✅ Recolectados: {len(mensajes)} mensajes en el rango solicitado.")
        return mensajes
        
    except Exception as e:
        print(f"   ❌ Error en línea {nombre_linea}: {e}")
        return []



# =================================================================
#                         CONFIGURACIÓN DE CONEXIÓN
# =================================================================

def configurar_urls(usar_vpn=False):
    """Configura las URLs base según el modo de conexión"""
    global URL_BASE, URL_MENSAJES, URL_VPN_LOGIN
    
    if usar_vpn:
        print("🔒 MODO VPN ACTIVADO: Usando Login GlobalProtect")
        # URL CORRECTA PROVISTA POR USUARIO (Producción):
        URL_BASE = "https://portalvpn.sofse.gob.ar/https/novedades.sofse.gob.ar"
        URL_MENSAJES = "https://portalvpn.sofse.gob.ar/https/novedades.sofse.gob.ar/mensajes/" 
        URL_VPN_LOGIN = "https://portalvpn.sofse.gob.ar/global-protect/login.esp?token=1"
    else:
        print("🌐 MODO DIRECTO: Usando novedades.sofse.gob.ar")
        URL_BASE = "https://novedades.sofse.gob.ar"
        URL_MENSAJES = "https://novedades.sofse.gob.ar/mensajes"
        URL_VPN_LOGIN = None

def obtener_mensajes_con_playwright(fecha_inicio=None, fecha_fin=None, linea_id_filtro=None, manual_mode=False):
    """
    Usa Playwright para manejar el login y obtener el HTML de TODAS las líneas
    """
    print("=" * 60)
    print("EXTRAYENDO MENSAJES DE SOFSE - TODAS LAS LÍNEAS")
    print(f"📅 Rango: {fecha_inicio} - {fecha_fin}")
    print("=" * 60)
    
    # Soporte para argumentos de línea de comandos (para automatización)
    import sys
    import os
    # Determinar si usar VPN (basado en flags externos o logica previa)
    # Por defecto asumimos VPN si manual mode está activo para este caso de uso
    usar_vpn_flag = "--vpn" in sys.argv
    configurar_urls(usar_vpn=usar_vpn_flag) 

    # --- INICIO LOOP PRINCIPAL DE PERSISTENCIA (PHOENIX MODE) ---
    while True:
        try:
            with sync_playwright() as p:
                # Configurar Proxy si existe
                proxy_settings = None
                try:
                    import proxy_config
                    if os.path.exists("proxy_config.py"):
                        proxy_url = proxy_config.get_proxy_url()
                        if proxy_url:
                            proxy_settings = {"server": proxy_url}
                except: pass

                # Lanzar contexto persistente
                user_data_dir = "sesion_chrome"
                print("\n🚀 Lanzando nuevo navegador...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    proxy=proxy_settings,
                    ignore_https_errors=True,
                    viewport={"width": 1280, "height": 720}
                )
                
                # Intentar obtener página existente o crear nueva
                page = context.pages[0] if context.pages else context.new_page()
                
                # Login Logic (Siempre navegar al inicio para evitar about:blank)
                try:
                    if usar_vpn_flag and URL_VPN_LOGIN:
                        print(f"🔐 Navegando a Login VPN: {URL_VPN_LOGIN}")
                        page.goto(URL_VPN_LOGIN, timeout=60000, wait_until="domcontentloaded")
                    else:
                        page.goto(URL_MENSAJES, timeout=60000, wait_until="commit")
                    page.wait_for_timeout(3000)
                except: pass
                
                # Verificar Login (Reutilizar lógica existente o simplificar)
                if "login" in page.url.lower():
                        print("🔐 Login requerido. Esperando...")
                        # Esperar login... (Loop de espera)
                        for _ in range(60):
                            if "login" not in page.url.lower(): break
                            time.sleep(2)

                # Scrapear
                todos_mensajes = []
                
                # --- MODO MANUAL (ESPERA ACTIVA) ---
                if manual_mode:
                    print("\n" + "=" * 60)
                    print("✋ MODO MANUAL: INTERACCIÓN REQUERIDA")
                    print("1. LOGIN: Inicia sesión en GlobalProtect (VPN).")
                    print("2. NAVEGAR: Una vez conectado, entrá a:")
                    print(f"   {URL_MENSAJES}")
                    print("   (O hacé clic en el ícono correspondiente en el portal)")
                    print("3. SCROLL: Bajá hasta el final para cargar todo.")
                    print("=" * 60)
                    
                    while True:
                        try:
                            opcion = input("\n[OPCIONES]\n 1. Ir a URL de Mensajes (Producción)\n 2. Usar pestaña actual\n 3. Reiniciar Navegador\n 4. Salir\n\n👉 Elegí una opción (1-4): ")
                            
                            if opcion.strip() == '4' or opcion.strip().lower() in ['exit', 'salir']:
                                print("👋 Cerrando todo...")
                                context.close()
                                return []

                            if opcion.strip() == '3':
                                print("🔄 Reiniciando navegador...")
                                break # Rompe el while interno, sale del with, y el while externo reinicia

                            if opcion.strip() == '1':
                                # Usar la URL configurada oficialmente
                                target_url = URL_MENSAJES
                                print(f"🚀 Navegando a: {target_url}...")
                                # Asegurar que usamos la página correcta
                                page = context.pages[0]
                                try:
                                    page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                                    print("✅ Navegación completada. Por favor hace SCROLL si es necesario.")
                                except Exception as e:
                                    print(f"⚠️ Alerta de navegación: {e}")
                            
                            elif opcion.strip() == '2':
                                 print("🔄 Usando pestaña actual...")
                                 page = context.pages[0]
                            
                            else:
                                print("❌ Opción inválida.")
                                continue

                            # Intentar extraer de la página actual + Paginación
                            print("\n🕵️  Intentando extraer mensajes (y paginar)...")
                            
                            mensajes_acumulados = []
                            pagina_actual = 1
                            
                            while True:
                                print(f"   📖 Procesando página {pagina_actual}...")
                                page.wait_for_timeout(2000) # Esperar renderizado tabla
                                html_content = page.content()
                                
                                mensajes, _ = extraer_mensajes_de_html(html_content, fecha_inicio, fecha_fin)
                                
                                # Si encontramos mensajes, los sumamos
                                if mensajes:
                                    # Evitar duplicados si la página no cambió (check simple por ID)
                                    nuevos = [m for m in mensajes if m not in mensajes_acumulados]
                                    if nuevos:
                                        mensajes_acumulados.extend(nuevos)
                                        print(f"      ✅ +{len(nuevos)} mensajes recolectados. (Subtotal: {len(mensajes_acumulados)})")
                                    else:
                                        print("      ⚠️ Página escaneada sin mensajes nuevos (posible fin o duplicado).")
                                else:
                                    print("      ⚠️ No se extrajeron mensajes de esta vista.")
                                
                                # BUSCAR PAGINACIÓN
                                # El botón suele ser un link <a> con texto "»" o title "Siguiente"
                                # En la foto se ve: [1] [2] [3] [»] [Últimas]
                                try:
                                    # Estrategia 1: Texto exacto
                                    next_btn = page.get_by_role("link", name="»", exact=True)
                                    
                                    # Validar visibilidad
                                    if next_btn.count() > 0 and next_btn.is_visible():
                                        # A veces el botón está deshabilitado si es el final
                                        parent_li = next_btn.locator("..") # Subir al <li>
                                        if "disabled" in (parent_li.get_attribute("class") or ""):
                                            print("      ⏹️ Botón 'Siguiente' deshabilitado. Fin.")
                                            break
                                            
                                        print("      ➡️ Clic en '»' para siguiente página...")
                                        next_btn.click()
                                        pagina_actual += 1
                                        time.sleep(2) # Espera breve post-click
                                    else:
                                        print("      ⏹️ No se ve botón '»' de siguiente. Fin del recorrido.")
                                        break
                                        
                                except Exception as e:
                                    print(f"      ⚠️ No se pudo paginar más: {e}")
                                    break

                            # Fin del while de paginación
                            if mensajes_acumulados:
                                cantidad = len(mensajes_acumulados)
                                print(f"\n🎉 ¡ÉXITO GLOBAL! Se encontraron {cantidad} mensajes en {pagina_actual} páginas.")
                                
                                # Agregar metadata
                                for m in mensajes_acumulados:
                                    m['linea'] = "Línea San Martín (Manual)" 
                                    m['area_id'] = 555
                                    
                                confirm = input("💾 ¿Guardar TODO el lote? (s/n): ")
                                if confirm.lower() == 's':
                                    context.close()
                                    return mensajes_acumulados
                                else:
                                    print("🔄 Descartados. Volviendo al menú...")
                            else:
                                print("\n⚠️  No se encontraron mensajes en ninguna página.")
                                print("   - Asegurate de estar en la URL correcta.")
                            
                        except KeyboardInterrupt:
                            return []
                        except Exception as e:
                            print(f"❌ Error en el loop manual: {e}")
                            if "closed" in str(e).lower():
                                print("🔄 Detectado cierre de conexión. Reiniciando navegador...")
                                break # Reinicia el navegador

                    # Si salimos del while interno con break, el context se cierra y se reinicia arriba
                    try: context.close()
                    except: pass
                
                else: 
                     # MODO AUTOMATICO
                     print("🤖 MODO AUTOMÁTICO: Extrayendo de todas las áreas...")
                     for area_id, nombre_linea in AREAS_MENSAJES.items():
                        if linea_id_filtro and area_id != linea_id_filtro:
                            continue
                            
                        mensajes = obtener_mensajes_linea(page, area_id, nombre_linea, fecha_inicio, fecha_fin)
                        todos_mensajes.extend(mensajes)
                        time.sleep(1)
                     
                     context.close()
                     return todos_mensajes
                     
        except Exception as crash_error:
            print(f"🔥 El navegador se cerró inesperadamente (`{crash_error}`). Reiniciando en 3 segundos...")
            time.sleep(3)
            # El while True reiniciará todo


# =================================================================
#                         EJECUCIÓN
# =================================================================

if __name__ == "__main__":
    try:
        # Soporte para rango de fechas
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--vpn', action='store_true', help='Usar modo VPN')
        parser.add_argument('--direct', action='store_true', help='Usar modo Directo')
        parser.add_argument('--inicio', type=str, help='Fecha inicio DD/MM/YYYY')
        parser.add_argument('--linea_id', type=int, help='ID de linea especifica (ej: 555 para San Martin)')
        parser.add_argument('--manual', action='store_true', help='Permite al usuario loguearse y navegar antes de extraer')
        args, unknown = parser.parse_known_args()

        if args.inicio:
            fecha_inicio = datetime.strptime(args.inicio, "%d/%m/%Y")
            fecha_fin = datetime.now()
            print(f"\n📅 MODO HISTÓRICO: {fecha_inicio.strftime('%d/%m/%Y')} -> {fecha_fin.strftime('%d/%m/%Y')}")
            if args.linea_id:
                print(f"🚄 Filtrando por Linea ID: {args.linea_id}")
            
            mensajes = obtener_mensajes_con_playwright(fecha_inicio, fecha_fin, args.linea_id, args.manual)
            
            nombre_archivo = f"mensajes_historico_{fecha_inicio.strftime('%Y%m%d')}_{datetime.now().strftime('%Y%m%d')}.json"
        else:
            # Modo Hoy (Default)
            fecha_hoy_obj = datetime.now()
            mensajes = obtener_mensajes_con_playwright(fecha_hoy_obj, fecha_hoy_obj)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"mensajes_sofse_hoy_{timestamp}.json"
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(mensajes, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO")
        print("=" * 60)
        print(f"\n📊 Total de mensajes extraídos: {len(mensajes)}")
        print(f"💾 Archivo guardado: {nombre_archivo}")
        
        # Resumen por línea
        print("\n📋 RESUMEN POR LÍNEA:")
        resumen = {}
        for m in mensajes:
            linea = m.get('linea', 'Sin línea')
            resumen[linea] = resumen.get(linea, 0) + 1
        
        for linea, cantidad in sorted(resumen.items()):
            print(f"   {linea}: {cantidad} mensajes")
        
        # Mostrar preview del primer mensaje
        if mensajes:
            print("\n" + "=" * 60)
            print("📋 PREVIEW DEL PRIMER MENSAJE:")
            print("=" * 60)
            print(json.dumps(mensajes[0], ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Evitar cierre inmediato en caso de error
        import sys
        if len(sys.argv) <= 1:
            input("\n⚠️ Proceso fallido. Presioná ENTER para cerrar...")
