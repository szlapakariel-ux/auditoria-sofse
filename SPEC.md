#📋 DOCUMENTO DE ESPECIFICACIÓN TÉCNICA - SOFSE VALIDACIÓN FERROVIARIA

ARQUITECTURA ACTUAL
Stack tecnológico:

Frontend: React + Vite + Tailwind CSS
Backend: Python Flask + Flask-CORS + Flask-Session
IA: Anthropic Claude API (con fallback Gemini)
Persistencia: JSON files (sin base de datos)
Puerto frontend: localhost:5173
Puerto backend: localhost:5000

Estructura de carpetas:
auditoria-sofse-react/
├── app.py                          ← Backend principal Flask
├── gestor_tandas.py                ← Lógica de asignación de mensajes
├── validador_mensajes.py           ← Motor de validación (v3.0, 13 mejoras)
├── inicializar_sistema.py          ← Importa mensajes al sistema
├── limpiar_reglas_duplicadas.py    ← Utilidad de limpieza
├── data/
│   └── mensajes_estado.json        ← Base de datos de mensajes
├── configs/
│   └── reglas/
│       ├── global/
│       │   └── personalizadas.json ← Reglas creadas por Ariel (ACTIVAS)
│       ├── globales/               ← Carpeta alternativa (VACÍA - bug)
│       ├── san_martin/             ← Reglas específicas San Martín (vacía)
│       └── roca/                   ← Reglas específicas Roca (vacía)
└── frontend/
    ├── src/
    │   ├── App.jsx                 ← Router principal
    │   ├── components/
    │   │   ├── Login.jsx           ← Formulario de login
    │   │   ├── SelectorLinea.jsx   ← Selector de líneas con contadores
    │   │   ├── ValidadorMensajes.jsx ← Panel principal de validación
    │   │   ├── MensajeCard.jsx     ← Tarjeta de mensaje con scores
    │   │   ├── MensajesBloqueados.jsx ← Acordeón colapsable
    │   │   ├── PanelErrores.jsx    ← Panel de Ariel
    │   │   └── AsistenteReglas.jsx ← Chat IA para crear reglas
    │   └── services/
    │       └── api.js              ← Endpoints mapeados
    └── vite.config.js

DICCIONARIO DE COMPONENTES
BACKEND
app.py
Motor de la aplicación. Maneja sesiones y expone todos los endpoints REST.
Endpoints:
POST /api/login              → Autentica usuario
POST /api/logout             → Cierra sesión
GET  /api/session            → Verifica sesión activa + mensajes asignados
GET  /api/lineas/disponibles → Lista líneas con conteo de pendientes
POST /api/seleccionar-linea  → Asigna tanda + devuelve bloqueados
POST /api/validar            → Procesa ENVIAR o REPORTAR
GET  /api/errores            → Lista mensajes DERIVADO_A_ARIEL
POST /api/errores/devolver   → Bloquea mensaje y lo devuelve al validador
POST /api/reglas/buscar      → Busca regla existente por patrón
POST /api/reglas/verificar-conflictos → Detecta contradicciones
POST /api/reglas/crear       → Guarda regla + re-valida mensajes
POST /api/analizar-regla-ia  → Chat multi-turno con Claude
Usuarios hardcodeados:
pythonUSUARIOS = {
    'patricia': {'password': 'patricia123', 'nombre': 'Patricia', 'rol': 'validador'},
    'diego':    {'password': 'diego123',    'nombre': 'Diego',    'rol': 'validador'},
    'ariel':    {'password': 'ariel123',    'nombre': 'Ariel',    'rol': 'supervisor'}
}

gestor_tandas.py
Gestiona la asignación y estado de mensajes.
Métodos clave:
pythonimportar_desde_validador(ruta_json)
    → Lee lote_revision_historico.json
    → Lee estructura: msg['analisis']['clasificacion']
    → Lee estructura: msg['analisis']['scores']

asignar_tanda(usuario, linea)
    → Solo asigna PENDIENTES (excluye bloqueados)
    → Devuelve máximo 5 mensajes

obtener_mensajes_asignados(usuario)
    → Filtra por estado ASIGNADO_{USUARIO}
    → Excluye bloqueados

obtener_bloqueados(usuario)
    → Filtra estado ASIGNADO_{USUARIO} + bloqueado==True

contar_pendientes_por_linea()
    → Para el selector de líneas

_guardar_mensajes()
    → Persiste data/mensajes_estado.json
```

**Estados posibles de un mensaje:**
```
PENDIENTE          → Sin asignar
ASIGNADO_PATRICIA  → Patricia lo tiene en su tanda
ASIGNADO_DIEGO     → Diego lo tiene en su tanda
COMPLETADO         → Validado y enviado
DERIVADO_A_ARIEL   → Reportado como error por validador
```

**Campos especiales:**
```
bloqueado: true/false     → Ariel lo devolvió bloqueado
explicacion_ariel: texto  → Motivo del bloqueo
derivado_por: nombre      → Quién lo derivó
comentario_validador: texto → Por qué creen que el sistema se equivocó

validador_mensajes.py (v3.0 - 13 mejoras)
Motor de validación de mensajes. NO está conectado a app.py en tiempo real.
Funciona offline: Se ejecuta sobre el lote histórico para generar lote_revision_historico.json.
Estructura de salida por mensaje:
json{
  "id": "00649214",
  "contenido": "3.1.A EL TREN...",
  "analisis": {
    "nivel_general": "IMPORTANTE",
    "clasificacion": {
      "IMPORTANTE": ["Falta origen y destino"],
      "OBSERVACIONES": ["Formato de hora alternativo"],
      "SUGERENCIAS": []
    },
    "scores": {
      "componentes": {"clasificacion": "ACEPTABLE", "valor": 65},
      "timing": {"clasificacion": "BUENO", "valor": 80},
      "estructura": {"clasificacion": "IMPECABLE", "valor": 95}
    },
    "componentes": {
      "A": "3361",
      "B": {"estado": "DEMORA"},
      "C": {"forma_comunicacion": "PROBLEMAS TECNICOS"},
      "D": "10:44",
      "F": "3.1.A"
    },
    "timing": {
      "hora_programada": "10:44",
      "hora_envio": "11:05:20",
      "diferencia_minutos": 21.3
    }
  }
}
```

---

## FRONTEND

### `App.jsx`
Router principal. Maneja 4 vistas:
```
login → selectorLinea → validador → (panelErrores solo Ariel)
Login.jsx
Formulario simple. Llama a POST /api/login.
SelectorLinea.jsx
Muestra líneas disponibles con contador de mensajes pendientes.
Llama a GET /api/lineas/disponibles.
ValidadorMensajes.jsx
Panel principal de Patricia/Diego.
Estados:
javascriptmensajes          → Tanda normal (5 mensajes)
mensajesBloqueados → Mensajes devueltos por Ariel
currentIndex      → Posición actual en la tanda
validadosHoy      → Contador del día
```

**Flujo:**
```
1. Carga mensajes desde props (mensajesIniciales)
2. Separa bloqueados de normales (deduplica por ID)
3. Muestra acordeón de bloqueados arriba (colapsado)
4. Muestra mensaje actual abajo
5. handleEnviar → POST /api/validar accion='ENVIAR'
6. handleReportarError → POST /api/validar accion='REPORTAR'
7. Avanza al siguiente o carga nueva tanda
```

### `MensajeCard.jsx`
Tarjeta completa del mensaje con toda la información.

**Secciones con color dinámico según score:**
```
🔴/🟡/🟢 Contenido del mensaje (color según estructura)
📦 Componentes incluidos (color según componentes)
⏱️ Timing expandido (color según timing)
🔴 Errores importantes (siempre rojo)
🟡 Observaciones (siempre amarillo)
💡 Sugerencias (siempre azul)
Props:
javascriptmensaje      → Objeto completo del mensaje
onEnviar     → Callback al enviar
onReportarError → Callback al reportar
bloqueado    → Boolean, deshabilita botones si true
```

**Popup de reporte:**
```
Muestra: contenido + observación del sistema
Pide: comentario del validador (textarea)
Envía: accion='REPORTAR' + comentario
```

### `MensajesBloqueados.jsx`
Acordeón colapsable amarillo.
- Por defecto: colapsado
- Expandido: muestra lista con explicación de Ariel
- Botón [VER MENSAJE COMPLETO] → abre modal solo lectura

### `PanelErrores.jsx`
Panel exclusivo de Ariel.
- Lista mensajes DERIVADO_A_ARIEL
- 2 botones por mensaje: [CREAR REGLA] [DEVOLVER]
- [CREAR REGLA] → abre AsistenteReglas.jsx
- [DEVOLVER] → popup con textarea → bloquea mensaje

### `AsistenteReglas.jsx`
Chat libre multi-turno con Claude IA.

**Flujo:**
```
1. Se abre al costado (panel lateral derecho, w-96)
2. Inicia análisis automático del comentario del validador
3. Ariel puede chatear libremente para replantear
4. IA conoce: reglas actuales + lógica del validador
5. Cuando tiene regla lista → muestra botón [Crear regla]
6. Verifica conflictos antes de crear
7. Crea regla + re-valida mensajes pendientes
8. Muestra resultado: cuántos mensajes afectó
```

---

# SISTEMA DE REGLAS

## Arquitectura:
```
configs/reglas/
├── global/personalizadas.json     ← ACTIVO (5 reglas creadas)
├── globales/personalizadas.json   ← VACÍO (bug: nombre diferente)
├── san_martin/personalizadas.json ← VACÍO
└── roca/personalizadas.json       ← VACÍO
Estructura de cada regla:
json{
  "id": "c3ff587f",
  "patron_detectado": "Formato alternativo DE/HACIA",
  "regex_sugerido": "(?:DE|DESDE)\\s+...",
  "accion_sugerida": "aprobar_sin_obs | aprobar_con_obs | rechazar",
  "tipo": "FALSO_POSITIVO | FALSO_NEGATIVO",
  "linea": "global | san_martin | roca",
  "creada_por": "Ariel",
  "fecha_creacion": "2026-02-11T13:43:35",
  "activa": true,
  "mensaje_origen": "00648851"
}
```

## Prioridad de reglas:
```
1. Regla específica de línea (san_martin, roca)
2. Regla global
3. Validador estándar (Python hardcodeado)
```

## Problema conocido:
El sistema guarda en `configs/reglas/global/` pero busca en `configs/reglas/globales/`. Causa que no encuentre reglas existentes al buscar.

---

# FLUJO COMPLETO DEL SISTEMA
```
OFFLINE (preparación):
validador_mensajes.py → analiza mensajes → lote_revision_historico.json
inicializar_sistema.py → importa al sistema → data/mensajes_estado.json

ONLINE (operación):
Patricia/Diego → login → selector línea → tanda de 5 mensajes
    ↓
[ENVIAR] → mensaje COMPLETADO → TODO: email al operador
    ↓
[REPORTAR ERROR] → comentario → DERIVADO_A_ARIEL
    ↓
Ariel → Panel Errores → ve mensaje + comentario
    ↓
[DEVOLVER] → bloquea → Patricia ve acordeón amarillo
    ↓
[CREAR REGLA] → AsistenteReglas (chat IA)
    → analiza comentario del validador
    → busca regla existente
    → crea/amplía regla
    → re-valida mensajes pendientes
```

---

# BACKLOG - PENDIENTES

## 🔴 CRÍTICO:
```
1. Conectar validador_mensajes.py a app.py
   → Cuando se crea regla, re-validar usando el motor completo
   → No solo cambiar nivel_general con regex simple
   → Actualmente: solo actualiza nivel_general
   → Debería: actualizar clasificacion + scores + componentes

2. Implementar envío de emails
   → Al hacer [ENVIAR], notificar al operador
   → Ya existe notificador_email_ROCA_v3.py
   → Solo falta conectarlo a app.py línea 134

3. Unificar carpetas de reglas
   → Bug: guarda en global/ pero busca en globales/
   → Fix: normalizar todas las rutas a globales/
```

## 🟡 IMPORTANTE:
```
4. Limpiar reglas duplicadas
   → Mismo patrón @T guardado 3 veces
   → Ejecutar: python limpiar_reglas_duplicadas.py

5. El AsistenteReglas confunde los dos sistemas
   → IA no distingue validador original de reglas JSON
   → Fix: mejorar system prompt (en proceso)

6. Re-validación no actualiza scores ni clasificacion
   → Solo cambia nivel_general
   → Patricia ve colores actualizados pero observaciones viejas
```

## 🔵 MEJORAS FUTURAS:
```
7. Deploy a Render/Railway
   → Variables de entorno configuradas
   → Falta: migrar JSON a base de datos real

8. Panel de estadísticas
   → Cuántos mensajes por operador
   → Tasa de falsos positivos por línea

9. Historial de reglas
   → Ver qué reglas creó Ariel y cuándo
   → Poder desactivar reglas sin borrarlas

10. Agregar líneas Mitre, Sarmiento, Belgrano Sur
    → Actualmente: solo San Martín y Roca configuradas
```

---

# REGLAS DE ORO
```
1. SEPARACIÓN DE RESPONSABILIDADES
   El validador analiza. El gestor asigna. El frontend muestra.
   Nunca mezclar lógica de negocio en el frontend.

2. ESTADOS EXPLÍCITOS
   Cada mensaje tiene un estado claro.
   Nunca inferir estado por ausencia de campos.

3. NO ROMPER LO QUE FUNCIONA
   Antes de modificar un endpoint, verificar qué componentes lo usan.
   Cambios en backend siempre con try/except.

4. DEDUPLICAR SIEMPRE
   Mensajes bloqueados pueden aparecer duplicados.
   Siempre filtrar por ID único antes de mostrar.

5. REGLAS JSON NO MODIFICAN EL VALIDADOR
   Son capas adicionales, no reemplazos.
   El validador original (Python) es la fuente de verdad inicial.

6. ARIEL TIENE CONTROL TOTAL
   Ninguna acción sobre reglas o mensajes se ejecuta sin confirmación de Ariel.
   El sistema sugiere, Ariel decide.
```

---

# LOG DE DECISIONES
```
[2026-01-20] Migración de Tkinter a React + Flask
  → Razón: interfaz más moderna y multi-usuario

[2026-01-25] Gestor de tandas con estado en JSON
  → Razón: sin base de datos para simplificar deploy
  → Riesgo: concurrencia si múltiples usuarios simultáneos

[2026-02-01] Validación offline + importación
  → Razón: validador_mensajes.py es complejo, no se puede conectar fácil
  → Pendiente: conectar para re-validación en tiempo real

[2026-02-05] Flujo de validación simplificado
  → Solo 2 botones: ENVIAR y REPORTAR ERROR
  → Eliminados: APROBAR y RECHAZAR del panel de Ariel

[2026-02-10] AsistenteReglas con chat multi-turno
  → Usa Claude API (Anthropic)
  → Fallback a Gemini si falla
  → System prompt incluye reglas actuales dinámicamente

[2026-02-11] Problema detectado: carpeta global vs globales
  → Reglas se guardan en configs/reglas/global/
  → Sistema busca en configs/reglas/globales/
  → Fix pendiente: unificar rutas
 Informe Técnico de Sincronización

Aquí tenés el estado real del sistema al día de hoy. No se ha generado código nuevo, solo una auditoría de lo existente.

## 1. Estructura de Directorios Real
El proyecto tiene una estructura híbrida (Python en raíz, React en `frontend`).

```
C:\Users\szlap\OneDrive\Desktop\auditoria-sofse-react\
├── app.py                      # Backend Flask Principal
├── validador_mensajes.py       # Lógica de Validación (Core)
├── gestor_tandas.py            # Lógica de asignación de mensajes
├── scraper_mensajes.py         # Extracción de datos (Selenium)
├── inicializar_sistema.py      # Script de arranque
├── cleaning_scripts/           # Scripts de mantenimiento
│   └── limpiar_reglas_duplicadas.py
├── configs/                    # Configuraciones y Reglas
│   ├── config_roca.json
│   ├── Contingencias.xlsx
│   └── reglas/                 # Carpetas de Reglas por Línea
│       ├── global/             # Reglas Globales (personalizadas.json)
│       ├── globales/           # (Legacy) componentes y estructura
│       ├── san_martin/         # (Vacía) personalizadas.json
│       ├── roca/               # (Vacía) personalizadas.json
│       ├── mitre/              # (Vacía) personalizadas.json
│       ├── sarmiento/          # (Vacía) personalizadas.json
│       ├── belgrano_sur/       # (Vacía) personalizadas.json
│       └── tren_de_la_costa/   # (Vacía) personalizadas.json
└── frontend/                   # Aplicación React
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx             # Componente Raíz
        └── components/
            ├── Login.jsx
            ├── SelectorLinea.jsx
            ├── ValidadorMensajes.jsx
            ├── MensajeCard.jsx
            ├── AsistenteReglas.jsx # Chat IA
            └── PanelErrores.jsx
```

## 2. Estado de los Componentes (React)

| Componente | Estado | Funcionalidad |
| :--- | :--- | :--- |
| **Login** | ✅ Funcional | Autenticación contra backend Flask. |
| **SelectorLinea** | ✅ Funcional | Permite elegir entre las 6 líneas configuradas. |
| **ValidadorMensajes** | ✅ Funcional | Muestra tarjetas, gestiona estados de aprobación y bloqueo. |
| **MensajeCard** | ✅ Funcional | Renderiza detalles, scores visuales y botón de reporte. |
| **AsistenteReglas** | ✅ Funcional | **Nuevo chat libre**. Conecta con endpoint `/api/analizar-regla-ia`. |
| **PanelErrores** | ⚠️ Pendiente | Aparentemente funcional, pero depende de lógica de admin (User: Ariel). |

## 3. Dependencias Reales

### Frontend (`frontend/package.json`)
*   **Core:** `react`, `react-dom`
*   **Http:** `axios` (aunque algunos componentes usan `fetch` nativo).
*   **UI/Iconos:** `lucide-react`, `tailwindcss`.
*   **Build:** `vite`.

### Backend (`requirements.txt` + `app.py`)
*   **Web Framework:** `Flask`, `Flask-CORS`.
*   **Datos:** `pandas`, `openpyxl` (para Excel).
*   **AI:** `anthropic` (Claude), `openai` (GPT), `requests` (para Gemini REST API).
*   **Utilidades:** `python-dotenv` (Variables de entorno), `selenium` (Scraper).

## 4. Flujo de Datos Actual

1.  **Carga:** `App.jsx` verifica sesión -> `SelectorLinea` pide líneas al backend.
2.  **Validación:** `ValidadorMensajes` recibe lote de mensajes (`gestor_tandas.py`).
3.  **Análisis IA:**
    *   `AsistenteReglas.jsx` envía mensaje + historial a `app.py`.
    *   `app.py` construye prompt del sistema con reglas de `configs/reglas/global`.
    *   `app.py` intenta conectar Secuencialmente: **Claude -> Gemini -> OpenAI**.
    *   Respuesta IA vuelve al chat. Si hay JSON de regla, frontend muestra botón "Crear Regla".
4.  **Creación Regla:** Frontend envía JSON a `/api/reglas/crear`, Backend guarda en `configs/reglas/global/personalizadas.json` (por defecto actual).

## 5. Deuda Técnica y Alertas ⚠️

1.  **Reglas "Globales":**
    *   Acabamos de unificar todo en `global`, pero el código mantiene lógica de búsqueda en carpetas vacías (`san_martin`, etc.). Funciona bien ahora porque están vacías y forzamos la búsqueda global primero, pero es una estructura que hay que mantener limpia.
    *   **Alerta:** Si alguien crea una regla "local" en el futuro en `configs/reglas/san_martin/`, el sistema la leerá **después** de las globales (orden corregido).

2.  **Validación de Código 17:**
    *   Se implementó la advertencia visual para código 17 ("Otras Contingencias"), pero **depende críticamente** de que el regex detecte el código `17.X.X`. El regex fue mejorado para aceptar guiones, pero sigue siendo un punto delicado si los operadores escriben muy mal el código.

3.  **Parsers Rígidos:**
    *   Como vimos con los mensajes de Susana y Claudio, el validador original (`validador_mensajes.py`) es muy estricto con espacios y paréntesis. Las reglas JSON son el parche, pero requieren mantenimiento constante (crear reglas nuevas) para cada variación humana.

4.  **Consistencia de Archivos:**
    *   Existen carpetas `global` (sin S) y `globales` (con S). El código busca en ambas por compatibilidad, pero sería ideal migrar todo a una sola carpeta canónica en el futuro para evitar confusiones.
