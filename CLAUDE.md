# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a railway message validation system (Sistema de Validación SOFSE) with:
- **Backend**: Python Flask API for message validation and batch management
- **Frontend**: React + Vite web application for user interface
- **Data**: JSON-based message storage and historical tracking

The system validates railway messages for completeness and format compliance, assigns work to validators, and tracks message states.

## Project Structure

```
.
├── frontend/                      # React + Vite application
│   ├── src/
│   │   ├── components/           # React components (Login, ValidadorMensajes, etc.)
│   │   ├── services/api.js       # Axios API client for backend communication
│   │   └── App.jsx               # Main app component with routing logic
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
├── validador_mensajes.py         # Core message validation rules and logic
├── gestor_tandas.py              # Batch management and message state tracking
├── inicializar_sistema.py        # System initialization
├── scraper_mensajes.py           # Message data import utility
├── requirements.txt              # Python dependencies
├── app.py                        # Flask API server (likely in root)
└── .env                         # Environment variables
```

## Key Technologies

- **Backend**: Flask 3.1.0, Flask-CORS, Flask-Session, Pandas, OpenPyXL, Anthropic API
- **Frontend**: React 18.2, Axios, Tailwind CSS, Vite 5.1, Lucide React icons
- **Database**: JSON files for message storage
- **Deployment**: Render (see frontend/README.md)

## Development Commands

### Frontend Development
```bash
cd frontend
npm install              # Install dependencies
npm run dev             # Start dev server at http://localhost:5173
npm run build           # Build for production
npm run preview         # Preview production build
```

### Backend Development
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run the Flask server (typically on port 5000)
python app.py
```

## Architecture Notes

### Message Validation Pipeline
1. **`validador_mensajes.py`**: Contains validation logic that checks messages for:
   - Completeness (required fields)
   - Format compliance
   - State transitions (CANCELADO/SUSPENDIDO handling)
   - Error classification (COMPLETO, IMPORTANTE, OBSERVACIONES, SUGERENCIAS)

2. **`gestor_tandas.py`**: Manages message workflow:
   - Loads messages from `data/mensajes_estado.json`
   - Assigns 5 pending messages per user per line (tanda)
   - Tracks states: PENDIENTE → ASIGNADO_[USER] → COMPLETADO or DERIVADO_A_ARIEL
   - Separates blocked messages in accordion UI

### User Roles
- **General Users** (patricia, diego, ariel): Can validate assigned messages
- **Ariel** (admin): Has access to error panel and admin tools in navbar

### Frontend State Management
- **App.jsx**: Main routing between login, selector, validator, and error panel views
- **CurrentView states**: `login`, `selector`, `validator`, `errors`
- **Components communicate** via state props and callbacks; no Redux/Context needed for current scope

### API Structure
- Frontend proxies `/api` requests to `http://localhost:5000` (via vite.config.js)
- Backend endpoints likely handle: login, session, line selection, message assignment, validation updates

## Environment Setup

- `VITE_API_URL`: Backend URL (default: `http://localhost:5000`)
- Test users in `frontend/README.md`: patricia, diego, ariel
- JSON data files: `lote_revision_historico.json`, `lote_aprobados_historico.json`

## Common Development Tasks

### Adding a New Validation Rule
1. Edit `validador_mensajes.py` - add rule logic to classification functions
2. Rules are categorized: IMPORTANTE, OBSERVACIONES, SUGERENCIAS
3. Test with existing message samples in JSON files

### Running Batch Operations
1. `python inicializar_sistema.py` - loads and displays message statistics
2. `python scraper_mensajes.py` - imports messages (likely from external source)

### Debugging Frontend Issues
- Check Network tab for API calls (`/api/...`)
- Console shows session/auth errors
- ValidadorMensajes component handles message display and user submissions

## Rule Management via Antigravity

Instead of built-in IA chat, Ariel now uses **Antigravity** (Google's AI IDE) to:
1. Define validation rules manually
2. Modify existing rules
3. Apply rules to pending messages

**Endpoints for Antigravity:**
- `GET /api/reglas/todas` - List all active rules
- `POST /api/reglas/crear` - Create new rule
- `POST /api/reglas/modificar/{id}` - Update existing rule
- `POST /api/reglas/aplicar-todas` - Re-validate all messages

See `ANTIGRAVITY_SETUP.md` for integration guide.

## Notes

- Messages stored as JSON: `id`, `estado`, `linea`, `contenido`, `asignado_a`, etc.
- States: PENDIENTE, ASIGNADO_[USER], COMPLETADO, DERIVADO_A_ARIEL, BLOQUEADO
- Rules stored in `configs/reglas/[linea]/personalizadas.json`
- **IA tokens removed** - backend no longer uses Claude, Gemini, or OpenAI
- Frontend uses Tailwind for styling; Lucide React for icons
- Session management via Flask-Session (cookies)
