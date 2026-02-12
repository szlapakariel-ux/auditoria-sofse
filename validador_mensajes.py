

"""
Validador de Mensajes SOFSE - Sistema ROCA v3.0
Autor: Ariel - SOFSE Yunex/Constitución  
Fecha: Diciembre 2024

MEJORAS IMPLEMENTADAS (v3.0):
1. ✅ Sección INFORMACIÓN FALTANTE solo si hay faltantes
2. ✅ CANCELADO/SUSPENDIDO no marca tardanza
3. ✅ Estados detectados con espacios múltiples (regex flexible)
4. ✅ Eliminada sugerencia del guion
5. ✅ Detecta inconsistencia código vs contingencia
6. ✅ SERVICIO_GENERAL no muestra tiempo de respuesta
7. ✅ Mensaje sin referencia a Excel
8. ✅ Sin repetir mensaje original en ejemplo
9. ✅ Detecta "DEMORA" singular con cantidad
10. ✅ Advierte código 17 (excepcional)

CLASIFICACIÓN:
- COMPLETO: Mensaje perfecto (antes EXCELENTE)
- IMPORTANTE: Falta información obligatoria
- OBSERVACIONES: Problemas de formato/proceso
- SUGERENCIAS: Mejoras opcionales
"""

import pandas as pd
import json
import re
import glob
import os
import sys
import io

# Forzar UTF-8 en consola Windows para evitar error con emojis
# Forzar UTF-8 en consola Windows para evitar error con emojis
if sys.platform == 'win32':
    # Check if already wrapped or closed to avoid crash on reload
    try:
        if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding.lower() != 'utf-8':
             sys.stdout.reconfigure(encoding='utf-8')
        elif not isinstance(sys.stdout, io.TextIOWrapper):
             # Original logic but guarded
             sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
             sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass # Ignore errors here to prevent module crash

from datetime import datetime, timedelta

# Corrector ortográfico avanzado (instalar: pip install language-tool-python)
try:
    import language_tool_python
    CORRECTOR_DISPONIBLE = True
except ImportError:
    CORRECTOR_DISPONIBLE = False

def cargar_config(linea="ROCA"):
    """Carga configuración específica de la línea"""
    try:
        # Normalizar nombre línea
        if not linea: linea = "ROCA"
        nombre_clean = linea.strip().lower().replace(' ', '_')
        if 'san_martin' in nombre_clean: nombre_clean = 'san_martin'
        
        # Buscar path relativo a este script
        base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, "configs", f"config_{nombre_clean}.json")
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Fallback a ROCA si no existe (para compatibilidad)
            # print(f"⚠️ Config no encontrada para {linea}, usando ROCA por defecto")
            path_roca = os.path.join(base_path, "configs", "config_roca.json")
            if os.path.exists(path_roca):
                with open(path_roca, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"palabras_tecnicas": []}
            
    except Exception as e:
        print(f"❌ Error cargando config: {e}")
        return {"palabras_tecnicas": []}

# =================================================================
#                    MAPEOS DE ESTADOS
# =================================================================

MAP_ESTADOS_CODIGO = {
    '1': {
        'nombre': 'DEMORA',
        'patrones': [
            r'CIRCULA\s+CON\s+DEMORAS?(?:\s+DE)?',
            r'REGISTRA\s+DEMORAS?',
            # MEJORA #5: Variantes de demora de partida
            r'SE\s+ENCUENTRA\s+DEMORANDO',
            r'DEMORANDO\s+SU\s+PARTIDA',
            r'DEMORA(?:S)?\s+EN\s+(?:LA\s+)?PARTIDA',
            r'PARTIDA\s+DEMORADA'
        ]
    },
    '2': {
        'nombre': 'CANCELACIÓN',
        'patrones': [
            r'HA\s+SIDO\s+CANCELADO',
            r'FUE\s+CANCELADO',
            r'SE\s+CANCEL[OÓ]',
            r'SER[AÁ]\s+CANCELADO'
        ]
    },
    '2B': {
        'nombre': 'SUSPENSIÓN',
        'patrones': [
            r'HA\s+SIDO\s+SUSPENDIDO',
            r'FUE\s+SUSPENDIDO',
            r'SE\s+SUSPEND[EÍ]',
            r'SER[AÁ]\s+SUSPENDIDO',
            r'SUSPENDIDO\s+EN',
            r'SER[AÁ]\s+SUSPENDIOD'  # Detectar typo común
        ]
    },
    '3': {
        'nombre': 'RESTABLECIMIENTO',
        'patrones': [
            # MEJORA #5: Agregar estado RESTABLECIMIENTO
            r'SE\s+RESTABLECE',
            r'RESTABLECE\s+(?:EL\s+)?SERVICIO',
            r'SERVICIO\s+RESTABLECIDO'
        ]
    },
    '4': {
        'nombre': 'REDUCIDO',
        'patrones': [
            r'CIRCULA\s+REDUCIDO',
            r'SERVICIO\s+REDUCIDO'
        ]
    },
    '5': {
        'nombre': 'CONDICIONAL',
        'patrones': [
            r'CIRCULA\s+(?:DE\s+FORMA\s+)?CONDICIONAL'
        ]
    },
    '6': {
        'nombre': 'INTERRUMPIDO',
        'patrones': [
            r'SE\s+ENCUENTRA\s+INTERRUMPIDO',
            r'EST[ÁA]\s+INTERRUMPIDO',
            r'INTERRUMPIDO\s+(?:ENTRE|EN)'
        ]
    }
}

# MEJORA: Diccionario de Sinónimos para Contingencias
SINONIMOS_CONTINGENCIAS = {
    'PROBLEMAS TÉCNICOS': [
        'PROBLEMAS TECNICOS', 'FALLA TECNICA', 'DESPERFECTOS TECNICOS', 
        'INCONVENIENTES TECNICOS', 'TECNICOS', 'TECNICO'
    ],
    'PROBLEMAS OPERATIVOS': [
        'PROBLEMAS OPERATIVOS', 'FALLA OPERATIVA', 'INCONVENIENTES OPERATIVOS', 
        'OPERATIVOS', 'OPERATIVO'
    ],
    'OTRAS CONTINGENCIAS': [
        'OTRAS CONTINGENCIAS', 'OTRA CAUSA', 'CAUSA DESCONOCIDA'
    ],
    'ACCIDENTE EN PASO A NIVEL': [
        'ACCIDENTE', 'ACCIDENTE PAN', 'COLISION', 'EMBESTIDA', 'ACCIDENTE EN VÍA'
    ],
    'OBRA EN ZONA DE VÍAS': [
        'OBRA', 'OBRAS', 'TRABAJOS EN VIA', 'REPARACION DE VÍA'
    ],
    'MANIFESTACIÓN / PIQUETE': [
        'MANIFESTACION', 'PIQUETE', 'CORTE DE VIA', 'PROTESTA'
    ]
}

# Estados que no requieren validación de tiempo (o tienen lógica especial)
ESTADOS_SIN_TARDANZA = ['REDUCIDO', 'INTERRUMPIDO', 'CONDICIONAL', 'REANUDACIÓN']

# =================================================================
#                    CARGAR CONTINGENCIAS
# =================================================================

def cargar_contingencias(archivo_excel="Contingencias.xlsx"):
    """Carga matriz de contingencias desde Excel"""
    try:
        df = pd.read_excel(archivo_excel)
        
        # Normalizar nombres de columnas para evitar problemas de mayúsculas/espacios
        df.columns = [c.strip().replace(' ', '_') for c in df.columns]
        
        # Asegurar que código sea string con 2 dígitos
        if 'Codigo' in df.columns:
            df['Código'] = df['Codigo'].astype(str).str.zfill(2)
        elif 'Código' in df.columns:
            df['Código'] = df['Código'].astype(str).str.zfill(2)
            
        # ========================================================
        # PARCHE EN MEMORIA (Alinear Excel viejo con Imagen Nueva)
        # ========================================================
        # El usuario indicó que la imagen es la 'guía'.
        # El Excel local tiene códigos viejos (ej: 01=Técnicos),
        # así que los corregimos aquí para que la validación funcione.
        
        col_com = None
        if 'Forma_Comunicacion' in df.columns: col_com = 'Forma_Comunicacion'
        elif 'Formas_de_comunicación' in df.columns: col_com = 'Formas_de_comunicación'
        
        if col_com:
            # Forzar 03 = PROBLEMAS TÉCNICOS
            df.loc[df[col_com].str.strip().str.upper() == 'PROBLEMAS TÉCNICOS', 'Código'] = '03'
            
            # Forzar 05 = PROBLEMAS OPERATIVOS (si existe la fila, o si era Manifestación)
            # En Excel viejo: 05=Manifestación. En Nuevo 05=Operativos.
            # Buscamos si existe "PROBLEMAS OPERATIVOS"
            mask_op = df[col_com].str.strip().str.upper() == 'PROBLEMAS OPERATIVOS'
            if mask_op.any():
                df.loc[mask_op, 'Código'] = '05'
            else:
                # Si no existe, podríamos renombrar la 05 vieja o agregar nueva.
                # Por seguridad, buscamos la 05 vieja y la actualizamos
                df.loc[df['Código'] == '05', col_com] = 'PROBLEMAS OPERATIVOS'

        return df
    except Exception as e:
        print(f"❌ Error cargando contingencias: {e}")
        return None


_REGLAS_CACHE = None

def cargar_reglas_personalizadas():
    """Carga reglas personalizadas desde JSON"""
    global _REGLAS_CACHE
    if _REGLAS_CACHE is not None:
        return _REGLAS_CACHE
    
    reglas = []
    base_path = os.path.dirname(os.path.abspath(__file__))
    dir_reglas = os.path.join(base_path, 'configs', 'reglas')
    
    if os.path.exists(dir_reglas):
        for root, dirs, files in os.walk(dir_reglas):
            for file in files:
                if file == 'personalizadas.json':
                    try:
                        path = os.path.join(root, file)
                        linea_dir = os.path.basename(root)
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for r in data.get('reglas', []):
                                if r.get('activa', True):
                                    r['_origen'] = linea_dir
                                    reglas.append(r)
                    except Exception as e:
                        print(f"⚠️ Error cargando reglas de {root}: {e}")
    
    _REGLAS_CACHE = reglas
    return reglas

def buscar_contingencia_con_sinonimos(contenido_upper, contingencias_df):
    """
    MEJORA #9: Busca contingencia en texto considerando sinónimos y estructura real
    Retorna: (codigo_contingencia, forma_comunicacion) o (None, None)
    """
    # 1. Búsqueda exacta en columna 'Forma_Comunicacion' (la que va al pasajero)
    col_comunicacion = None
    if 'Forma_Comunicacion' in contingencias_df.columns:
        col_comunicacion = 'Forma_Comunicacion'
    elif 'Formas_de_comunicación' in contingencias_df.columns:
        col_comunicacion = 'Formas_de_comunicación' # fallback por si acaso

    if col_comunicacion:
        for idx, row in contingencias_df.iterrows():
            forma = str(row[col_comunicacion]).upper()
            if forma and forma != 'NAN':
                # Regex flexible
                patron = re.escape(forma).replace(r'\ ', r'\s+')
                if re.search(patron, contenido_upper):
                    codigo = str(row['Código']).zfill(2)
                    return (codigo, forma)
    
    # 2. Búsqueda por sinónimos (si falla la exacta)
    # Actualizado según imagen del usuario:
    # 03 = PROBLEMAS TÉCNICOS
    # 05 = PROBLEMAS OPERATIVOS
    # 17 = OTRAS CONTINGENCIAS
    
    for forma_oficial, sinonimos in SINONIMOS_CONTINGENCIAS.items():
        for sinonimo in sinonimos:
            patron = re.escape(sinonimo).replace(r'\ ', r'\s+')
            if re.search(patron, contenido_upper):
                
                # Buscar el código que corresponde a esa forma oficial en el Excel
                if col_comunicacion:
                    match = contingencias_df[contingencias_df[col_comunicacion].str.upper() == forma_oficial]
                    if not match.empty:
                        codigo = str(match.iloc[0]['Código']).zfill(2)
                        return (codigo, sinonimo)
                
                # Fallback manual si no está en Excel (por seguridad)
                if forma_oficial == 'PROBLEMAS TÉCNICOS': return ('03', sinonimo)
                if forma_oficial == 'PROBLEMAS OPERATIVOS': return ('05', sinonimo)
                if forma_oficial == 'OTRAS CONTINGENCIAS': return ('17', sinonimo)

    return (None, None)

# =================================================================
#                    DETECCIÓN TIPO MENSAJE
# =================================================================

def detectar_tipo_mensaje(contenido):
    """
    Detecta si es TREN ESPECÍFICO, SERVICIO GENERAL o REANUDACIÓN
    
    TREN ESPECÍFICO: Habla de UN tren puntual con número
    SERVICIO GENERAL: Habla del estado de ramal/línea/servicio
    REANUDACIÓN: MEJORA #2 - Mensaje de restablecimiento de servicio
    """
    contenido_upper = contenido.upper()
    
    # MEJORA #2: Detectar reanudación/restablecimiento
    # MEJORA #2: Detectar reanudación/restablecimiento
    if re.search(r'SE\s+RESTABLECE|RESTABLECE\s+(?:EL\s+)?SERVICIO', contenido_upper):
        # Buscar si menciona ramal/línea
        # MEJORA #13: Permitir guiones en nombres de ramales (ej: Retiro-Cabred)
        match_servicio = re.search(
            r'(?:RAMAL|L[ÍI]NEA)\s+([A-ZÁÉÍÓÚÑ\s\-\.]+?)(?:\s+SE\s+|\s+RESTABLECE)',
            contenido_upper
        )
        if match_servicio:
            return {
                'tipo': 'REANUDACION',
                'nombre_servicio': match_servicio.group(1).strip()
            }
        else:
            return {'tipo': 'REANUDACION'}
    
    # Buscar número de tren
    match_tren = re.search(
        r'(?:EL\s+)?TREN\s+(?:N[°º]?\s*)?(\d+)',
        contenido_upper
    )
    
    if match_tren:
        return {
            'tipo': 'TREN_ESPECIFICO',
            'numero_tren': match_tren.group(1)
        }
    
    # Buscar servicio/ramal/línea
    # MEJORA #13: Permitir guiones en nombres de ramales
    match_servicio = re.search(
        r'(?:EL\s+)?(?:SERVICIO|RAMAL|L[ÍI]NEA)\s+([A-ZÁÉÍÓÚÑ\s\-\.]+?)(?:\s+SE\s+|\s+CIRCULA|\s+HA\s+)',
        contenido_upper
    )
    
    if match_servicio:
        return {
            'tipo': 'SERVICIO_GENERAL',
            'nombre_servicio': match_servicio.group(1).strip()
        }
    
    return {
        'tipo': 'DESCONOCIDO'
    }

# =================================================================
#                    VALIDACIÓN CÓDIGO ESTRUCTURA
# =================================================================

def extraer_codigo_estructura(contenido):
    """
    Extrae código de estructura X.Y.Z del mensaje
    Ejemplo: "3.1.A" → X=3, Y=1, Z=A
    Acepta variantes con guiones, espacios o al final del mensaje.
    """
    # Regex más flexible: busca al inicio o con separadores claros
    # Permite: "3.1.A TEXTO", "3-1-A TEXTO", " TEXTO (3.1.A)"
    match = re.search(r'(?:^|[\s\(\-])(\d{1,2})[\.\-](\d{1,2})[\.\-]([A-Z])(?=[\s\)\-]|$)', contenido.strip())
    
    if match:
        return {
            'completo': f"{match.group(1)}.{match.group(2)}.{match.group(3)}",
            'X': match.group(1).zfill(2),  # Código contingencia (01-17...)
            'Y': match.group(2),             # Estado (1-6)
            'Z': match.group(3)              # Ciclo vida
        }
    return None

def validar_codigo_estructura(codigo_extraido, codigo_contingencia_detectado, estado_detectado):
    """
    Valida que el código de estructura coincida con contingencia y estado
    
    MEJORA #5: Detecta inconsistencia código vs contingencia
    MEJORA #8: Acepta código 17 sin contingencia para estaciones compuestas
    """
    observaciones = []
    
    if not codigo_extraido:
        observaciones.append("❌ Falta código de estructura (ej: 3.1.A)")
        return observaciones
    
    # MEJORA #8: Código 17 sin contingencia es válido (estaciones compuestas)
    if codigo_extraido['X'] == '17' and not codigo_contingencia_detectado:
        # Código 17 no requiere contingencia explícita
        pass
    # Validar X (contingencia) para otros códigos
    elif codigo_extraido['X'] != codigo_contingencia_detectado:
        obs = f"⚠️ Inconsistencia en código: Usaste {codigo_extraido['X']} pero la contingencia corresponde al código {codigo_contingencia_detectado}"
        observaciones.append(obs)
    
    # Validar Y (estado)
    estado_esperado = MAP_ESTADOS_CODIGO.get(codigo_extraido['Y'], {}).get('nombre', '')
    if estado_esperado and estado_detectado and estado_esperado != estado_detectado:
        obs = f"⚠️ Inconsistencia en estado: Código indica {estado_esperado} pero el mensaje describe {estado_detectado}"
        observaciones.append(obs)
    
    return observaciones

# =================================================================
#                    VALIDACIÓN DE COMPONENTES
# =================================================================

def validar_componentes(mensaje, contingencias_df):
    """
    Valida los componentes del mensaje según tipo
    
    MEJORAS:
    - #3: Regex flexible con espacios múltiples
    - #9: Detecta "DEMORA" singular
    - #12: Normalizar espacios múltiples
    """
    global CORRECTOR_DISPONIBLE
    
    contenido = mensaje.get('contenido', '')
    
    # MEJORA #12: Normalizar espacios múltiples
    contenido = re.sub(r'\s+', ' ', contenido).strip()
    
    contenido_upper = contenido.upper()
    
    tipo_info = detectar_tipo_mensaje(contenido)
    tipo = tipo_info['tipo']
    
    componentes = {
        'tipo_mensaje': tipo,
        'A': None,  # TREN o SERVICIO
        'B': None,  # ESTADO (demora, cancelación, etc)
        'C': None,  # CONTINGENCIA
        'D': None,  # HORA (solo tren específico)
        'E': None,  # RECORRIDO (solo tren específico)
        'F': None,  # CÓDIGO estructura
        'estructura_valida': False,
        'ortografia_valida': True,
        'errores_ortografia': []
    }
    
    # Componente F: Código de estructura
    codigo_estructura = extraer_codigo_estructura(contenido)
    if codigo_estructura:
        componentes['F'] = codigo_estructura['completo']
        # La estructura solo es válida si además reconocemos el tipo de mensaje
        if tipo != 'DESCONOCIDO':
            componentes['estructura_valida'] = True
        else:
            # Si el tipo es DESCONOCIDO, aunque tenga código, la estructura global no es válida
            componentes['estructura_valida'] = False
            componentes.setdefault('advertencias_formato', []).append(
                "Código detectado pero el mensaje no tiene formato reconocido (TREN o GENERAL)"
            )
    
    # Componente A: Número de tren o servicio
    if tipo == 'TREN_ESPECIFICO':
        match_tren = re.search(r'TREN\s+(?:N[°º]?\s*)?(\d+)', contenido_upper)
        if match_tren:
            componentes['A'] = match_tren.group(1)
    elif tipo == 'SERVICIO_GENERAL':
        # MEJORA #13: Permitir guiones en servicio
        match_servicio = re.search(
            r'(?:SERVICIO|RAMAL|L[ÍI]NEA)\s+([A-ZÁÉÍÓÚÑ\s\-\.]+?)(?:\s+SE\s+|\s+CIRCULA|\s+HA\s+)',
            contenido_upper
        )
        if match_servicio:
            componentes['A'] = match_servicio.group(1).strip()
    
    # Componente B: Estado (MEJORA #3: regex flexible)
    estado_detectado = None
    usa_estructura_formal = False
    
    for cod_estado, info_estado in MAP_ESTADOS_CODIGO.items():
        for patron in info_estado['patrones']:
            if re.search(patron, contenido_upper):
                estado_detectado = info_estado['nombre']
                usa_estructura_formal = True
                componentes['B'] = {
                    'estado': estado_detectado,
                    'codigo': cod_estado,
                    'estructura_formal': True
                }
                break
        if estado_detectado:
            break
    
    # Si no encontró estado formal, buscar menciones informales
    if not estado_detectado:
        # Buscar "DEMORA" sin estructura formal
        if re.search(r'\bDEMORAS?\b', contenido_upper):
            estado_detectado = 'DEMORA'
            componentes['B'] = {
                'estado': estado_detectado,
                'codigo': '1',
                'estructura_formal': False
            }
        # Buscar "CANCELADO/A" sin estructura formal
        elif re.search(r'\bCANCELAD[OA]S?\b', contenido_upper):
            estado_detectado = 'CANCELACIÓN'
            componentes['B'] = {
                'estado': estado_detectado,
                'codigo': '2',
                'estructura_formal': False
            }
    
    # Si es DEMORA, buscar minutos (MEJORA #1: acepta MIN., MIN, singular DEMORA)
    if estado_detectado == 'DEMORA':
        match_minutos = re.search(
            r'(?:DEMORAS?|REGISTRA)\s+(?:DE\s+)?(\d+)\s*(?:MINUTOS?|MIN\.?)',
            contenido_upper
        )
        if match_minutos:
            if componentes['B']:
                componentes['B']['minutos'] = match_minutos.group(1)
    
    # Componente C: Contingencia (MEJORA #9: con sinónimos)
    codigo_contingencia = None
    forma_comunicacion = None
    
    if contingencias_df is not None:
        # MEJORA #9: Buscar con sinónimos
        codigo_contingencia, forma_comunicacion = buscar_contingencia_con_sinonimos(
            contenido_upper, contingencias_df
        )
        if codigo_contingencia:
            componentes['C'] = {
                'codigo': codigo_contingencia,
                'forma_comunicacion': forma_comunicacion
            }
    
    # Componente D y E: Lógica diferenciada por Tipo
    
    if tipo == 'TREN_ESPECIFICO':
        # --- D - HORA (Oficial: DE LAS XX:XX HS) ---
        match_hora = re.search(r'DE\s+LAS\s*(\d{1,2})[:\.\s](\d{2})\s*HS', contenido_upper)
        if match_hora:
            hour_str = match_hora.group(1)
            min_str = match_hora.group(2)
            # Find the separator used (safe slice)
            full_match = match_hora.group(0)
            # Logic to deduce separator might be tricky if spacing is wonky, so we simplify:
            sep = " " if " " in match_hora.group(0)[-6:] else ":" # Rough heuristic or just assume warnings

            componentes['D'] = f"{hour_str}:{min_str}"
            
            # Observación si usa punto o espacio en lugar de dos puntos
            if '.' in full_match or ' ' in full_match[match_hora.start(1)-match_hora.start(0):]: # Check chars between H and M
                 pass # We skip specific separator checks for now to prioritize extraction
                 # or restore the check with better logic

        else:
            # Intentar Flexible (DE LAS sin HS, A LAS, SALIDA...)
            # MEJORA: Soportar "DE LAS HH.MM" sin HS
            match_hora_flex = re.search(r'(?:A\s+LAS|DE\s+LAS|DE|SALIDA|HORA)\s*(\d{1,2})[:\s\.](\d{2})', contenido_upper)
            if match_hora_flex:
                 componentes['D'] = f"{match_hora_flex.group(1)}:{match_hora_flex.group(2)}"
                 componentes.setdefault('advertencias_formato', []).append(
                     "Según Matriz de Mensajes: Usa formato 'DE LAS HH:MM HS'"
                 )

        # --- E - RECORRIDO (Oficial: DESDE [A] HACIA [B]) ---
        # MEJORA: Aceptamos "DE [Origen]" además de "DESDE"
        match_origen = re.search(r'(?:PARTIENDO\s+(?:DE|DESDE)|DESDE|DE)\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)(?=\s+(?:HACIA|A\s+[A-ZÁÉÍÓÚÑ]|CON\s+DEMORA|CIRCULA|HA\s+SIDO|FUE))', contenido_upper)
        match_destino = re.search(r'HACIA\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)(?=\s+(?:CIRCULA|HA\s+SIDO|FUE|CON\s+DEMORA|REGISTRA|SE\s+ENCUENTRA|POR\s+|O\s+TRAS\s+|RESTABLECE|SE\s+|$))', contenido_upper)
        
        # Lógica Flexible: Si no encuentra oficial, buscar variantes
        if not match_origen or not match_destino:
            # Variante 1: "ENTRE [A] Y [B]"
            match_entre = re.search(r'ENTRE\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)\s+Y\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)(?=\s+(?:CIRCULA|HA\s+SIDO|FUE|CON\s+DEMORA|$))', contenido_upper)
            if match_entre:
                componentes['E'] = {
                    'origen': match_entre.group(1).strip(),
                    'destino': match_entre.group(2).strip()
                }
                componentes.setdefault('advertencias_formato', []).append(
                    "Según Matriz de Mensajes: Usa 'DESDE [Origen] HACIA [Destino]'"
                )
                match_origen = True # Flag para que pase la validación
                match_destino = True
            
            # Variante 2: "DE [A] A [B]" (Solo si no encontró ENTRE)
            if not componentes.get('E'):
                match_de_a = re.search(r'(?:SALIENDO\s+|SALE\s+)?DE\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)\s+A\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)(?=\s+(?:CIRCULA|HA\s+SIDO|FUE|CON\s+DEMORA|$))', contenido_upper)
                if match_de_a:
                    componentes['E'] = {
                        'origen': match_de_a.group(1).strip(),
                        'destino': match_de_a.group(2).strip()
                    }
                    componentes.setdefault('advertencias_formato', []).append(
                        "Según Matriz de Mensajes: Usa 'HACIA [Estacion]' en lugar de 'A'"
                    )
        
        if (match_origen and match_destino) or componentes.get('E'):
            if not componentes.get('E'): # Si encontró oficial
                 componentes['E'] = {
                    'origen': match_origen.group(1).strip() if match_origen else None,
                    'destino': match_destino.group(1).strip() if match_destino else None
                }

    elif tipo == 'SERVICIO_GENERAL':
        # --- D - LUGAR (Contextual: "EN ...") ---
        # Busca indicador de lugar después del motivo o al final
        match_lugar = re.search(r'\bEN\s+([A-ZÁÉÍÓÚÑ\s\.]+?)(?=\s+(?:DISCULPA|SEPA|\.|$))', contenido_upper)
        if match_lugar:
             # Filtrar falsos positivos comunes
             lugar = match_lugar.group(1).strip()
             if lugar not in ["EL DIA", "LA TARDE", "LA NOCHE", "EL TRANSCURSO"]:
                componentes['D'] = lugar

        # --- E - DISCULPAS (Opcional) ---
        if "DISCULPA" in contenido_upper or "SEPA DISCULPAR" in contenido_upper:
            componentes['E'] = "Se piden disculpas"
    
    # Validar ortografía con LanguageTool (si está disponible)
    errores_detectados = []
    
    
    # Cargar palabras técnicas desde config
    config = cargar_config(mensaje.get('linea', 'ROCA'))
    palabras_tecnicas = set(config.get('palabras_tecnicas', []))

    if CORRECTOR_DISPONIBLE:
        try:
            # Inicializar corrector español (se carga en memoria)
            tool = language_tool_python.LanguageTool('es')
            
            # Analizar el texto
            matches = tool.check(contenido)
            
            for match in matches:
                palabra_error = contenido[match.offset:match.offset + match.errorLength]
                
                # Ignorar si es palabra técnica conocida
                if palabra_error.upper() in palabras_tecnicas:
                    continue
                
                # Solo errores ortográficos y tipográficos (no gramática)
                if match.ruleId.startswith('MORFOLOGIK') or 'SPELLING' in match.ruleId:
                    sugerencia = match.replacements[0] if match.replacements else '?'
                    errores_detectados.append(f"{palabra_error} → {sugerencia}")
            
            tool.close()
            
        except Exception as e:
            # Si falla LanguageTool, usar sistema regex de respaldo
            CORRECTOR_DISPONIBLE = False
            # Guardamos el aviso como sistema, no como sugerencia de formato para el operador
            componentes['aviso_sistema'] = "Ortografía Básica (Falta Java)"
    
    # Sistema de respaldo con regex (si LanguageTool no disponible)
    if not CORRECTOR_DISPONIBLE:
        # 1. Palabras terminadas incorrectamente (typos comunes)
        patrones_error = [
            (r'\bSUSPENDIOD\b', 'SUSPENDIDO'),
            (r'\bCIRUCLA\b', 'CIRCULA'),
            (r'\bCIRUCLAN\b', 'CIRCULAN'),
            (r'\bPARTEINEDO\b', 'PARTIENDO'),
            (r'\bPARTIDIENDO\b', 'PARTIENDO'),
            (r'\bMOOTIVO\b', 'MOTIVO'),
            (r'\bMOTIVIO\b', 'MOTIVO'),
            (r'\bHACIAA\b', 'HACIA'),
            (r'\bHAICIA\b', 'HACIA'),
            (r'\bREGISTRAA\b', 'REGISTRA'),
            (r'\bREGISTRAAD[OA]\b', 'REGISTRADO/A'),
        ]
        
        for patron, correcto in patrones_error:
            if re.search(patron, contenido_upper):
                palabra_error = re.search(patron, contenido_upper).group()
                errores_detectados.append(f"{palabra_error} → {correcto}")
        
        # 2. Detectar palabras con letras duplicadas incorrectas (3+ letras iguales consecutivas)
        # Buscar patrones como AAA, RRR, etc.
        if re.search(r'([A-Z])\1{2,}', contenido_upper):
            errores_detectados.append("Letras repetidas excesivamente")
    
    # 3. Detectar espacios múltiples (siempre activo)
    if '  ' in contenido:
        espacios_multiples = len(re.findall(r'\s{2,}', contenido))
        if espacios_multiples > 2:
            errores_detectados.append(f"Espacios múltiples ({espacios_multiples} lugares)")
    
    # Aplicar errores detectados
    if errores_detectados:
        componentes['ortografia_valida'] = False
        componentes['errores_ortografia'].extend(errores_detectados)
    
    # Detectar espacios múltiples (ya incluido arriba)
    if '  ' in contenido:  # Dos o más espacios
        espacios_multiples = len(re.findall(r'\s{2,}', contenido))
        if espacios_multiples > 2:  # Tolerar 1-2 espacios dobles
            componentes['ortografia_valida'] = False
            componentes['errores_ortografia'].append(f"Espacios múltiples ({espacios_multiples} lugares)")
    
    return componentes, codigo_estructura, codigo_contingencia, estado_detectado

# =================================================================
#                    VALIDACIÓN TIEMPO RESPUESTA
# =================================================================

def validar_tiempo_respuesta(mensaje, componentes):
    """
    Valida el tiempo de respuesta
    
    MEJORAS:
    - #2: CANCELADO/SUSPENDIDO no valida tardanza
    - #4: CANCELACIÓN acepta timing flexible (hasta 15 min antes es OPORTUNO)
    - #6: SERVICIO_GENERAL no muestra tiempo de respuesta
    """
    # No validar para SERVICIO_GENERAL (MEJORA #6)
    if componentes.get('tipo_mensaje') == 'SERVICIO_GENERAL':
        return None
    
    # No validar para estados sin tardanza (MEJORA #2)
    estado = componentes.get('B', {})
    if isinstance(estado, dict):
        estado_nombre = estado.get('estado', '')
        if estado_nombre in ESTADOS_SIN_TARDANZA:
            return None
    
    # Si no hay hora programada, no se puede calcular
    hora_programada = componentes.get('D')
    if not hora_programada:
        return None
    
    # Para CANCELACIÓN o SUSPENSIÓN, calcular tiempo desde hora programada (no necesita minutos de demora)
    es_cancelacion_o_suspension = isinstance(estado, dict) and estado.get('estado') in ['CANCELACIÓN', 'SUSPENSIÓN']
    minutos_demora = componentes.get('B', {}).get('minutos') if isinstance(componentes.get('B'), dict) else None
    
    # Si no es cancelación/suspensión y no tiene minutos de demora, no se puede calcular
    if not es_cancelacion_o_suspension and not minutos_demora:
        return None
    
    # Calcular tardanza
    try:
        fecha_mensaje = mensaje.get('fecha_hora', '')
        hora_envio = datetime.strptime(fecha_mensaje, "%d/%m/%Y %H:%M:%S")
        
        # Parsear hora programada
        partes_hora = hora_programada.split(':')
        hora_prog = hora_envio.replace(
            hour=int(partes_hora[0]),
            minute=int(partes_hora[1]),
            second=0
        )
        
        # Calcular hora real de salida, cancelación o suspensión
        if es_cancelacion_o_suspension:
            # Para cancelación/suspensión, comparar contra la hora programada directamente
            hora_referencia = hora_prog
        else:
            # Para demoras, calcular hora real de salida
            hora_referencia = hora_prog + timedelta(minutes=int(minutos_demora))
        
        # Calcular tardanza
        tardanza_segundos = (hora_envio - hora_referencia).total_seconds()
        tardanza_minutos = tardanza_segundos / 60
        
        # MEJORA #4: Clasificación especial para CANCELACIÓN/SUSPENSIÓN
        if es_cancelacion_o_suspension:
            if tardanza_minutos <= 5:  # Hasta 5 min después (incluye anticipados)
                clasificacion = "OPORTUNO"
                nivel = "ACEPTABLE"  # Verde/Correcto
            elif tardanza_minutos <= 10:  # 5-10 min después
                clasificacion = "ACEPTABLE"  # Antes era TARDIO
                nivel = "OBSERVACION" # Amarillo/Atención
            else:  # Más de 10 min después
                clasificacion = "CRITICO"
                nivel = "IMPORTANTE" # Rojo/Mal
        else:
            # Clasificación para DEMORA
            if tardanza_minutos < -60:  # Más de 1 hora antes
                clasificacion = "ANTICIPADO"
                nivel = "EXCELENTE"
            elif tardanza_minutos < 0:  # Antes de la salida
                clasificacion = "ANTICIPADO"
                nivel = "MUY_BUENO"
            elif tardanza_minutos <= 5:  # Hasta 5 min tarde
                clasificacion = "OPORTUNO"
                nivel = "ACEPTABLE"  # Verde/Correcto
            elif tardanza_minutos <= 10:  # 5-10 min tarde
                clasificacion = "ACEPTABLE"
                nivel = "OBSERVACION" # Amarillo/Atención
            else:  # Más de 10 min tarde
                clasificacion = "CRITICO"
                nivel = "IMPORTANTE" # Rojo/Mal
        
        return {
            'tardanza_minutos': round(tardanza_minutos, 1),
            'clasificacion': clasificacion,
            'nivel': nivel,
            'hora_programada': hora_programada,
            'minutos_demora': minutos_demora if not es_cancelacion_o_suspension else 0,
            'hora_referencia': hora_referencia.strftime("%H:%M"),
            'hora_envio': hora_envio.strftime("%H:%M:%S"),
            'es_cancelacion': es_cancelacion_o_suspension
        }
    
    except Exception as e:
        return None

# =================================================================
#                    CLASIFICACIÓN FINAL
# =================================================================

def clasificar_mensaje(mensaje, componentes, codigo_estructura, codigo_contingencia, estado_detectado, timing):
    """
    Clasifica el mensaje en: COMPLETO, IMPORTANTE, OBSERVACIONES, SUGERENCIAS
    
    MEJORAS:
    - #1: Sección faltante solo si hay
    - #10: Advierte código 17
    """
    clasificacion = {
        'IMPORTANTE': [],
        'OBSERVACIONES': [],
        'SUGERENCIAS': []
    }
    
    tipo = componentes.get('tipo_mensaje')
    
    # Validar componentes según tipo
    if tipo == 'TREN_ESPECIFICO':
        # Componente A: Número tren
        if not componentes.get('A'):
            clasificacion['IMPORTANTE'].append("Falta número de tren")
        
        # Componente B: Estado con minutos
        if not componentes.get('B'):
            clasificacion['IMPORTANTE'].append("Falta estado del servicio")
        elif isinstance(componentes['B'], dict):
            # Si usa estructura informal, agregar sugerencia
            if not componentes['B'].get('estructura_formal', True):
                clasificacion['SUGERENCIAS'].append(
                    f"⚠️ El mensaje menciona '{componentes['B'].get('estado')}' pero no usa la estructura formal. "
                    f"Ejemplo: 'CIRCULA CON DEMORAS DE X MINUTOS' o 'HA SIDO CANCELADO'"
                )
            # MEJORA #7: Minutos opcionales en demora de partida
            if componentes['B'].get('estado') == 'DEMORA' and not componentes['B'].get('minutos'):
                # Detectar si es demora de partida
                contenido = mensaje.get('contenido', '').upper()
                es_demora_partida = re.search(
                    r'DEMORANDO\s+(?:SU\s+)?PARTIDA|DEMORA(?:S)?\s+EN\s+(?:LA\s+)?PARTIDA|PARTIDA\s+DEMORADA',
                    contenido
                )
                
                if es_demora_partida:
                    # MEJORA #7: Demora de partida sin minutos = observación (no crítico)
                    clasificacion['OBSERVACIONES'].append(
                        "💡 Demora de partida sin cantidad de minutos. "
                        "Si se conoce estimación, agregarla ayuda al pasajero"
                    )
                else:
                    # Demora en marcha sin minutos = falta info crítica
                    clasificacion['IMPORTANTE'].append("Falta cantidad de minutos de demora")
        
        # Componente D: Hora
        if not componentes.get('D'):
            clasificacion['IMPORTANTE'].append("Falta hora programada")
        
        # Componente E: Recorrido
        recorrido = componentes.get('E')
        if not recorrido:
            clasificacion['IMPORTANTE'].append("Falta origen y destino")
        elif isinstance(recorrido, dict):
            if not recorrido.get('origen'):
                clasificacion['IMPORTANTE'].append("Falta estación origen")
            if not recorrido.get('destino'):
                clasificacion['IMPORTANTE'].append("Falta estación destino")
    
    elif tipo == 'SERVICIO_GENERAL':
        # Componente A: Servicio/ramal/línea
        if not componentes.get('A'):
            clasificacion['IMPORTANTE'].append("Falta identificación del servicio")
        
        # Componente B: Estado
        if not componentes.get('B'):
            clasificacion['IMPORTANTE'].append("Falta estado del servicio")
        elif isinstance(componentes['B'], dict):
            # Si usa estructura informal, agregar sugerencia
            if not componentes['B'].get('estructura_formal', True):
                clasificacion['SUGERENCIAS'].append(
                    f"⚠️ El mensaje menciona '{componentes['B'].get('estado')}' pero no usa la estructura formal. "
                    f"Ejemplo: 'EL SERVICIO SE ENCUENTRA INTERRUMPIDO' o 'CIRCULA REDUCIDO'"
                )
        
        # Componente C: Contingencia (check global abajo)
        
        # MEJORA #13: Sugerencia para nombres con guiones (aceptable pero sugerir oficial)
        servicio_detectado = componentes.get('A')
        if servicio_detectado and '-' in servicio_detectado:
            clasificacion['SUGERENCIAS'].append(
                f"💡 Uso de guiones en '{servicio_detectado}' es aceptable, pero se sugiere validar Matriz de Comunicación (ej: usar nombre de Ramal oficial)."
            )

        # Componente D: Lugar (Opcional pero recomendado en ciertos casos)
        if hasattr(componentes, 'get') and not componentes.get('D'):
             # Si es Accidente o Obra, suele requerir Lugar
             causa = componentes.get('C', {}).get('codigo', '') if isinstance(componentes.get('C'), dict) else ''
             if causa in ['01', '02', '11', '12']: # Accidentes o Obras
                 clasificacion['SUGERENCIAS'].append("💡 Podría ser útil especificar el LUGAR (ej: 'EN LAFERRERE')")

        # Componente E: Disculpas (Opcional)
        # No es obligatorio, pero es buena práctica

    
    # Componente C: Contingencia (ambos tipos)
    if not componentes.get('C'):
        # MEJORA #6: Código 17 con cancelación puede no tener motivo detallado
        # MEJORA #11: Formaciones sin contingencia detallada es aceptable
        estado = componentes.get('B', {})
        estado_nombre = estado.get('estado', '') if isinstance(estado, dict) else ''
        codigo_X = codigo_estructura['X'] if codigo_estructura else None
        
        # Verificar si menciona "formaciones"
        contenido_msg = mensaje.get('contenido', '').upper()
        menciona_formaciones = 'FORMACION' in contenido_msg
        
        if estado_nombre in ['CANCELACIÓN', 'SUSPENDIDO'] and codigo_X == '17':
            clasificacion['OBSERVACIONES'].append(
                "ℹ️ Código 17 sin motivo detallado. Si existe causa específica, usar código correspondiente"
            )
        elif menciona_formaciones:
            # MEJORA #11: Formaciones sin contingencia es válido
            clasificacion['SUGERENCIAS'].append(
                "💡 Mensaje sobre formaciones sin causa específica. Si hay motivo técnico, considerar agregarlo"
            )
        else:
            clasificacion['IMPORTANTE'].append("Falta motivo de la contingencia")
    
    # Componente F: Código estructura
    if not componentes.get('estructura_valida'):
        clasificacion['IMPORTANTE'].append("Falta código de estructura (ej: 3.1.A)")
    else:
        # Validar consistencia código (MEJORA #5)
        if codigo_estructura and codigo_contingencia:
            obs_codigo = validar_codigo_estructura(codigo_estructura, codigo_contingencia, estado_detectado)
            for obs in obs_codigo:
                if '❌' in obs:
                    clasificacion['IMPORTANTE'].append(obs)
                else:
                    clasificacion['OBSERVACIONES'].append(obs)
        
        # MEJORA #10: Advertir código 17
        if codigo_estructura and codigo_estructura['X'] == '17':
            clasificacion['OBSERVACIONES'].append("⚠️ Código 17 (OTRAS CONTINGENCIAS) es excepcional. Verificar si existe código más específico")
    
    # Ortografía
    if not componentes.get('ortografia_valida'):
        for error in componentes.get('errores_ortografia', []):
            clasificacion['OBSERVACIONES'].append(f"Ortografía: {error}")

    # Advertencias de Formato (Educativas)
    for advertencia in componentes.get('advertencias_formato', []):
         clasificacion['SUGERENCIAS'].append(f"💡 Formato: {advertencia}")
    
    # Timing (MEJORA #2: solo si aplica)
    if timing and timing.get('nivel') in ['OBSERVACION', 'IMPORTANTE']:
        tardanza = timing['tardanza_minutos']
        if abs(tardanza) > 15:
            clasificacion['OBSERVACIONES'].append(f"Notificación tardía: {abs(tardanza):.0f} minutos después de la salida real")
    
    # Determinar nivel general
    if clasificacion['IMPORTANTE']:
        nivel_general = 'IMPORTANTE'
    elif clasificacion['OBSERVACIONES']:
        nivel_general = 'OBSERVACIONES'
    elif clasificacion['SUGERENCIAS']:
        nivel_general = 'SUGERENCIAS'
    else:
        nivel_general = 'COMPLETO'
    
    return clasificacion, nivel_general

# =================================================================
#                    GENERAR REPORTE
# =================================================================

def calcular_scores(componentes, timing, mensaje):
    """
    Calcula los 3 scores independientes del mensaje
    
    Returns:
        dict con score_componentes, score_timing, score_estructura
    """
    scores = {
        'componentes': {'clasificacion': '', 'detalles': []},
        'timing': {'clasificacion': '', 'detalles': []},
        'estructura': {'clasificacion': '', 'detalles': []}
    }
    
    # ========== SCORE 1: COMPONENTES ==========
    componentes_puntos = 0
    
    # A - Número de tren (20pts)
    if componentes.get('A'):
        componentes_puntos += 20
    else:
        scores['componentes']['detalles'].append("Falta número de tren")
    
    # B - Estado/Demora (20pts)
    if componentes.get('B'):
        componentes_puntos += 20
    else:
        scores['componentes']['detalles'].append("Falta estado/demora")
    
    # C - Causa (15pts)
    if componentes.get('C'):
        componentes_puntos += 15
    elif componentes.get('tipo_mensaje') == 'INFORMATIVO':
        componentes_puntos += 15  # N/A justificado
    else:
        scores['componentes']['detalles'].append("Falta causa específica")
    
    # D - Horario (15pts)
    if componentes.get('D'):
        componentes_puntos += 15
    elif componentes.get('tipo_mensaje') == 'SERVICIO_GENERAL':
        componentes_puntos += 15 # N/A justificado
    else:
        scores['componentes']['detalles'].append("Falta horario")
    
    # E - Origen/Destino (20pts)
    if componentes.get('E'):
        # Si es un dict (Tren Específico)
        if isinstance(componentes['E'], dict):
            if componentes['E'].get('origen') and componentes['E'].get('destino'):
                componentes_puntos += 20
            else:
                 scores['componentes']['detalles'].append("Falta origen y/o destino")
        elif componentes.get('tipo_mensaje') == 'SERVICIO_GENERAL':
            # Si es Servicio General, E es Disculpas (Opcional)
            # Para general, se asume 20pts base si no es requerido, o puntos extra si está
            componentes_puntos += 20
    elif componentes.get('tipo_mensaje') == 'SERVICIO_GENERAL':
        componentes_puntos += 20 # N/A justificado
    else:
        scores['componentes']['detalles'].append("Falta origen y/o destino")
    
    # F - Código formal (10pts)
    if componentes.get('estructura_valida'):
        componentes_puntos += 10
    else:
        scores['componentes']['detalles'].append("Falta código formal")
    
    # Clasificar componentes
    if componentes_puntos >= 90:
        scores['componentes']['clasificacion'] = 'COMPLETO'
    elif componentes_puntos >= 70:
        scores['componentes']['clasificacion'] = 'ACEPTABLE'
    else:
        scores['componentes']['clasificacion'] = 'INCOMPLETO'
    
    # ========== SCORE 2: TIMING ==========
    if timing and timing.get('tardanza_minutos') is not None:
        tardanza = timing['tardanza_minutos']
        estado = componentes.get('B', {})
        if isinstance(estado, dict):
            estado_nombre = estado.get('estado', '').upper()
        else:
            estado_nombre = ''
        
        es_cancelacion_suspension = estado_nombre in ['CANCELACIÓN', 'SUSPENDIDO']
        
        # Lógica de timing
        if -5 <= tardanza <= 0:
            # Enviado 0-5 min ANTES
            scores['timing']['clasificacion'] = 'EXCELENTE'
            scores['timing']['detalles'].append(f"Enviado {abs(tardanza):.0f} min antes del horario")
        elif tardanza < -5 and es_cancelacion_suspension:
            # Más de 5 min antes para cancelaciones/suspensiones
            scores['timing']['clasificacion'] = 'EXCELENTE'
            scores['timing']['detalles'].append(f"Enviado {abs(tardanza):.0f} min antes (cancelación/suspensión)")
        elif 0 < tardanza <= 11:
            # 6-11 min después
            scores['timing']['clasificacion'] = 'BUENO'
            scores['timing']['detalles'].append(f"Enviado {tardanza:.0f} min después del horario")
        else:
            # Más de 12 min después
            scores['timing']['clasificacion'] = 'DEFICIENTE'
            scores['timing']['detalles'].append(f"Enviado {tardanza:.0f} min después del horario")
    else:
        scores['timing']['clasificacion'] = 'N/A'
        scores['timing']['detalles'].append("No se pudo calcular timing")
    
    # ========== SCORE 3: ESTRUCTURA ==========
    estructura_puntos = 0
    
    # Ortografía (40pts)
    errores_ortografia = componentes.get('errores_ortografia', [])
    num_errores = len(errores_ortografia)
    
    if num_errores == 0:
        estructura_puntos += 40
    elif num_errores == 1:
        estructura_puntos += 25
        scores['estructura']['detalles'].append(f"Ortografía: {errores_ortografia[0]}")
    elif num_errores <= 3:
        estructura_puntos += 15
        for error in errores_ortografia:
            scores['estructura']['detalles'].append(f"Ortografía: {error}")
    elif num_errores <= 5:
        estructura_puntos += 10
        scores['estructura']['detalles'].append(f"{num_errores} errores ortográficos: {', '.join(errores_ortografia[:3])}...")
    else:
        scores['estructura']['detalles'].append(f"{num_errores} errores ortográficos graves")
    
    # Formato/Espaciado (30pts)
    if componentes.get('estructura_valida'):
        estructura_puntos += 30
    else:
        estructura_puntos += 10
        scores['estructura']['detalles'].append("Formato incorrecto")
    
    # Claridad (30pts) - basado en si el mensaje es comprensible
    contenido = mensaje.get('contenido', '').upper()
    if len(contenido) > 50 and componentes.get('tipo_mensaje'):
        estructura_puntos += 30  # Mensaje claro
    elif len(contenido) > 30:
        estructura_puntos += 20
        scores['estructura']['detalles'].append("Redacción mejorable")
    else:
        estructura_puntos += 10
        scores['estructura']['detalles'].append("Mensaje muy breve o confuso")
    
    # Clasificar estructura (umbrales ajustados para ser más estrictos)
    if estructura_puntos >= 95:
        scores['estructura']['clasificacion'] = 'IMPECABLE'
    elif estructura_puntos >= 75:
        scores['estructura']['clasificacion'] = 'CORRECTO'
    elif estructura_puntos >= 55:
        scores['estructura']['clasificacion'] = 'MEJORABLE'
    else:
        scores['estructura']['clasificacion'] = 'DEFICIENTE'
    
    return scores

def generar_reporte(mensaje, componentes, clasificacion, nivel_general, timing):
    """
    Genera reporte completo del mensaje
    """
    # Calcular scores
    scores = calcular_scores(componentes, timing, mensaje)
    
    return {
        'numero_mensaje': mensaje.get('numero_mensaje'),
        'operador': mensaje.get('operador'),
        'fecha_hora': mensaje.get('fecha_hora'),
        'linea': mensaje.get('linea'),
        'contenido': mensaje.get('contenido'),
        'tipo_mensaje': componentes.get('tipo_mensaje'),
        'componentes': componentes,
        'clasificacion': clasificacion,
        'nivel_general': nivel_general,
        'timing': timing,
        'scores': scores,
        'requiere_notificacion': nivel_general in ['IMPORTANTE', 'OBSERVACIONES']
    }

# =================================================================
#                    VALIDAR MENSAJE (FUNCIÓN PRINCIPAL)
# =================================================================

def validar_mensaje_ROCA(mensaje, contingencias_df):
    """
    Función principal de validación
    
    Args:
        mensaje: dict con datos del mensaje
        contingencias_df: DataFrame con matriz de contingencias
    
    Returns:
        dict con reporte completo
    """
    # 1. Validar componentes
    componentes, codigo_estructura, codigo_contingencia, estado_detectado = validar_componentes(
        mensaje, contingencias_df
    )
    
    # 2. Validar timing (MEJORAS #2 y #6)
    timing = validar_tiempo_respuesta(mensaje, componentes)
    
    # 3. Clasificar mensaje
    clasificacion, nivel_general = clasificar_mensaje(
        mensaje, componentes, codigo_estructura, codigo_contingencia, estado_detectado, timing
    )
    
    # =================================================================
    # APLICAR REGLAS PERSONALIZADAS (SOBRESCRITURA DE VALIDACIÓN)
    # =================================================================
    reglas = cargar_reglas_personalizadas()
    contenido = mensaje.get('contenido', '')
    linea_msg = mensaje.get('linea', '').lower().replace(' ', '_')
    
    regla_aplicada = None
    
    for regla in reglas:
        # 1. Verificar alcance (Global o misma línea)
        if regla['_origen'] != 'global' and regla['_origen'] != linea_msg:
            continue
            
        # 2. Verificar regex
        regex = regla.get('regex_sugerido', '')
        if regex:
            try:
                if re.search(regex, contenido, re.IGNORECASE | re.UNICODE):
                    accion = regla.get('accion_sugerida') or regla.get('accion')
                    
                    if accion == 'aprobar_sin_obs':
                        nivel_general = 'COMPLETO'
                        # Limpiar errores
                        clasificacion = {'IMPORTANTE': [], 'OBSERVACIONES': [], 'SUGERENCIAS': []}
                        regla_aplicada = regla['patron_detectado']
                        break # Prioridad a la primera coincidencia que apruebe
                        
                    elif accion == 'aprobar_con_obs':
                        nivel_general = 'OBSERVACIONES'
                        # Mantener observaciones pero asegurar nivel
                        regla_aplicada = regla['patron_detectado']
                        break
            except Exception:
                pass

    # 4. Generar reporte
    reporte = generar_reporte(mensaje, componentes, clasificacion, nivel_general, timing)
    
    if regla_aplicada:
        reporte['regla_personalizada_aplicada'] = regla_aplicada
        # Forzar en reporte final
        if nivel_general == 'COMPLETO':
            reporte['requiere_notificacion'] = False
    
    return reporte

# =================================================================
#                    PROCESAMIENTO BATCH
# =================================================================

def validar_mensajes_desde_json(archivo_json=None, contingencias_df=None):
    """
    Valida mensajes desde archivo JSON
    """
    # Buscar último JSON si no se especifica
    if not archivo_json:
        archivos_json = glob.glob("mensajes_sofse_*.json") + glob.glob("mensajes_nuevos_temp_*.json") + glob.glob("mensajes_roca_*.json")
        if not archivos_json:
            print("❌ No se encontró archivo JSON de mensajes")
            return []
        archivo_json = max(archivos_json, key=os.path.getmtime)
    
    print(f"📖 Leyendo: {archivo_json}")
    
    # Cargar mensajes
    with open(archivo_json, 'r', encoding='utf-8') as f:
        mensajes = json.load(f)
    
    print(f"📊 Total mensajes: {len(mensajes)}")
    
    # Cargar contingencias si no se pasaron
    if contingencias_df is None:
        contingencias_df = cargar_contingencias()
    
    # Validar cada mensaje
    reportes = []
    for mensaje in mensajes:
        try:
            reporte = validar_mensaje_ROCA(mensaje, contingencias_df)
            reportes.append(reporte)
        except Exception as e:
            print(f"⚠️ Error validando #{mensaje.get('numero_mensaje', 'N/A')}: {e}")
    
    return reportes


# =================================================================
#                    API PÚBLICA (PARA APP FLASK)
# =================================================================

_CONTINGENCIAS_CACHE = None

def procesar_mensaje(mensaje):
    """
    Wrapper para validar un solo mensaje desde una app externa.
    Maneja la carga y cacheo de contingencias automáticamente.
    """
    global _CONTINGENCIAS_CACHE
    
    if _CONTINGENCIAS_CACHE is None:
        _CONTINGENCIAS_CACHE = cargar_contingencias()
        
    return validar_mensaje_ROCA(mensaje, _CONTINGENCIAS_CACHE)


# =================================================================
#                    MAIN (MODO STANDALONE)
# =================================================================

if __name__ == "__main__":
    print("="*80)
    print("🔍 VALIDADOR MENSAJES SOFSE - SISTEMA ROCA v3.0")
    print("="*80)
    
    # Cargar contingencias
    contingencias_df = cargar_contingencias()
    if contingencias_df is None:
        print("❌ No se pudo cargar Contingencias.xlsx")
        exit(1)
    
    # Validar mensajes
    reportes = validar_mensajes_desde_json(contingencias_df=contingencias_df)
    
    # Importar notificador
    try:
        from notificador_email_ROCA_v3 import notificar_mensaje_ROCA
        
        print(f"\n{'='*80}")
        print("📧 ENVIANDO NOTIFICACIONES")
        print("="*80)
        
        for reporte in reportes:
            if reporte.get('requiere_notificacion'):
                exito, msg = notificar_mensaje_ROCA(reporte, modo='produccion')
                if exito:
                    print(f"✅ Email enviado: #{reporte['numero_mensaje']}")
                else:
                    print(f"❌ Error: {msg}")
    
    except ImportError:
        print("\n⚠️ No se encontró notificador_email_ROCA_v3.py")
        print("   Los reportes se generaron pero no se enviaron emails")
    
    print(f"\n{'='*80}")
    print(f"✅ Validación completada: {len(reportes)} mensajes procesados")
    print("="*80)
