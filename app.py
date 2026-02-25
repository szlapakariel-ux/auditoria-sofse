from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from gestor_tandas import GestorTandas
import validador_mensajes
import os
import json
import threading
import time
import urllib.request
from pathlib import Path
from datetime import timedelta, datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-super-secreta-cambiar-en-produccion')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('RENDER'))

# CORS: en producción el frontend está en el mismo dominio, no necesita CORS
# Dejamos localhost para desarrollo local + portalvpn para el bookmarklet
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:5000",
    os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000'),
    "https://portalvpn.sofse.gob.ar",
])

gestor = GestorTandas()

# ============================================
# KEEP-ALIVE PING (evita que Render duerma)
# ============================================
def keep_alive():
    """Hace ping al propio servicio cada 10 minutos para que Render no lo duerma"""
    url = os.environ.get('RENDER_EXTERNAL_URL')
    if not url:
        return  # Solo corre en Render, no en local
    
    health_url = f"{url}/health"
    while True:
        time.sleep(600)  # 10 minutos
        try:
            urllib.request.urlopen(health_url, timeout=10)
            print(f"🏓 Ping keep-alive OK → {health_url}")
        except Exception as e:
            print(f"⚠️ Ping keep-alive falló: {e}")

# Arrancar el ping en un hilo separado
ping_thread = threading.Thread(target=keep_alive, daemon=True)
ping_thread.start()

USUARIOS = {
    'ariel': {'password': 'ariel123', 'nombre': 'Ariel'},
    'patricia': {'password': 'patricia123', 'nombre': 'Patricia'},
    'diego': {'password': 'diego123', 'nombre': 'Diego'}
}

def cargar_todas_las_reglas():
    """Carga todas las reglas activas de todos los archivos"""
    todas = []
    rutas = [
        'configs/reglas/globales/personalizadas.json',
        'configs/reglas/globales/componentes.json',
        'configs/reglas/san_martin/personalizadas.json',
        'configs/reglas/roca/personalizadas.json',
        'configs/reglas/mitre/personalizadas.json',
        'configs/reglas/sarmiento/personalizadas.json',
        'configs/reglas/belgrano_sur/personalizadas.json',
        'configs/reglas/tren_de_la_costa/personalizadas.json',
    ]
    for ruta in rutas:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reglas = [r for r in data.get('reglas', []) if r.get('activa', True)]
                for r in reglas:
                    r['_archivo'] = ruta
                todas.extend(reglas)
    return todas


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = data.get('usuario', '').lower()
    password = data.get('password', '')
    if usuario in USUARIOS and USUARIOS[usuario]['password'] == password:
        session['usuario'] = usuario
        session['nombre'] = USUARIOS[usuario]['nombre']
        session.permanent = True
        return jsonify({'ok': True, 'nombre': USUARIOS[usuario]['nombre']})
    return jsonify({'ok': False, 'error': 'Incorrectos'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    if 'nombre' in session:
        gestor.liberar_mensajes(session['nombre'])
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/session', methods=['GET'])
def check_session():
    if 'nombre' in session:
        usuario = session['nombre']
        mensajes = gestor.obtener_mensajes_asignados(usuario)
        bloqueados = gestor.obtener_bloqueados(usuario)
        
        # DEDUPLICAR
        ids_vistos = set()
        bloqueados_unicos = []
        for m in bloqueados:
            if m['id'] not in ids_vistos:
                ids_vistos.add(m['id'])
                bloqueados_unicos.append(m)
        
        print(f"✅ Session check {usuario}: {len(mensajes)} asignados + {len(bloqueados_unicos)} bloqueados")
        
        return jsonify({
            'ok': True,
            'nombre': usuario,
            'mensajes': bloqueados_unicos + mensajes,
            'total_asignados': len(mensajes),
            'total_bloqueados': len(bloqueados_unicos)
        })
    return jsonify({'ok': False}), 401

@app.route('/api/lineas/disponibles', methods=['GET'])
def lineas_disponibles():
    conteo = gestor.contar_pendientes_por_linea()
    return jsonify({'ok': True, 'lineas': conteo})

@app.route('/api/seleccionar-linea', methods=['POST'])
def seleccionar_linea():
    if 'nombre' not in session:
        return jsonify({'ok': False}), 401
    
    data = request.get_json()
    linea = data.get('linea')
    usuario = session['nombre']
    
    # Obtener tanda normal (solo PENDIENTES)
    tanda = gestor.asignar_tanda(usuario, linea)
    
    # Obtener mensajes BLOQUEADOS para este usuario
    bloqueados = gestor.obtener_bloqueados(usuario)
    
    # DEDUPLICAR bloqueados por ID
    ids_vistos = set()
    bloqueados_unicos = []
    for m in bloqueados:
        if m['id'] not in ids_vistos:
            ids_vistos.add(m['id'])
            bloqueados_unicos.append(m)
    
    session['linea_actual'] = linea
    
    print(f"✅ {usuario} seleccionó {linea}: {len(tanda)} pendientes + {len(bloqueados_unicos)} bloqueados")
    
    return jsonify({
        'ok': True,
        'linea': linea,
        'mensajes': bloqueados_unicos + tanda,
        'total': len(tanda),
        'total_bloqueados': len(bloqueados_unicos)
    })

@app.route('/api/validar', methods=['POST'])
def validar_mensaje():
    if 'nombre' not in session:
        return jsonify({'ok': False}), 401
    
    data = request.get_json()
    print(f"🔍 DEBUG VALIDAR - Data recibida: {data}")
    mensaje_id = data.get('mensaje_id')
    accion = data.get('accion')
    comentario = data.get('comentario', '')
    print(f"🔍 DEBUG VALIDAR - mensaje_id={mensaje_id}, accion={accion}, comentario={comentario[:50] if comentario else 'N/A'}")
    
    # Buscar mensaje
    mensaje = next((m for m in gestor.mensajes if m['id'] == mensaje_id), None)
    if not mensaje:
        return jsonify({'ok': False}), 404
    
    if accion == 'ENVIAR':
        # Sistema acertó - enviar email según clasificación
        mensaje['estado'] = 'COMPLETADO'
        mensaje['procesado_por'] = session['nombre']
        mensaje['procesado_en'] = datetime.now().isoformat()
        mensaje['validado_como'] = 'CORRECTO'
        
        # TODO: Aquí llamar función que envía email al operador
        # enviar_email_operador(mensaje)
        
    elif accion in ['REPORTAR_ERROR', 'REPORTAR']:
        # Sistema se equivocó - derivar a Ariel
        mensaje['estado'] = 'DERIVADO_A_ARIEL'
        mensaje['derivado_por'] = session['nombre']
        mensaje['derivado_en'] = datetime.now().isoformat()
        mensaje['comentario_validador'] = comentario
        print(f"✅ Mensaje {mensaje_id} derivado a Ariel por {session['nombre']}")
        # NO se envía email al operador
    
    gestor._guardar_mensajes()
    
    # Contar mensajes restantes
    restantes = gestor.contar_asignados(session['nombre'])
    
    # Si no quedan, asignar nueva tanda
    nueva_tanda = []
    if restantes == 0:
        nueva_tanda = gestor.asignar_tanda(session['nombre'], session.get('linea_actual'))
    
    return jsonify({
        'ok': True,
        'restantes': restantes,
        'nueva_tanda': nueva_tanda
    })

@app.route('/api/errores', methods=['GET'])
def obtener_errores():
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403
    errores = [m for m in gestor.mensajes if m['estado'] == 'DERIVADO_A_ARIEL']
    return jsonify({'ok': True, 'errores': errores})

@app.route('/api/errores/desbloquear', methods=['POST'])
def desbloquear_mensaje():
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403
    data = request.get_json()
    mensaje = next((m for m in gestor.mensajes if m['id'] == data.get('mensaje_id')), None)
    if not mensaje:
        return jsonify({'ok': False}), 404
    mensaje['estado'] = 'PENDIENTE'
    gestor._guardar_mensajes()
    return jsonify({'ok': True})

@app.route('/api/errores/devolver', methods=['POST'])
def devolver_mensaje():
    """Ariel devuelve mensaje bloqueado a validador"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403
    
    data = request.get_json()
    mensaje_id = data.get('mensaje_id')
    explicacion = data.get('explicacion', '')
    
    mensaje = next((m for m in gestor.mensajes if m['id'] == mensaje_id), None)
    
    if not mensaje:
        return jsonify({'ok': False}), 404
    
    # Devolver a quien lo derivó originalmente
    validador_original = mensaje.get('derivado_por', 'Patricia')
    
    mensaje['estado'] = f'ASIGNADO_{validador_original.upper()}'
    mensaje['bloqueado'] = True
    mensaje['explicacion_ariel'] = explicacion
    mensaje['bloqueado_en'] = datetime.now().isoformat()
    
    gestor._guardar_mensajes()
    
    print(f"✅ Mensaje {mensaje_id} devuelto BLOQUEADO a {validador_original}")
    
    return jsonify({'ok': True})

@app.route('/api/reglas/verificar-conflictos', methods=['POST'])
def verificar_conflictos():
    """Verifica si una regla nueva tiene conflictos con existentes"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403
    
    data = request.get_json()
    regla_nueva = data.get('regla_nueva')
    
    # Cargar reglas existentes
    # Cargar reglas existentes
    linea = regla_nueva['linea']
    
    linea_carpeta = linea.lower().replace(' ', '_').replace('(', '').replace(')', '')
    mapa_carpetas = {
        'global': 'globales',
        'globales': 'globales',
        'línea_san_martín_manual': 'san_martin',
        'linea_san_martin_manual': 'san_martin',
    }
    carpeta = mapa_carpetas.get(linea_carpeta, linea_carpeta)
    
    # Verificar en ambas carpetas
    rutas_verificar = [
        f'configs/reglas/{carpeta}/personalizadas.json',
        'configs/reglas/globales/personalizadas.json',
    ]
    
    conflictos = []
    
    for ruta_reglas in rutas_verificar:
        if os.path.exists(ruta_reglas):
            with open(ruta_reglas, 'r', encoding='utf-8') as f:
                data_reglas = json.load(f)
                reglas_existentes = data_reglas.get('reglas', [])
            
            # Buscar conflictos
            for regla in reglas_existentes:
                # Conflicto: mismo patrón, acción diferente
                if regla.get('patron_detectado') == regla_nueva.get('patron_detectado'):
                    if regla.get('accion_sugerida') != regla_nueva.get('accion_sugerida'):
                        conflictos.append({
                            'tipo': 'CONTRADICCION',
                            'regla_existente_id': regla.get('id'),
                            'explicacion': f"Ya existe regla '{regla.get('patron_detectado')}' con acción '{regla.get('accion_sugerida')}' diferente a la nueva '{regla_nueva.get('accion_sugerida')}'"
                        })
                
                # Conflicto: regex muy similar
                if regla.get('regex_sugerido') == regla_nueva.get('regex_sugerido'):
                    conflictos.append({
                        'tipo': 'DUPLICACION',
                        'regla_existente_id': regla.get('id'),
                        'explicacion': f"Regex idéntico a regla existente '{regla.get('patron_detectado')}'"
                    })
    
    return jsonify({
        'ok': True,
        'conflictos': conflictos
    })

@app.route('/api/reglas/buscar', methods=['POST'])
def buscar_regla():
    """Busca reglas existentes relacionadas al patrón"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403
    
    data = request.get_json()
    patron = data.get('patron', '').lower()
    linea = data.get('linea', '').lower().replace(' ', '_').replace('(', '').replace(')', '')
    
    # Identificar carpeta de línea
    linea_norm = linea.lower().replace('linea_', '').replace('línea_', '').replace(' ', '_').replace('(', '').replace(')', '')
    
    mapa_carpetas = {
        'san_martin_manual': 'san_martin',
        'san_martin': 'san_martin',
        'roca': 'roca',
        'mitre': 'mitre',
        'sarmiento': 'sarmiento',
        'belgrano_sur': 'belgrano_sur',
        'tren_de_la_costa': 'tren_de_la_costa'
    }
    
    carpeta_linea = mapa_carpetas.get(linea_norm, linea_norm)

    rutas_buscar = [
        # 1. Buscar PRIMERO en globales
        'configs/reglas/globales/personalizadas.json',
        'configs/reglas/globales/componentes.json',
        'configs/reglas/globales/estructura.json',
        
        # 2. Buscar DESPUÉS en carpeta de la línea específica (si existe)
        f'configs/reglas/{carpeta_linea}/personalizadas.json',
    ]
    print(f"🔍 Buscando regla en: {rutas_buscar}")
    
    palabras_clave = [p for p in patron.split() if len(p) > 3]  # Solo palabras significativas
    
    for ruta in rutas_buscar:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                data_reglas = json.load(f)
            
            for regla in data_reglas.get('reglas', []):
                if not regla.get('activa', True):
                    continue
                
                nombre_regla = regla.get('patron_detectado', '').lower()
                regex_regla = regla.get('regex_sugerido', '').lower()
                
                # Buscar por palabras clave en nombre
                coincidencias_nombre = sum(1 for p in palabras_clave if p in nombre_regla)
                
                # Buscar por similitud de regex (primeros 10 caracteres)
                regex_nuevo = data.get('regex', '')[:10].lower()
                similitud_regex = regex_nuevo and regex_nuevo in regex_regla
                
                if coincidencias_nombre >= 2 or similitud_regex:
                    return jsonify({
                        'ok': True,
                        'regla_encontrada': True,
                        'regla': regla
                    })
    
    return jsonify({
        'ok': True,
        'regla_encontrada': False
    })

@app.route('/api/reglas/crear', methods=['POST'])
def crear_regla():
    """Crea nueva regla y re-valida mensajes afectados"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403
    
    data = request.get_json()
    regla = data.get('regla')
    
    # Generar ID único
    import uuid
    regla['id'] = str(uuid.uuid4())[:8]
    regla['fecha_creacion'] = datetime.now().isoformat()
    regla['activa'] = True
    
    # Guardar en archivo correspondiente
    # Normalizar nombre de carpeta
    linea_carpeta = regla['linea'].replace(' ', '_').replace('(', '').replace(')', '').lower()
    # Mapear nombres de línea a carpetas
    mapa_carpetas = {
        'global': 'globales',
        'globales': 'globales',
        'linea_san_martin_manual': 'san_martin',
        'linea_san_martin': 'san_martin',
        'san_martin': 'san_martin',
        'linea_roca': 'roca',
        'roca': 'roca',
        'linea_mitre': 'mitre',
        'mitre': 'mitre',
        'linea_sarmiento': 'sarmiento',
        'sarmiento': 'sarmiento',
        'linea_belgrano_sur': 'belgrano_sur',
        'belgrano_sur': 'belgrano_sur',
        'tren_de_la_costa': 'tren_de_la_costa',
        'costa': 'tren_de_la_costa'
    }
    carpeta = mapa_carpetas.get(linea_carpeta, linea_carpeta)
    ruta_reglas = f'configs/reglas/{carpeta}/personalizadas.json'
    print(f"🔍 Guardando regla en: {ruta_reglas}")
    
    # Crear directorio si no existe
    Path(f'configs/reglas/{carpeta}').mkdir(parents=True, exist_ok=True)
    
    # Cargar o crear archivo
    if os.path.exists(ruta_reglas):
        with open(ruta_reglas, 'r', encoding='utf-8') as f:
            data_reglas = json.load(f)
    else:
        data_reglas = {'version': '1.0', 'reglas': []}
    
    # Agregar nueva regla
    data_reglas['reglas'].append(regla)
    
    # Guardar
    with open(ruta_reglas, 'w', encoding='utf-8') as f:
        json.dump(data_reglas, f, indent=2, ensure_ascii=False)
    
    # Re-validar mensajes afectados
    # 1. Limpiar cache para cargar la regla nueva
    validador_mensajes.recargar_reglas()
    
    mensajes_resueltos = 0
    mensajes_reclasificados = 0
    
    import re as re_module

    for mensaje in gestor.mensajes:
        # Solo verificar mensajes relevantes (no completados ni bloqueados por otro motivo)
        # Nota: 'bloqueado' es un flag, no un estado.
        if mensaje['estado'] in ['PENDIENTE', 'ASIGNADO_PATRICIA', 'ASIGNADO_DIEGO', 'ASIGNADO_ARIEL', 'DERIVADO_A_ARIEL']:
            try:
                # Usar regex de la regla para filtrar candidatos (optimización)
                regex = regla.get('regex_sugerido', '')
                if regex and re_module.search(regex, mensaje['contenido'], re_module.IGNORECASE | re_module.UNICODE):
                    
                    # 2. Re-valida completamente usando el motor real
                    nuevo_reporte = validador_mensajes.procesar_mensaje(mensaje)
                    
                    old_nivel = mensaje.get('nivel_general', '')
                    new_nivel = nuevo_reporte.get('nivel_general', '')
                    
                    # 3. Actualizar campos del mensaje en memoria
                    mensaje.update({
                        'clasificacion': nuevo_reporte['clasificacion'],
                        'nivel_general': new_nivel,
                        'scores': nuevo_reporte['scores'],
                        'componentes': nuevo_reporte['componentes'],
                        'timing': nuevo_reporte['timing'],
                        # Agregar info de regla aplicada si existe
                        'regla_personalizada_aplicada': nuevo_reporte.get('regla_personalizada_aplicada')
                    })
                    
                    # 4. Lógica de resolución de estados
                    if mensaje['estado'] == 'DERIVADO_A_ARIEL':
                        # Si estaba reportado y ahora pasa (o tiene observaciones aceptables)
                        if new_nivel in ['COMPLETO', 'OBSERVACIONES']:
                            mensaje['estado'] = 'PENDIENTE'
                            mensajes_resueltos += 1
                            print(f"✅ Mensaje {mensaje.get('id')} resuelto/desbloqueado por regla nueva")
                    else:
                        if old_nivel != new_nivel:
                            mensajes_reclasificados += 1
                            
            except Exception as e:
                print(f"⚠️ Error re-validando mensaje {mensaje.get('id')}: {e}")
                continue
    
    gestor._guardar_mensajes()
    
    print(f"✅ Regla '{regla['patron_detectado']}' creada. Afectados: {mensajes_resueltos + mensajes_reclasificados}")
    
    return jsonify({
        'ok': True,
        'regla_id': regla['id'],
        'mensajes_afectados': mensajes_resueltos + mensajes_reclasificados,
        'mensajes_resueltos': mensajes_resueltos,
        'mensajes_reclasificados': mensajes_reclasificados
    })

# ENDPOINT DE IA ELIMINADO - Antigravity maneja la creación/modificación de reglas

# ============================================
# ENDPOINTS PARA ANTIGRAVITY
# ============================================

@app.route('/api/reglas/todas', methods=['GET'])
def obtener_todas_reglas():
    """Retorna todas las reglas activas - para que Antigravity las consulte"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403

    todas_reglas = cargar_todas_las_reglas()
    return jsonify({
        'ok': True,
        'total': len(todas_reglas),
        'reglas': todas_reglas
    })

@app.route('/api/reglas/modificar/<regla_id>', methods=['POST'])
def modificar_regla(regla_id):
    """Modifica una regla existente - llamado por Antigravity"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403

    data = request.get_json()
    actualizaciones = data.get('actualizaciones', {})

    todas_reglas = cargar_todas_las_reglas()
    regla_encontrada = False

    for regla in todas_reglas:
        if regla.get('id') == regla_id:
            # Actualizar campos permitidos
            campos_permitidos = ['regex_sugerido', 'accion_sugerida', 'tipo', 'patron_detectado']
            for campo in campos_permitidos:
                if campo in actualizaciones:
                    regla[campo] = actualizaciones[campo]

            regla['fecha_modificacion'] = datetime.now().isoformat()
            regla_encontrada = True

            # Guardar en archivo
            ruta_archivo = regla.get('_archivo')
            if ruta_archivo and os.path.exists(ruta_archivo):
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    contenido = json.load(f)

                # Actualizar en la lista
                for r in contenido.get('reglas', []):
                    if r.get('id') == regla_id:
                        r.update(regla)
                        break

                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    json.dump(contenido, f, indent=2, ensure_ascii=False)

                # Re-validar mensajes
                validador_mensajes.recargar_reglas()

                print(f"✅ Regla '{regla_id}' modificada exitosamente")
                return jsonify({
                    'ok': True,
                    'mensaje': 'Regla modificada',
                    'regla': regla
                })

    return jsonify({'ok': False, 'error': 'Regla no encontrada'}), 404

@app.route('/api/reglas/aplicar-todas', methods=['POST'])
def aplicar_reglas_todas():
    """Re-valida todos los mensajes con las reglas actuales - llamado por Antigravity después de crear/modificar"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403

    validador_mensajes.recargar_reglas()

    mensajes_resueltos = 0
    mensajes_reclasificados = 0

    for mensaje in gestor.mensajes:
        if mensaje['estado'] in ['PENDIENTE', 'ASIGNADO_PATRICIA', 'ASIGNADO_DIEGO', 'ASIGNADO_ARIEL', 'DERIVADO_A_ARIEL']:
            try:
                nuevo_reporte = validador_mensajes.procesar_mensaje(mensaje)

                old_nivel = mensaje.get('nivel_general', '')
                new_nivel = nuevo_reporte.get('nivel_general', '')

                mensaje.update({
                    'clasificacion': nuevo_reporte['clasificacion'],
                    'nivel_general': new_nivel,
                    'scores': nuevo_reporte['scores'],
                    'componentes': nuevo_reporte['componentes']
                })

                if mensaje['estado'] == 'DERIVADO_A_ARIEL':
                    if new_nivel in ['COMPLETO', 'OBSERVACIONES']:
                        mensaje['estado'] = 'PENDIENTE'
                        mensajes_resueltos += 1
                else:
                    if old_nivel != new_nivel:
                        mensajes_reclasificados += 1

            except Exception as e:
                print(f"⚠️ Error re-validando {mensaje.get('id')}: {e}")
                continue

    gestor._guardar_mensajes()

    return jsonify({
        'ok': True,
        'mensaje': 'Re-validación completada',
        'mensajes_resueltos': mensajes_resueltos,
        'mensajes_reclasificados': mensajes_reclasificados,
        'total_afectados': mensajes_resueltos + mensajes_reclasificados
    })

# ============================================
# PANEL DE SCRAPING VPN
# ============================================

def transformar_mensaje_scrapeado(msg_scraper: dict, reporte: dict, linea_nombre: str) -> dict:
    """Convierte el dict del scraper al formato del sistema (mensajes_estado.json)"""
    # ID formateado con ceros a la izquierda (8 dígitos)
    id_raw = msg_scraper.get('numero_mensaje', '') or msg_scraper.get('id_mensaje', '')
    id_formateado = str(id_raw).zfill(8) if id_raw else ''

    return {
        'id':            id_formateado,
        'contenido':     msg_scraper.get('contenido', ''),
        'operador':      msg_scraper.get('operador', ''),
        'linea':         linea_nombre,
        'fecha_hora':    msg_scraper.get('fecha_hora', ''),
        'tipo_mensaje':  reporte.get('tipo_mensaje'),
        'estado':        'PENDIENTE',
        'asignado_a':    None,
        'asignado_en':   None,
        'procesado_por': None,
        'procesado_en':  None,
        'nivel_general': reporte.get('nivel_general', 'OBSERVACIONES'),
        'clasificacion': reporte.get('clasificacion', {}),
        'scores':        reporte.get('scores', {}),
        'componentes':   reporte.get('componentes', {}),
        'timing':        reporte.get('timing'),
    }

@app.route('/api/scraping/san-martin', methods=['POST'])
def scraping_san_martin():
    """Scrapea mensajes de San Martín usando credenciales VPN del validador"""
    if 'nombre' not in session:
        return jsonify({'ok': False, 'error': 'No autenticado'}), 401

    data = request.get_json()
    vpn_user     = (data.get('vpn_user', '') or '').strip()
    vpn_password = (data.get('vpn_password', '') or '').strip()
    fecha_inicio_str = (data.get('fecha_inicio', '') or '').strip()
    fecha_fin_str    = (data.get('fecha_fin', '') or '').strip()

    if not all([vpn_user, vpn_password, fecha_inicio_str, fecha_fin_str]):
        return jsonify({'ok': False, 'error': 'Faltan datos: vpn_user, vpn_password, fecha_inicio, fecha_fin'}), 400

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%d/%m/%Y')
        fecha_fin    = datetime.strptime(fecha_fin_str,    '%d/%m/%Y')
    except ValueError:
        return jsonify({'ok': False, 'error': 'Formato de fecha inválido. Usar DD/MM/YYYY'}), 400

    if (fecha_fin - fecha_inicio).days > 7:
        return jsonify({'ok': False, 'error': 'Rango máximo permitido: 7 días'}), 400

    if fecha_fin < fecha_inicio:
        return jsonify({'ok': False, 'error': 'La fecha fin debe ser mayor o igual a fecha inicio'}), 400

    # Scraping
    try:
        from scraper_requests import scrape_san_martin, ScraperLoginError, ScraperError
        mensajes_scrapeados = scrape_san_martin(vpn_user, vpn_password, fecha_inicio, fecha_fin)
    except ScraperLoginError as e:
        return jsonify({'ok': False, 'error': f'Credenciales VPN incorrectas: {e}'}), 401
    except ScraperError as e:
        return jsonify({'ok': False, 'error': f'Error durante el scraping: {e}'}), 500
    except Exception as e:
        print(f"Error inesperado en scraping: {e}")
        return jsonify({'ok': False, 'error': 'Error inesperado. Verificá tu conexión a internet.'}), 500

    # Deduplicación: comparar id_mensaje (scraper) vs id (sistema, zero-padded)
    ids_existentes = set()
    for m in gestor.mensajes:
        raw = m.get('id', '').lstrip('0') or '0'
        ids_existentes.add(raw)

    LINEA_SAN_MARTIN = 'Línea San Martín'
    nuevos    = 0
    duplicados = 0
    errores    = 0
    mensajes_nuevos = []

    for msg in mensajes_scrapeados:
        id_raw = str(msg.get('id_mensaje', '') or msg.get('numero_mensaje', '')).lstrip('0') or '0'

        if not id_raw or id_raw == '0':
            errores += 1
            continue

        if id_raw in ids_existentes:
            duplicados += 1
            continue

        try:
            reporte = validador_mensajes.procesar_mensaje(msg)
            msg_sistema = transformar_mensaje_scrapeado(msg, reporte, LINEA_SAN_MARTIN)
            mensajes_nuevos.append(msg_sistema)
            ids_existentes.add(id_raw)  # Evitar duplicados dentro del mismo batch
            nuevos += 1
        except Exception as e:
            print(f"⚠️  Error procesando mensaje {id_raw}: {e}")
            errores += 1

    if mensajes_nuevos:
        gestor.mensajes.extend(mensajes_nuevos)
        gestor._guardar_mensajes()

    print(f"🚂 Scraping San Martín por {session['nombre']}: "
          f"{nuevos} nuevos, {duplicados} duplicados, {errores} errores")

    return jsonify({
        'ok':         True,
        'nuevos':     nuevos,
        'duplicados': duplicados,
        'errores':    errores,
        'timestamp':  datetime.now().isoformat(),
    })


# ============================================
# IMPORTAR MENSAJES VÍA BOOKMARKLET
# (el validador los extrae desde su Chrome y los envía acá)
# ============================================

# Token simple para evitar spam — configurar en .env
IMPORT_TOKEN = os.environ.get('IMPORT_TOKEN', 'sofse2026')

@app.route('/api/scraping/importar', methods=['POST', 'OPTIONS'])
def importar_mensajes_bookmarklet():
    """Recibe mensajes ya parseados desde el bookmarklet del validador"""
    # Verificar token
    token = request.args.get('token', '')
    if token != IMPORT_TOKEN:
        return jsonify({'ok': False, 'error': 'Token inválido'}), 403

    data = request.get_json()
    if not data or 'mensajes' not in data:
        return jsonify({'ok': False, 'error': 'Faltan mensajes en el body'}), 400

    mensajes_recibidos = data.get('mensajes', [])
    if not mensajes_recibidos:
        return jsonify({'ok': True, 'nuevos': 0, 'duplicados': 0, 'errores': 0,
                        'mensaje': 'No se encontraron mensajes en la página'})

    # Deduplicación: comparar ids
    ids_existentes = set()
    for m in gestor.mensajes:
        raw = m.get('id', '').lstrip('0') or '0'
        ids_existentes.add(raw)

    nuevos = 0
    duplicados = 0
    errores = 0
    mensajes_nuevos = []

    for msg in mensajes_recibidos:
        id_raw = str(msg.get('id_mensaje', '') or msg.get('numero_mensaje', '')).lstrip('0') or '0'

        if not id_raw or id_raw == '0':
            errores += 1
            continue

        if id_raw in ids_existentes:
            duplicados += 1
            continue

        # Inferir nombre de línea desde el mensaje o usar default
        linea_nombre = msg.get('linea', '') or 'Línea San Martín'

        try:
            reporte = validador_mensajes.procesar_mensaje(msg)
            msg_sistema = transformar_mensaje_scrapeado(msg, reporte, linea_nombre)
            mensajes_nuevos.append(msg_sistema)
            ids_existentes.add(id_raw)
            nuevos += 1
        except Exception as e:
            print(f"⚠️  Error procesando mensaje {id_raw}: {e}")
            errores += 1

    if mensajes_nuevos:
        gestor.mensajes.extend(mensajes_nuevos)
        gestor._guardar_mensajes()

    print(f"📋 Bookmarklet import: {nuevos} nuevos, {duplicados} duplicados, {errores} errores")

    return jsonify({
        'ok':         True,
        'nuevos':     nuevos,
        'duplicados': duplicados,
        'errores':    errores,
        'timestamp':  datetime.now().isoformat(),
    })


# ============================================
# SCRAPER HÍBRIDO: Login auto + Extracción CDP
# (Playwright abre Chrome, usuario navega, backend extrae)
# ============================================

@app.route('/api/scraping/iniciar', methods=['POST'])
def scraping_iniciar():
    """Abre Chrome con Playwright y hace login al portal VPN"""
    if 'nombre' not in session:
        return jsonify({'ok': False, 'error': 'No autenticado'}), 401

    data = request.get_json()
    vpn_user     = (data.get('vpn_user', '') or '').strip()
    vpn_password = (data.get('vpn_password', '') or '').strip()

    if not vpn_user or not vpn_password:
        return jsonify({'ok': False, 'error': 'Ingresá usuario y contraseña VPN'}), 400

    try:
        from scraper_hibrido import abrir_y_login
        resultado = abrir_y_login(vpn_user, vpn_password)
        print(f"🌐 Scraping iniciar por {session['nombre']}: {resultado.get('mensaje', '')}")
        return jsonify(resultado)
    except ImportError:
        return jsonify({
            'ok': False,
            'error': 'Playwright no disponible en este servidor. Usá el bookmarklet como alternativa.'
        }), 500
    except Exception as e:
        print(f"❌ Error en scraping/iniciar: {e}")
        return jsonify({'ok': False, 'error': f'Error: {str(e)}'}), 500


@app.route('/api/scraping/extraer', methods=['POST'])
def scraping_extraer():
    """Lee mensajes de la página abierta en Chrome via CDP"""
    if 'nombre' not in session:
        return jsonify({'ok': False, 'error': 'No autenticado'}), 401

    try:
        from scraper_hibrido import extraer_pagina_actual
        resultado = extraer_pagina_actual()
    except ImportError:
        return jsonify({
            'ok': False,
            'error': 'Playwright no disponible en este servidor.'
        }), 500
    except Exception as e:
        print(f"❌ Error en scraping/extraer: {e}")
        return jsonify({'ok': False, 'error': f'Error: {str(e)}'}), 500

    if not resultado.get('ok') or not resultado.get('mensajes'):
        return jsonify({
            'ok': resultado.get('ok', False),
            'error': resultado.get('mensaje', 'No se encontraron mensajes'),
            'url_leida': resultado.get('url', ''),
            'nuevos': 0,
            'duplicados': 0,
            'errores': 0,
        })

    # Deduplicación (misma lógica que los otros endpoints)
    ids_existentes = set()
    for m in gestor.mensajes:
        raw = m.get('id', '').lstrip('0') or '0'
        ids_existentes.add(raw)

    nuevos = 0
    duplicados = 0
    errores = 0
    mensajes_nuevos = []

    for msg in resultado['mensajes']:
        id_raw = str(msg.get('id_mensaje', '') or msg.get('numero_mensaje', '')).lstrip('0') or '0'

        if not id_raw or id_raw == '0':
            errores += 1
            continue

        if id_raw in ids_existentes:
            duplicados += 1
            continue

        linea_nombre = msg.get('linea', '') or 'Línea San Martín'

        try:
            reporte = validador_mensajes.procesar_mensaje(msg)
            msg_sistema = transformar_mensaje_scrapeado(msg, reporte, linea_nombre)
            mensajes_nuevos.append(msg_sistema)
            ids_existentes.add(id_raw)
            nuevos += 1
        except Exception as e:
            print(f"⚠️  Error procesando mensaje {id_raw}: {e}")
            errores += 1

    if mensajes_nuevos:
        gestor.mensajes.extend(mensajes_nuevos)
        gestor._guardar_mensajes()

    print(f"🚂 Extracción CDP por {session['nombre']}: "
          f"{nuevos} nuevos, {duplicados} duplicados, {errores} errores | {resultado.get('url', '')}")

    return jsonify({
        'ok':         True,
        'nuevos':     nuevos,
        'duplicados': duplicados,
        'errores':    errores,
        'url_leida':  resultado.get('url', ''),
        'timestamp':  datetime.now().isoformat(),
    })


@app.route('/api/scraping/estado', methods=['GET'])
def scraping_estado():
    """Verifica si hay un Chrome abierto con debug port"""
    try:
        from scraper_hibrido import browser_activo
        activo = browser_activo()
        return jsonify({'ok': True, 'browser_activo': activo})
    except ImportError:
        return jsonify({'ok': True, 'browser_activo': False, 'playwright_disponible': False})
    except Exception:
        return jsonify({'ok': True, 'browser_activo': False})


# ============================================
# HEALTH CHECK
# ============================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'environment': 'render' if os.environ.get('RENDER') else 'local',
        'deploy_version': 'v2-dynamic-html'
    })

@app.route('/debug-assets', methods=['GET'])
def debug_assets():
    """Endpoint de diagnóstico para verificar qué assets tiene el frontend."""
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist', 'assets')
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')
    result = {
        'dist_exists': os.path.exists(dist_dir),
        'assets_dir_exists': os.path.exists(assets_dir),
        'dist_files': [],
        'asset_files': [],
    }
    if os.path.exists(dist_dir):
        result['dist_files'] = os.listdir(dist_dir)
    if os.path.exists(assets_dir):
        result['asset_files'] = os.listdir(assets_dir)
    return jsonify(result)

# ============================================
# SERVIR FRONTEND (React build) EN PRODUCCIÓN
# ============================================
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')

# MIME types explícitos para archivos estáticos
MIME_TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.json': 'application/json',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
}

def _get_index_html():
    """
    Genera el index.html leyendo los assets reales del dist/.
    Si el dist/ existe, toma los nombres de los archivos JS/CSS generados
    por Vite (con hash) para garantizar que siempre sirve el build correcto.
    """
    assets_dir = os.path.join(FRONTEND_DIR, 'assets')
    js_file = ''
    css_file = ''
    if os.path.exists(assets_dir):
        for f in os.listdir(assets_dir):
            if f.endswith('.js'):
                js_file = f'/assets/{f}'
            elif f.endswith('.css'):
                css_file = f'/assets/{f}'

    return f'''<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <meta name="theme-color" content="#1e40af" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <meta name="description" content="Sistema de Validación de Mensajes Ferroviarios - SOFSE" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚆</text></svg>" />
    <title>Validación SOFSE</title>
    {f'<script type="module" crossorigin src="{js_file}"></script>' if js_file else ''}
    {f'<link rel="stylesheet" crossorigin href="{css_file}">' if css_file else ''}
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>'''


if os.path.exists(FRONTEND_DIR):
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """
        Sirve el frontend de React con MIME types correctos y cache headers.
        - Archivos en /assets/* → cache largo (tienen hash en nombre)
        - index.html → generado dinámicamente con assets reales del dist/
        - Las rutas /api/* NO llegan acá porque Flask las resuelve antes
        """
        file_path = os.path.join(FRONTEND_DIR, path)
        if path and os.path.exists(file_path):
            # Detectar MIME type correcto
            ext = os.path.splitext(path)[1].lower()
            mimetype = MIME_TYPES.get(ext)

            response = send_from_directory(FRONTEND_DIR, path, mimetype=mimetype)

            # Assets con hash → cache largo (1 año)
            if 'assets/' in path:
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            return response

        # SPA fallback → index.html generado dinámicamente (siempre fresco)
        from flask import Response
        html = _get_index_html()
        response = Response(html, mimetype='text/html')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
