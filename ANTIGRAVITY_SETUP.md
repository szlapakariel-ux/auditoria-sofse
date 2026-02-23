# Integración Antigravity - Gestión de Reglas

## 🎯 Descripción

Esta guía permite que **Antigravity (agente de Google)** se conecte a tu backend para:
1. Ver errores pendientes de validación
2. Trabajar con Ariel para definir/modificar reglas
3. Aplicar reglas a todos los mensajes pendientes

## 📡 Endpoints Disponibles

### 1. Obtener Errores Derivados
```
GET /api/errores
Headers:
  - Cookie: session=... (mismo de la sesión de Ariel)
Response:
{
  "ok": true,
  "errores": [
    {
      "id": 123,
      "linea": "ROCA",
      "contenido": "...",
      "comentario_validador": "...",
      "derivado_por": "Patricia",
      "clasificacion": {
        "IMPORTANTE": [...],
        "OBSERVACIONES": [...]
      }
    }
  ]
}
```

### 2. Obtener Todas las Reglas Activas
```
GET /api/reglas/todas
Headers:
  - Cookie: session=... (mismo de la sesión de Ariel)
Response:
{
  "ok": true,
  "total": 15,
  "reglas": [
    {
      "id": "a1b2c3d4",
      "patron_detectado": "Horario sin espacios",
      "regex_sugerido": "\\d{2}:\\d{2}",
      "accion_sugerida": "aprobar_sin_obs",
      "tipo": "FALSO_POSITIVO",
      "linea": "global",
      "fecha_creacion": "2024-12-15T...",
      "activa": true
    }
  ]
}
```

### 3. Crear Nueva Regla
```
POST /api/reglas/crear
Headers:
  - Cookie: session=... (mismo de la sesión de Ariel)
  - Content-Type: application/json
Body:
{
  "regla": {
    "patron_detectado": "Horario con guión bajo",
    "regex_sugerido": "\\d{2}_\\d{2}\\s*HS",
    "accion_sugerida": "aprobar_sin_obs",
    "tipo": "FALSO_POSITIVO",
    "linea": "global",
    "mensaje_origen": 123,
    "creada_por": "Antigravity"
  }
}
Response:
{
  "ok": true,
  "regla_id": "xyz789",
  "mensajes_afectados": 5,
  "mensajes_resueltos": 3,
  "mensajes_reclasificados": 2
}
```

### 4. Modificar Regla Existente
```
POST /api/reglas/modificar/{regla_id}
Headers:
  - Cookie: session=... (mismo de la sesión de Ariel)
  - Content-Type: application/json
Body:
{
  "actualizaciones": {
    "regex_sugerido": "\\d{2}[:_.]\\d{2}\\s*HS",
    "patron_detectado": "Variantes de horario"
  }
}
Response:
{
  "ok": true,
  "mensaje": "Regla modificada",
  "regla": {...}
}
```

### 5. Aplicar Todas las Reglas (Re-validar)
```
POST /api/reglas/aplicar-todas
Headers:
  - Cookie: session=... (mismo de la sesión de Ariel)
Response:
{
  "ok": true,
  "mensaje": "Re-validación completada",
  "mensajes_resueltos": 8,
  "mensajes_reclasificados": 4,
  "total_afectados": 12
}
```

## 🚀 Cómo Antigravity Interactúa

### Paso 1: Ariel abre Antigravity
```
Ariel hace clic en "ABRIR EN ANTIGRAVITY" en Panel de Errores
↓
Se abre Antigravity (herramienta Google) en un contexto con:
  - error_id: ID del mensaje derivado
  - url_api: http://localhost:5000 (o URL de producción)
```

### Paso 2: Antigravity solicita los errores
```
Antigravity → GET /api/errores
↓
Backend retorna lista de errores derivados
```

### Paso 3: Antigravity trabaja con Ariel
```
Antigravity: "Veo que el error es formato de horario."
Ariel: "Sí, necesito que detecte también formato con guión bajo"
Antigravity: "OK, voy a crear una regla que cubra ambos"
```

### Paso 4: Antigravity crea o modifica regla
```
Antigravity → POST /api/reglas/crear (o POST /api/reglas/modificar)
↓
Backend guarda la regla en configs/reglas/[linea]/personalizadas.json
```

### Paso 5: Antigravity aplica a todos
```
Antigravity → POST /api/reglas/aplicar-todas
↓
Backend re-valida todos los mensajes pendientes
↓
Mensajes afectados cambian de estado o clasificación
```

## 🔐 Seguridad

- ✅ **Solo Ariel puede crear/modificar reglas** (validación por sesión)
- ✅ **Cookies de sesión persisten** entre Antigravity y backend
- ✅ **CORS habilitado** para localhost:5173 y localhost:5000

## 📋 Estructura JSON de Regla

```json
{
  "id": "a1b2c3d4",
  "patron_detectado": "Descripción clara del patrón detectado",
  "regex_sugerido": "Expresión regular Python válida",
  "accion_sugerida": "aprobar_sin_obs | aprobar_con_obs | rechazar",
  "tipo": "FALSO_POSITIVO | FALSO_NEGATIVO",
  "linea": "global | roca | san_martin | mitre | sarmiento | belgrano_sur | tren_de_la_costa",
  "fecha_creacion": "ISO timestamp",
  "fecha_modificacion": "ISO timestamp (opcional)",
  "activa": true,
  "mensaje_origen": 123,
  "creada_por": "Ariel | Antigravity"
}
```

## 🛠️ Tipos de Reglas

### FALSO_POSITIVO
- El validador marcó error pero el mensaje está correcto
- Ejemplo: Horario sin dos puntos `14_30` es interpretado como `14:30`

### FALSO_NEGATIVO
- El validador NO detectó un error que realmente existe
- Ejemplo: Un formato de estado no reconocido como válido

## 📁 Ubicación de Reglas

Las reglas se guardan en:
```
configs/reglas/
├── globales/
│   └── personalizadas.json      (Reglas para todas las líneas)
├── roca/
│   └── personalizadas.json      (Reglas específicas ROCA)
├── san_martin/
│   └── personalizadas.json
├── mitre/
│   └── personalizadas.json
├── sarmiento/
│   └── personalizadas.json
├── belgrano_sur/
│   └── personalizadas.json
└── tren_de_la_costa/
    └── personalizadas.json
```

## 🔄 Flujo Completo Ejemplo

```
1. Ariel ve error: "Horario sin espacios 14_30HS"
   ↓
2. Hace clic "ABRIR EN ANTIGRAVITY"
   ↓
3. Antigravity accede a GET /api/errores
   ↓
4. Antigravity analiza el error y pide:
   "¿Creo regla para detectar horarios con guión bajo?"
   ↓
5. Ariel confirma: "Sí, pero también con punto: 14.30HS"
   ↓
6. Antigravity ajusta regex: "\\d{2}[:_.]\\d{2}\\s*HS"
   ↓
7. Antigravity → POST /api/reglas/crear
   ↓
8. Backend guarda regla en configs/reglas/roca/personalizadas.json
   ↓
9. Antigravity → POST /api/reglas/aplicar-todas
   ↓
10. Backend re-valida todos los mensajes
    ↓
11. Mensajes con ese formato ahora pasan validación ✅
```

## ⚙️ Variables de Entorno

No se necesitan tokens de IA (se eliminaron todos).

Variables necesarias:
- `SECRET_KEY`: Para sesiones Flask
- `RENDER_EXTERNAL_URL`: URL pública en Render (si aplica)

## 🧪 Testing Local

```bash
# Terminal 1: Backend
python app.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Antigravity
# Abre Antigravity desde tu computadora
# Configura URL: http://localhost:5000
# Autentica como Ariel
```

## 📝 Prompts Sugeridos para Antigravity

### Para listar errores:
```
"Mostrá los últimos 10 errores derivados"
```

### Para crear regla:
```
"El mensaje #123 tiene horario sin espacios (14_30HS).
Creá una regla FALSO_POSITIVO que detecte este patrón
y lo apruebe sin observaciones"
```

### Para modificar regla:
```
"Ampliá la regla 'a1b2c3d4' para que también detecte
puntos entre horas: 14.30HS además de 14_30HS"
```

### Para aplicar cambios:
```
"Aplicá todas las reglas actuales a los mensajes pendientes
y mostrá cuántos se resolvieron"
```
