import json
from datetime import datetime
from pathlib import Path

class GestorTandas:
    def __init__(self, archivo_mensajes='data/mensajes_estado.json'):
        self.archivo = Path(archivo_mensajes)
        self.mensajes = self._cargar_mensajes()
    
    def _cargar_mensajes(self):
        if self.archivo.exists():
            with open(self.archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _guardar_mensajes(self):
        self.archivo.parent.mkdir(exist_ok=True)
        with open(self.archivo, 'w', encoding='utf-8') as f:
            json.dump(self.mensajes, f, ensure_ascii=False, indent=2)
    
    def asignar_tanda(self, usuario, linea):
        """
        Asigna 5 mensajes PENDIENTES (NO bloqueados)
        Los bloqueados se muestran aparte en el acordeón
        """
        # Buscar SOLO mensajes PENDIENTES de esa línea
        pendientes = [
            m for m in self.mensajes 
            if m['estado'] == 'PENDIENTE' and m['linea'] == linea
        ]
        
        # Tomar los primeros 5
        tanda = pendientes[:5]
        
        # Marcarlos como asignados
        for mensaje in tanda:
            mensaje['estado'] = f'ASIGNADO_{usuario.upper()}'
            mensaje['asignado_a'] = usuario
            mensaje['linea_asignada'] = linea
            mensaje['asignado_en'] = datetime.now().isoformat()
        
        self._guardar_mensajes()
        return tanda

    def obtener_bloqueados(self, usuario):
        """Obtiene mensajes bloqueados para este usuario"""
        return [
            m for m in self.mensajes 
            if m['estado'] == f'ASIGNADO_{usuario.upper()}' 
            and m.get('bloqueado', False) == True
        ]
    
    def procesar_mensaje(self, mensaje_id, accion, usuario):
        mensaje = next((m for m in self.mensajes if m['id'] == mensaje_id), None)
        if not mensaje:
            return False
        if accion == 'ENVIAR':
            mensaje['estado'] = 'COMPLETADO'
        elif accion == 'REPORTAR' or accion == 'REPORTAR_ERROR':
            mensaje['estado'] = 'DERIVADO_A_ARIEL'
        mensaje['procesado_por'] = usuario
        mensaje['procesado_en'] = datetime.now().isoformat()
        self._guardar_mensajes()
        return True
    
    def contar_asignados(self, usuario):
        return len([m for m in self.mensajes if m['estado'] == f'ASIGNADO_{usuario.upper()}'])
    
    def liberar_mensajes(self, usuario):
        for mensaje in self.mensajes:
            if mensaje['estado'] == f'ASIGNADO_{usuario.upper()}':
                mensaje['estado'] = 'PENDIENTE'
                mensaje['asignado_a'] = None
        self._guardar_mensajes()
    
    def obtener_mensajes_asignados(self, usuario):
        return [m for m in self.mensajes if m['estado'] == f'ASIGNADO_{usuario.upper()}']
    
    def contar_pendientes_por_linea(self):
        conteo = {}
        for mensaje in self.mensajes:
            if mensaje['estado'] == 'PENDIENTE':
                linea = mensaje['linea']
                conteo[linea] = conteo.get(linea, 0) + 1
        return conteo
    
    def importar_desde_validador(self, ruta_json_validador):
        """Importa mensajes desde el JSON del validador"""
        try:
            with open(ruta_json_validador, 'r', encoding='utf-8') as f:
                mensajes_validador = json.load(f)
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {ruta_json_validador}")
            return

        self.mensajes = []
        
        for msg in mensajes_validador:
            # CRÍTICO: Los datos están dentro de 'analisis'
            # Usamos .get({}, {}) para asegurarnos de que si analisis es None, sea {}
            analisis = msg.get('analisis') or {}
            
            self.mensajes.append({
                'id': msg.get('numero_mensaje'),
                'contenido': msg.get('contenido'),
                'operador': msg.get('operador'),
                'linea': msg.get('linea'),
                'fecha_hora': msg.get('fecha_hora'),
                'tipo_mensaje': analisis.get('tipo_mensaje'),
                'estado': 'PENDIENTE',
                'asignado_a': None,
                'asignado_en': None,
                'procesado_por': None,
                'procesado_en': None,
                'nivel_general': analisis.get('nivel_general', 'OBSERVACIONES'),
                'clasificacion': analisis.get('clasificacion', {}),
                'scores': analisis.get('scores', {}),
                'componentes': analisis.get('componentes', {}),
                'timing': analisis.get('timing')
            })
        
        self._guardar_mensajes()
        print(f"Importados {len(self.mensajes)} mensajes correctamente")
