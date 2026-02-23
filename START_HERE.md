# 🚀 COMIENZA AQUÍ - Antigravity Setup

## ¿Qué cambió?

Tu sistema ya **NO usa IA (Claude, Gemini, OpenAI)**. Ahora usas **Antigravity** (herramienta de Google) para que **Ariel maneje las reglas manualmente sin intervención automática de IA**.

Esto significa:
- ✅ Cero tokens consumidos
- ✅ Cero dependencias de APIs externas
- ✅ Control total en manos de Ariel
- ✅ Reglas personalizadas sin limitaciones de IA

---

## 📋 Archivos Importantes

| Archivo | Propósito |
|---------|-----------|
| **RESUMEN_CAMBIOS.md** | ¿Qué se cambió y por qué? Comienza aquí |
| **ANTIGRAVITY_SETUP.md** | Documentación técnica de endpoints |
| **ANTIGRAVITY_PROMPTS.txt** | Prompts listos para copiar/pegar en Antigravity |
| **CLAUDE.md** | Arquitectura general del proyecto |

---

## 🎯 Inicio Rápido (5 minutos)

### Paso 1: Arrancar Backend
```bash
cd /path/to/auditoria-sofse-react
python app.py
# Backend corre en http://localhost:5000
```

### Paso 2: Arrancar Frontend
```bash
cd frontend
npm run dev
# Frontend corre en http://localhost:5173
```

### Paso 3: Instalar Antigravity
Descargar e instalar desde: https://codelabs.developers.google.com/guides/antigravity

### Paso 4: Configurar Antigravity
- Abrir Antigravity
- Configurar URL: `http://localhost:5000`

### Paso 5: Loguearse en Frontend
- Abrir navegador: `http://localhost:5173`
- Login con: `ariel` / `ariel123`

### Paso 6: Probar
- Ir a Panel de Errores
- Hacer clic en "ABRIR EN ANTIGRAVITY"
- Escribir un prompt (ver ANTIGRAVITY_PROMPTS.txt)

---

## 📞 Prompts Básicos para Empezar

En Antigravity, escribe:

**1. Ver errores:**
```
Mostrá los errores pendientes de validación
```

**2. Crear regla:**
```
Necesito una regla para horarios sin espacios: 14_30HS
Es un FALSO_POSITIVO (el validador marca error pero está bien)
Creá la regla para la línea ROCA
```

**3. Aplicar cambios:**
```
Aplicá todas las reglas a los mensajes pendientes
```

Ver `ANTIGRAVITY_PROMPTS.txt` para 30+ prompts más.

---

## 🔧 Estructura de Carpetas

```
.
├── app.py                           # Backend Flask
├── validador_mensajes.py            # Motor de validación
├── gestor_tandas.py                 # Gestor de estados
├── configs/reglas/                  # Reglas personalizadas
│   ├── globales/personalizadas.json
│   ├── roca/personalizadas.json
│   ├── san_martin/personalizadas.json
│   └── ...
├── frontend/                        # React + Vite
│   ├── src/
│   │   ├── components/PanelErrores.jsx  (✅ Botón ANTIGRAVITY)
│   │   └── App.jsx
│   └── package.json
├── ANTIGRAVITY_SETUP.md             (Documentación técnica)
├── ANTIGRAVITY_PROMPTS.txt          (Prompts listos)
├── RESUMEN_CAMBIOS.md               (Qué se cambió)
└── CLAUDE.md                        (Arquitectura general)
```

---

## ✅ Endpoints Nuevos

Antigravity puede usar estos endpoints del backend:

```
GET  /api/reglas/todas                    → Listar reglas activas
POST /api/reglas/crear                    → Crear nueva regla
POST /api/reglas/modificar/{id}           → Modificar regla
POST /api/reglas/aplicar-todas            → Re-validar todos los mensajes
GET  /api/errores                         → Ver errores derivados
```

Ver `ANTIGRAVITY_SETUP.md` para detalles técnicos.

---

## 🎓 ¿Cómo Funciona?

```
1. Ariel ve error en Panel de Errores
            ↓
2. Hace clic "ABRIR EN ANTIGRAVITY"
            ↓
3. Se abre herramienta Antigravity (Google IDE)
            ↓
4. Antigravity llama a GET /api/reglas/todas
   (trae todas las reglas existentes)
            ↓
5. Ariel y Antigravity trabajan juntos:
   Ariel: "Necesito regla para horarios sin espacios"
   Antigravity: "OK, voy a crearla con este regex"
            ↓
6. Antigravity → POST /api/reglas/crear
   (guarda la regla en configs/reglas/[linea]/personalizadas.json)
            ↓
7. Antigravity → POST /api/reglas/aplicar-todas
   (re-valida todos los mensajes pendientes)
            ↓
8. Mensajes afectados cambian de estado o clasificación
```

---

## 🔒 Seguridad

✅ Seguridad implementada:
- Tokens de IA completamente removidos
- No hay APIs externas
- Solo Ariel puede crear/modificar reglas
- Cookies persisten automáticamente
- No hay exposición de credenciales

---

## 🆘 Troubleshooting

### "No puedo conectar a http://localhost:5000"
- Verificá que `python app.py` está corriendo
- Revisa que no hay error en la terminal del backend

### "Antigravity no encuentra la herramienta"
- Instalá desde: https://codelabs.developers.google.com/guides/antigravity
- Reinicia la computadora después de instalar

### "Tengo error 403 en endpoints"
- Verificá que iniciaste sesión como Ariel en frontend
- Las cookies deben persistir automáticamente

### "La regla se crea pero no se aplica"
- Después de crear, siempre ejecutá: `POST /api/reglas/aplicar-todas`
- Ver `ANTIGRAVITY_PROMPTS.txt` prompt 4.1

---

## 📚 Siguiente Lectura

1. **Lee primero**: `RESUMEN_CAMBIOS.md` (resumen de cambios)
2. **Luego**: `ANTIGRAVITY_SETUP.md` (detalles técnicos)
3. **Finalmente**: `ANTIGRAVITY_PROMPTS.txt` (prompts para usar)

---

## 🎉 Listo!

Tu sistema está completamente preparado. Solo falta:
1. Instalar Antigravity
2. Comenzar a usar los prompts
3. Crear y modificar reglas sin IA

¿Preguntas? Ver `ANTIGRAVITY_SETUP.md` o `ANTIGRAVITY_PROMPTS.txt`.

**¡A trabajar con Antigravity! 🚀**
