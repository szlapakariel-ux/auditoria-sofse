
import json
import os
import re
from pathlib import Path

# Configuración
ARCHIVO_MENSAJES = 'data/mensajes_estado.json'
DIR_REGLAS = 'configs/reglas'

def cargar_mensajes():
    if not os.path.exists(ARCHIVO_MENSAJES):
        print("❌ No se encontró el archivo de mensajes.")
        return []
    with open(ARCHIVO_MENSAJES, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_mensajes(mensajes):
    with open(ARCHIVO_MENSAJES, 'w', encoding='utf-8') as f:
        json.dump(mensajes, f, indent=2, ensure_ascii=False)
    print("✅ Mensajes guardados correctamente.")

def cargar_todas_las_reglas():
    reglas = []
    # Buscar en todas las subcarpetas de configs/reglas
    for ruta in Path(DIR_REGLAS).rglob('personalizadas.json'):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                nombre_linea = ruta.parent.name
                for r in data.get('reglas', []):
                    r['origen_archivo'] = nombre_linea # Para saber si es global o de línea
                    reglas.append(r)
        except Exception as e:
            print(f"⚠️ Error cargando reglas de {ruta}: {e}")
    return reglas

def aplicar_cambios():
    mensajes = cargar_mensajes()
    reglas = cargar_todas_las_reglas()
    
    if not mensajes:
        return

    print(f"📋 Analizando {len(mensajes)} mensajes con {len(reglas)} reglas personalizadas...")
    
    contador_afectados = 0
    
    for mensaje in mensajes:
        # Solo procesamos mensajes que NO estén ya completados/rechazados manualmente
        # Opcional: Re-procesar TODO si quieres corregir incluso lo validado manualmente,
        # pero por seguridad, enfoquémonos en lo pendiente/automático.
        # Si quieres TODO, comenta la siguiente línea.
        # if mensaje.get('nivel_general') == 'COMPLETO': continue 
        
        texto = mensaje.get('contenido', '')
        linea_msg = mensaje.get('linea', '').lower().replace(' ', '_')
        
        cambio_realizado = False
        
        for regla in reglas:
            # 1. Verificar alcance (Global o misma línea)
            if regla['origen_archivo'] != 'global' and regla['origen_archivo'] != linea_msg:
                continue
                
            # 2. Verificar regex
            regex = regla.get('regex_sugerido', '')
            if not regex: continue
            
            try:
                match = re.search(regex, texto, re.IGNORECASE | re.UNICODE)
                if match:
                    # ¡Coincidencia! Aplicar acción
                    accion = regla.get('accion_sugerida') or regla.get('accion')
                    
                    # Guardar estado anterior para log
                    estado_anterior = mensaje.get('nivel_general', 'N/A')
                    
                    if accion == 'aprobar_sin_obs':
                        mensaje['nivel_general'] = 'COMPLETO'
                        # Si estaba reportado, lo limpiamos
                        if mensaje.get('estado') == 'DERIVADO_A_ARIEL':
                            mensaje['estado'] = 'PENDIENTE'
                        
                        # Limpiar errores del sistema (Importante)
                        if 'clasificacion' in mensaje:
                            mensaje['clasificacion']['IMPORTANTE'] = [] # Limpiar errores
                            mensaje['clasificacion']['OBSERVACIONES'] = [] # Limpiar obs
                            
                    elif accion == 'aprobar_con_obs':
                        mensaje['nivel_general'] = 'OBSERVACIONES'
                        if mensaje.get('estado') == 'DERIVADO_A_ARIEL':
                            mensaje['estado'] = 'PENDIENTE'
                    
                    if mensaje.get('nivel_general') != estado_anterior:
                         print(f"✅ Mensaje {mensaje['id']} ({linea_msg}) corregido por regla '{regla['patron_detectado']}'")
                         cambio_realizado = True
                         contador_afectados += 1
                         break # Una regla es suficiente, pasamos al siguiente mensaje
                         
            except Exception as e:
                # print(f"Error regex en mensaje {mensaje['id']}: {e}")
                pass
                
    if contador_afectados > 0:
        print(f"\n✨ Se actualizaron {contador_afectados} mensajes por las reglas personalizadas.")
        guardar_mensajes(mensajes)
    else:
        print("\n👍 Ningún mensaje requirió cambios (ya estaban correctos o ninguna regla aplicó).")

if __name__ == "__main__":
    aplicar_cambios()
