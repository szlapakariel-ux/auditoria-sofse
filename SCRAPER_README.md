# 🚂 SOFSE VPN Scraper - Documentación

## Estado Actual ✅

El scraper **funciona correctamente** con la siguiente arquitectura:

### Decisiones Técnicas Finales

#### ❌ Lo que NO funcionó
1. **Playwright Chromium descargado** - Tenía problemas de extracción corrupta
   - Error: `Executable doesn't exist` aunque el archivo existía físicamente
   - Causa: Descarga/extracción incompleta del .zip de Chromium
   - **Solución**: Usar Chrome del sistema en su lugar

2. **Sesión persistente** (`launch_persistent_context`)
   - Problemas: `about:blank`, conflictos con Chrome abierto, sesión perdida
   - Causa: Conflictos entre user_data_dir y el perfil real de Chrome
   - **Solución**: Usar cookies guardadas en JSON

3. **`page.triple_click()`**
   - Error: `'Locator' object has no attribute 'triple_click'`
   - **Solución**: Cambiar a `page.click(click_count=3)`

#### ✅ Lo que SÍ funciona
- **Chrome del sistema** (`C:\Program Files\Google\Chrome\Application\chrome.exe`)
  - Reutiliza cookies reales del navegador
  - No interfiere con Chrome abierto
  - Más confiable que Chromium descargado

- **Guardar/Cargar cookies en JSON** (`cookies_vpn.json`)
  - Primera ejecución: pide login manual, guarda cookies
  - Próximas ejecuciones: carga cookies automáticamente
  - Si cookies expiran: pide login nuevamente

- **Contexto normal en vez de persistente**
  ```python
  browser = p.chromium.launch(executable_path=CHROME_PATH)
  context = browser.new_context()
  # Cargar cookies si existen
  if ARCHIVO_COOKIES.exists():
      cookies = json.load(...)
      context.add_cookies(cookies)
  ```

## Uso

### Primera ejecución (requiere login)
```powershell
.\.venv\Scripts\python.exe scraper_vpn.py --linea roca --debug
# Te pide que te loguees manualmente en el navegador que se abre
# Presioná ENTER cuando estés en "Mensajes → Listado"
# Las cookies se guardan automáticamente
```

### Próximas ejecuciones (sin login)
```powershell
.\.venv\Scripts\python.exe scraper_vpn.py --linea belgrano_sur
# Entra automáticamente usando las cookies guardadas en cookies_vpn.json
```

### Todas las líneas
```powershell
.\.venv\Scripts\python.exe scraper_vpn.py --todas
```

### Con rango de fechas
```powershell
.\.venv\Scripts\python.exe scraper_vpn.py --inicio 01/02/2026 --linea roca
```

### En modo headless (sin ventana visible)
```powershell
.\.venv\Scripts\python.exe scraper_vpn.py --linea roca --headless
```

## Archivos generados

- `mensajes_sofse_YYYYMMDD_HHMMSS.json` - Mensajes extraídos
- `cookies_vpn.json` - Cookies VPN guardadas (para reutilizar)
- `debug_scraper/` - Screenshots y HTML de cada página (si usa `--debug`)

## Campos extraídos por mensaje

```json
{
  "id_mensaje": "656570",
  "numero_mensaje": "00656570",
  "fecha": "24/02/2026",
  "hora": "07:41:52",
  "fecha_hora": "24/02/2026 07:41:52",
  "linea": "Línea San Martín",
  "criticidad": "IMPORTANTE",
  "tipificacion": "DEMORAS",
  "estado": "Nuevo",
  "contenido": "17.1.A - EL TREN N @T3337 DE LAS 0727 HS...",
  "operador": "Carlos Mendoza",
  "grupos": ["ESTACIONES"],
  "estado_sms": "",
  "estado_email": "",
  "area_id": 555
}
```

## Próximas mejoras (si necesarias)

- [ ] Integrar output JSON con `gestor_tandas.py` para importar mensajes al sistema
- [ ] Agregar schedule automático (correr scraper cada X horas)
- [ ] Validar/deduplicar contra mensajes existentes
- [ ] Logging detallado a archivo

---

**Última actualización**: 24/02/2026
**Autor**: Claude
**Estado**: ✅ Funcionando correctamente con Chrome del sistema + cookies JSON
