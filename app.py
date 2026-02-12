from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from gestor_tandas import GestorTandas
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
# Dejamos localhost para desarrollo local
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:5000",
    os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
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
        'configs/reglas/global/personalizadas.json',
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

def construir_system_prompt(reglas_actuales):
    """Construye el system prompt con contexto completo"""
    
    reglas_resumen = []
    for r in reglas_actuales:
        reglas_resumen.append({
            'id': r.get('id'),
            'patron': r.get('patron_detectado'),
            'regex': r.get('regex_sugerido'),
            'accion': r.get('accion_sugerida'),
            'tipo': r.get('tipo', 'FALSO_POSITIVO'),
            'linea': r.get('linea', 'global')
        })
    
    return f"""Sos un asistente experto en reglas de validación para mensajes ferroviarios SOFSE Argentina.

## CONCEPTO FUNDAMENTAL - DOS SISTEMAS SEPARADOS:

### SISTEMA 1: VALIDADOR ORIGINAL (validador_mensajes.py)
- Analiza cada mensaje cuando llega al sistema
- Tiene lógica hardcodeada en Python con sus propios regex
- Detecta componentes A, B, C, D, E, F
- NO lee los archivos JSON de reglas personalizadas
- NO puede modificarse fácilmente

### SISTEMA 2: REGLAS PERSONALIZADAS (configs/reglas/*.json)
- Son reglas que crea Ariel manualmente
- Se aplican DESPUÉS de la validación original, en re-validaciones
- Pueden corregir errores del validador original
- Son los archivos JSON que ves más abajo

### POR QUÉ EL VALIDADOR NO TOMÓ UN FORMATO:
Cuando el validador original marca un error en un mensaje que parece correcto,
significa que el formato usado por el operador NO coincide con el regex
hardcodeado en validador_mensajes.py.

Ejemplos de formatos que el validador NO reconoce:
- Horario "DE LAS08 59 HS" → espera "DE LAS HH:MM HS" (con espacio y dos puntos)
- Minutos "5_ MINUTOS" → espera "5 MINUTOS" (sin guión bajo)
- Origen "DE RETIRO (LSM) HACIA PILAR" → puede fallar por los paréntesis

### LO QUE PUEDE HACER UNA REGLA PERSONALIZADA:
Una regla JSON NO modifica el validador original.
Lo que hace es: después de que el validador marcó el error,
la regla dice "este error es en realidad un falso positivo,
el mensaje está bien aunque el validador no lo reconoció".

## TU TRABAJO EN ESTE CHAT:
1. Leer el COMENTARIO DEL VALIDADOR (Patricia/Diego)
2. Entender qué formato específico causó el problema
3. Verificar si alguna REGLA PERSONALIZADA ya existente cubre ese caso
4. Si existe → decirle a Ariel "ya existe la regla X, pero no se aplicó porque..."
5. Si no existe → sugerir crear una regla nueva
6. NUNCA decir "aplicar las reglas vigentes" como si fuera una acción ejecutable
7. NUNCA confundir el validador original con las reglas JSON

## REGLAS PERSONALIZADAS ACTUALMENTE EN EL SISTEMA ({{len(reglas_actuales)}} reglas):
{json.dumps(reglas_resumen, ensure_ascii=False, indent=2)}

## LÓGICA DEL VALIDADOR ORIGINAL:

### COMPONENTES POR TIPO:

TREN_ESPECIFICO (código 3.x.x o 17.x.x):
- A: Número de tren → regex espera: \\d{{4}}
- B: Estado → espera: DEMORA | CANCELADO | SUSPENDIDO
- C: Motivo → espera texto libre de contingencia
- D: Hora → espera EXACTAMENTE: "DE LAS HH:MM HS" con dos puntos
- E: Recorrido → espera: "DE [origen] HACIA [destino]" sin paréntesis intermedios
- F: Código → espera: \\d{{1,2}}\\.\\d{{1,2}}\\.[A-Z]

SERVICIO_GENERAL (código 03.x.x):
- No requiere tren ni hora ni recorrido puntual

### FORMATOS QUE EL VALIDADOR ORIGINAL NO RECONOCE:
- Horario sin dos puntos: 14_30, 14 30, 14.30, 1430, DE LAS14:30HS (sin espacio)
- Minutos con símbolo: 5_ MINUTOS, 10_MIN, 5_MIN
- Recorrido con paréntesis en origen: DE RETIRO (LSM) HACIA PILAR
- Número de tren con prefijo: @T3432, N @T3432

## CÓMO RESPONDER:

### Si el formato YA tiene regla existente:
"El validador no reconoció [formato] porque su regex espera [formato correcto].
Ya existe la regla [ID] que cubre este caso.
Sin embargo, esa regla no se aplicó a este mensaje porque [razón].
¿Querés que verifique si la regla necesita ajuste?"

### Si el formato NO tiene regla existente:
"El validador no reconoció [formato] porque su regex espera [formato correcto].
No existe regla para este caso todavía.
Te sugiero crear una regla con este patrón: [patrón]"

### Cuando tenés una regla lista:
Incluí al final un bloque JSON así:
```json
{{
  "lista_para_crear": true,
  "patron_detectado": "descripción clara",
  "regex_sugerido": "expresión regular válida en Python",
  "accion_sugerida": "aprobar_sin_obs | aprobar_con_obs | rechazar",
  "tipo": "FALSO_POSITIVO | FALSO_NEGATIVO",
  "ampliar_regla_id": "id_si_amplía_una_existente_o_null"
}}
```

## TONO:
- Respondé en español argentino
- Sé directo y concreto
- Máximo 5 líneas por respuesta
- No repitas lo que ya dijiste
- Si Ariel replantea, ajustá tu análisis sin volver a explicar todo desde cero"""

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
        'configs/reglas/global/personalizadas.json',
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
        # 1. Buscar PRIMERO en globales (con S y sin S)
        'configs/reglas/globales/personalizadas.json',
        'configs/reglas/globales/componentes.json',
        'configs/reglas/globales/estructura.json',
        'configs/reglas/global/personalizadas.json',
        
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
        'global': 'global',
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
    mensajes_resueltos = 0
    mensajes_reclasificados = 0
    
    # Obtener acción con múltiples nombres posibles
    accion = regla.get('accion_sugerida') or regla.get('accion') or 'aprobar_con_obs'

    for mensaje in gestor.mensajes:
        if mensaje['estado'] in ['PENDIENTE', 'ASIGNADO_PATRICIA', 'ASIGNADO_DIEGO', 'ASIGNADO_ARIEL', 'DERIVADO_A_ARIEL']:
            import re as re_module
            try:
                if re_module.search(regla.get('regex_sugerido', ''), mensaje['contenido']):
                    if accion == 'aprobar_sin_obs':
                        mensaje['nivel_general'] = 'COMPLETO'
                    elif accion == 'aprobar_con_obs':
                        mensaje['nivel_general'] = 'OBSERVACIONES'
                    
                    if mensaje['estado'] == 'DERIVADO_A_ARIEL':
                        mensaje['estado'] = 'PENDIENTE'
                        mensajes_resueltos += 1
                    else:
                        mensajes_reclasificados += 1
            except Exception as e:
                print(f"⚠️ Error al aplicar regex a mensaje {mensaje['id']}: {e}")
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

@app.route('/api/analizar-regla-ia', methods=['POST'])
def analizar_regla_ia():
    """Chat multi-turno con IA para crear reglas"""
    if session.get('nombre') != 'Ariel':
        return jsonify({'ok': False}), 403
    
    data = request.get_json()
    historial = data.get('historial', [])
    mensaje_actual = data.get('mensaje_actual', '')
    mensaje_ferroviario = data.get('mensaje_ferroviario', {})
    
    # Cargar reglas actuales dinámicamente
    reglas_actuales = cargar_todas_las_reglas()
    system_prompt = construir_system_prompt(reglas_actuales)
    
    # Construir historial para la API
    messages = []
    
    # Si es el primer mensaje, incluir contexto del mensaje ferroviario
    if len(historial) == 0:
        primer_mensaje = f"""Analizá este caso donde {mensaje_ferroviario.get('derivado_por', 'el validador')} reportó un error del sistema.

COMENTARIO DEL VALIDADOR:
"{mensaje_ferroviario.get('comentario_validador', '')}"

CONTENIDO DEL MENSAJE FERROVIARIO:
{mensaje_ferroviario.get('contenido', '')}

ERROR QUE EL SISTEMA DETECTÓ:
{chr(10).join(['- ' + e for e in mensaje_ferroviario.get('clasificacion', {}).get('IMPORTANTE', [])])}

OBSERVACIONES DEL SISTEMA:
{chr(10).join(['- ' + e for e in mensaje_ferroviario.get('clasificacion', {}).get('OBSERVACIONES', [])])}

Identificá si es falso positivo o falso negativo basándote en el comentario del validador."""
        messages.append({"role": "user", "content": primer_mensaje})
    else:
        # Reconstruir historial completo
        for msg in historial:
            messages.append({
                "role": msg['rol'],
                "content": msg['contenido']
            })
        # Agregar mensaje actual
        if mensaje_actual:
            messages.append({"role": "user", "content": mensaje_actual})
    
    # Intentar con ANTHROPIC (Claude)
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_key:
        try:
            print("📡 Intentando conectar con Claude (Anthropic)...")
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
            
            respuesta_texto = response.content[0].text
            return procesar_respuesta_ia(respuesta_texto)
            
        except Exception as e:
            print(f"⚠️ Error Anthropic: {e}")

    # Intentar con GEMINI (Google)
    gemini_key = os.environ.get('GEMINI_API_KEY', '').strip().replace("'", "").replace('"', "")
    if len(gemini_key) > 5:
        try:
            print("📡 Intentando conectar con Gemini...")
            import requests
            
            # Convertir historial a formato Gemini
            contents = []
            # System prompt va separado o como primer mensaje user/model
            # En Gemini 1.5 Flash podemos usar system instruction o meterlo en el primer turno
            
            # Estrategia: System prompt como parte del primer mensaje de usuario
            # Y mapear historial
            
            # Mantener el primer mensaje con system prompt si es posible, o concatenarlo
            
            msgs_gemini = []
            msgs_gemini.append({
                "role": "user",
                "parts": [{"text": system_prompt + "\n\n" + messages[0]['content']}]
            })
            
            for m in messages[1:]:
                role = "model" if m['role'] == "assistant" else "user"
                msgs_gemini.append({
                    "role": role,
                    "parts": [{"text": m['content']}]
                })
                
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
            payload = {
                "contents": msgs_gemini,
                "generationConfig": {"temperature": 0.3}
            }
            
            resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=25)
            
            if resp.status_code == 200:
                respuesta_texto = resp.json()['candidates'][0]['content']['parts'][0]['text']
                return procesar_respuesta_ia(respuesta_texto)
            else:
                print(f"⚠️ Error Gemini: {resp.text[:100]}")
                
        except Exception as e:
            print(f"⚠️ Excepción Gemini: {e}")

    # Intentar con OPENAI (GPT-4o)
    openai_key = os.environ.get('OPENAI_API_KEY', '').strip().replace("'", "").replace('"', "")
    if len(openai_key) > 10:
        try:
            print("📡 Intentando conectar con OpenAI...")
            import requests
            
            msgs_openai = [{"role": "system", "content": system_prompt}] + messages
            
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": msgs_openai,
                    "temperature": 0.3
                },
                timeout=30
            )
            
            if resp.status_code == 200:
                respuesta_texto = resp.json()['choices'][0]['message']['content']
                return procesar_respuesta_ia(respuesta_texto)
            else:
                print(f"⚠️ Error OpenAI: {resp.text[:100]}")
                
        except Exception as e:
            print(f"⚠️ Excepción OpenAI: {e}")

    print("❌ FATAL: Todas las IAs fallaron.")
    return jsonify({'ok': False, 'error': 'Fallo total de conexión con IAs. Verificar API Keys.'}), 500

def procesar_respuesta_ia(respuesta_texto):
    """Procesa el texto de respuesta y extrae JSON si existe"""
    import json
    
    regla_lista = None
    if '```json' in respuesta_texto:
        try:
            json_str = respuesta_texto.split('```json')[1].split('```')[0].strip()
            regla_json = json.loads(json_str)
            if regla_json.get('lista_para_crear'):
                regla_lista = regla_json
                # Limpiar el JSON del texto para mostrar
                respuesta_texto = respuesta_texto.split('```json')[0].strip()
        except:
            pass
    
    return jsonify({
        'ok': True,
        'respuesta': respuesta_texto,
        'regla_lista': regla_lista
    })


# ============================================
# HEALTH CHECK
# ============================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'environment': 'render' if os.environ.get('RENDER') else 'local'
    })

# ============================================
# SERVIR FRONTEND (React build) EN PRODUCCIÓN
# ============================================
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')

if os.path.exists(FRONTEND_DIR):
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """
        Sirve el frontend de React.
        - Si pide un archivo que existe (JS, CSS, imágenes) → lo sirve directo
        - Si no → devuelve index.html (React Router maneja la ruta)
        - Las rutas /api/* NO llegan acá porque Flask las resuelve antes
        """
        file_path = os.path.join(FRONTEND_DIR, path)
        if path and os.path.exists(file_path):
            return send_from_directory(FRONTEND_DIR, path)
        return send_from_directory(FRONTEND_DIR, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
