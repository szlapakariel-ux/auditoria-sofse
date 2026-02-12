import { useState, useEffect, useRef } from 'react';
import { MessageSquare, Loader, Send, X, Settings } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

export default function AsistenteReglas({ mensaje, onCerrar, onReglaCreada }) {
    const [historial, setHistorial] = useState([]);
    const [inputUsuario, setInputUsuario] = useState('');
    const [cargando, setCargando] = useState(false);
    const [reglaLista, setReglaLista] = useState(null);
    const [mostrarConfirmarRegla, setMostrarConfirmarRegla] = useState(false);
    const chatEndRef = useRef(null);

    // Auto-scroll al último mensaje
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [historial, cargando]);

    // Análisis inicial automático
    useEffect(() => {
        iniciarAnalisis();
    }, []);

    const llamarIA = async (mensajeUsuario = null, historialActual = []) => {
        setCargando(true);

        try {
            const response = await fetch(`${API_URL}/api/analizar-regla-ia`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    historial: historialActual,
                    mensaje_actual: mensajeUsuario,
                    mensaje_ferroviario: {
                        id: mensaje.id,
                        contenido: mensaje.contenido,
                        operador: mensaje.operador,
                        linea: mensaje.linea,
                        derivado_por: mensaje.derivado_por || 'el validador',
                        comentario_validador: mensaje.comentario_validador || '',
                        clasificacion: mensaje.clasificacion || {},
                        componentes: mensaje.componentes || {},
                        scores: mensaje.scores || {}
                    }
                })
            });

            const data = await response.json();

            if (data.ok) {
                const nuevaRespuesta = {
                    rol: 'assistant',
                    contenido: data.respuesta
                };

                setHistorial(prev => [...prev, nuevaRespuesta]);

                if (data.regla_lista) {
                    setReglaLista(data.regla_lista);
                    setMostrarConfirmarRegla(true);
                }
            } else {
                setHistorial(prev => [...prev, {
                    rol: 'assistant',
                    contenido: '❌ Error al conectar con la IA. Por favor reintentá.'
                }]);
            }
        } catch (error) {
            console.error('Error:', error);
            setHistorial(prev => [...prev, {
                rol: 'assistant',
                contenido: '❌ Error de conexión. Verificá que el backend esté corriendo.'
            }]);
        } finally {
            setCargando(false);
        }
    };

    const iniciarAnalisis = async () => {
        await llamarIA(null, []);
    };

    const handleEnviarMensaje = async () => {
        if (!inputUsuario.trim() || cargando) return;

        const textoUsuario = inputUsuario.trim();
        setInputUsuario('');

        // Agregar mensaje del usuario al historial
        const nuevoMensajeUsuario = {
            rol: 'user',
            contenido: textoUsuario
        };

        const historialActualizado = [...historial, nuevoMensajeUsuario];
        setHistorial(historialActualizado);

        // Llamar al IA con el historial completo
        await llamarIA(textoUsuario, historialActualizado);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleEnviarMensaje();
        }
    };

    const handleConfirmarRegla = async () => {
        if (!reglaLista) return;
        setCargando(true);

        try {
            // Verificar conflictos
            const resConflictos = await fetch(`${API_URL}/api/reglas/verificar-conflictos`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    regla_nueva: {
                        ...reglaLista,
                        linea: reglaLista.ampliar_regla_id ? 'global' : (mensaje.linea || 'global')
                    }
                })
            });

            const dataConflictos = await resConflictos.json();
            const conflictos = dataConflictos.conflictos || [];

            if (conflictos.length > 0) {
                const textoConflictos = conflictos.map(c => `• ${c.tipo}: ${c.explicacion}`).join('\n');
                setHistorial(prev => [...prev, {
                    rol: 'assistant',
                    contenido: `⚠️ Detecté conflictos con reglas existentes:\n\n${textoConflictos}\n\n¿Querés crear la regla de todos modos?`
                }]);
                setMostrarConfirmarRegla(false);
                setCargando(false);
                return;
            }

            // Crear la regla
            const resCrear = await fetch(`${API_URL}/api/reglas/crear`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    regla: {
                        ...reglaLista,
                        linea: reglaLista.ampliar_regla_id ? 'global' : (mensaje.linea || 'global'),
                        mensaje_origen: mensaje.id,
                        creada_por: 'Ariel'
                    }
                })
            });

            const dataCrear = await resCrear.json();

            if (dataCrear.ok) {
                setHistorial(prev => [...prev, {
                    rol: 'assistant',
                    contenido: `✅ Regla creada exitosamente.\n\nMensajes afectados: ${dataCrear.mensajes_afectados}\n• ${dataCrear.mensajes_resueltos} sacados del panel de errores\n• ${dataCrear.mensajes_reclasificados} pendientes reclasificados`
                }]);
                setReglaLista(null);
                setMostrarConfirmarRegla(false);
                onReglaCreada(dataCrear);
            }
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setCargando(false);
        }
    };

    return (
        <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-2xl border-l-2 border-purple-200 flex flex-col z-40">

            {/* Header */}
            <div className="bg-purple-600 text-white p-4 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-2">
                    <Settings size={22} />
                    <div>
                        <h3 className="font-bold text-base">Asistente de Reglas</h3>
                        <p className="text-xs text-purple-200">Mensaje #{mensaje.id}</p>
                    </div>
                </div>
                <button onClick={onCerrar} className="hover:bg-purple-700 p-1 rounded transition-colors">
                    <X size={20} />
                </button>
            </div>

            {/* Contexto del mensaje */}
            <div className="bg-purple-50 border-b border-purple-200 p-3 flex-shrink-0">
                <p className="text-xs font-bold text-purple-700 mb-1">COMENTARIO DEL VALIDADOR:</p>
                <p className="text-xs text-purple-900 italic">
                    "{mensaje.comentario_validador || 'Sin comentario'}"
                </p>
            </div>

            {/* Chat */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">

                {historial.map((msg, i) => (
                    <div key={i} className={`flex ${msg.rol === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm ${msg.rol === 'user'
                            ? 'bg-blue-500 text-white rounded-br-sm'
                            : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                            }`}>
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.contenido}</p>
                        </div>
                    </div>
                ))}

                {/* Indicador de carga */}
                {cargando && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2">
                            <Loader className="animate-spin text-purple-600" size={16} />
                            <span className="text-sm text-gray-500">Analizando...</span>
                        </div>
                    </div>
                )}

                {/* Botón confirmar regla */}
                {mostrarConfirmarRegla && reglaLista && !cargando && (
                    <div className="bg-green-50 border-2 border-green-300 rounded-xl p-3">
                        <p className="text-xs font-bold text-green-700 mb-2">
                            ✅ REGLA LISTA PARA CREAR:
                        </p>
                        <p className="text-xs text-green-800 mb-1">
                            <strong>Patrón:</strong> {reglaLista.patron_detectado}
                        </p>
                        <p className="text-xs text-green-800 mb-1">
                            <strong>Tipo:</strong> {reglaLista.tipo}
                        </p>
                        <p className="text-xs text-green-800 mb-3">
                            <strong>Acción:</strong> {reglaLista.accion_sugerida}
                        </p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => {
                                    setMostrarConfirmarRegla(false);
                                    setReglaLista(null);
                                }}
                                className="flex-1 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg text-xs font-semibold"
                            >
                                Seguir charlando
                            </button>
                            <button
                                onClick={handleConfirmarRegla}
                                className="flex-1 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-semibold"
                            >
                                ✅ Crear regla
                            </button>
                        </div>
                    </div>
                )}

                <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 p-3 flex-shrink-0 bg-white">
                <div className="flex gap-2 items-end">
                    <textarea
                        value={inputUsuario}
                        onChange={(e) => setInputUsuario(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={cargando}
                        className="flex-1 p-3 border border-gray-300 rounded-xl text-sm resize-none focus:ring-2 focus:ring-purple-400 outline-none disabled:bg-gray-50"
                        placeholder="Escribí tu replanteo... (Enter para enviar)"
                        rows={2}
                    />
                    <button
                        onClick={handleEnviarMensaje}
                        disabled={!inputUsuario.trim() || cargando}
                        className="p-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                    >
                        <Send size={18} />
                    </button>
                </div>
                <p className="text-xs text-gray-400 mt-1 text-center">
                    Shift+Enter para nueva línea
                </p>
            </div>
        </div>
    );
}
