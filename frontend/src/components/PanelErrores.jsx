import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, ArrowLeft, Send } from 'lucide-react';
import { getErrores, desbloquearMensaje } from '../services/api';

export default function PanelErrores() {
    const [errores, setErrores] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        cargarErrores();
    }, []);

    const cargarErrores = async () => {
        setLoading(true);
        try {
            const data = await getErrores();
            if (data.ok) {
                setErrores(data.errores);
            }
        } catch (error) {
            console.error('Error al cargar errores:', error);
        } finally {
            setLoading(false);
        }
    };




    const [showDevolver, setShowDevolver] = useState(false);
    const [mensajeDevolver, setMensajeDevolver] = useState(null);
    const [explicacion, setExplicacion] = useState('');

    const handleDevolver = (mensaje) => {
        setMensajeDevolver(mensaje);
        setShowDevolver(true);
    };

    const confirmarDevolver = async () => {
        if (!explicacion.trim()) {
            alert('Debes escribir una explicación');
            return;
        }

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/errores/devolver`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mensaje_id: mensajeDevolver.id,
                    explicacion: explicacion
                })
            });

            const data = await response.json();

            if (data.ok) {
                alert('Mensaje devuelto y bloqueado para el validador');
                setShowDevolver(false);
                setExplicacion('');
                setMensajeDevolver(null);
                cargarErrores();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al devolver mensaje');
        }
    };

    if (loading) {
        return <div className="p-8 text-center">Cargando errores...</div>;
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <AlertTriangle className="text-red-600" size={28} />
                Panel de Errores - Mensajes Derivados ({errores.length})
            </h1>

            {errores.length === 0 ? (
                <div className="bg-green-50 border border-green-300 rounded-lg p-8 text-center">
                    <CheckCircle className="mx-auto text-green-600 mb-3" size={48} />
                    <p className="text-lg font-semibold text-green-800">
                        ¡No hay errores pendientes!
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {errores.map((mensaje) => (
                        <div key={mensaje.id} className="bg-white border-l-4 border-red-500 rounded-lg shadow-md p-6">
                            {/* Header */}
                            <div className="mb-4 pb-4 border-b">
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="text-lg font-bold text-red-700">
                                        🔴 Mensaje #{mensaje.id} - {mensaje.linea}
                                    </h3>
                                    <span className="text-sm text-gray-500">
                                        Derivado por: {mensaje.derivado_por}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600">
                                    Operador: {mensaje.operador} | {mensaje.fecha_hora}
                                </p>
                            </div>

                            {/* Contenido */}
                            <div className="mb-4 bg-gray-50 p-3 rounded font-mono text-sm">
                                {mensaje.contenido}
                            </div>

                            {/* Observación del sistema */}
                            <div className="mb-4 bg-yellow-50 p-3 rounded border border-yellow-300">
                                <p className="font-bold text-sm mb-2">OBSERVACIÓN DEL SISTEMA:</p>
                                {mensaje.clasificacion?.IMPORTANTE?.map((item, i) => (
                                    <p key={i} className="text-sm text-red-700">🔴 {item}</p>
                                ))}
                                {mensaje.clasificacion?.OBSERVACIONES?.map((item, i) => (
                                    <p key={i} className="text-sm text-yellow-700">🟡 {item}</p>
                                ))}
                            </div>

                            {/* Comentario del validador */}
                            <div className="mb-4 bg-blue-50 p-3 rounded border border-blue-300">
                                <p className="font-bold text-sm mb-1">COMENTARIO DEL VALIDADOR:</p>
                                <p className="text-sm text-gray-700">{mensaje.comentario_validador}</p>
                            </div>

                            {/* Botones */}
                            <div className="flex gap-3">
                                <a
                                    href={`antigravity://error/${mensaje.id}?contenido=${encodeURIComponent(mensaje.contenido)}&comentario=${encodeURIComponent(mensaje.comentario_validador)}`}
                                    className="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
                                    title="Abrir en Antigravity para crear/modificar regla"
                                >
                                    <Send size={20} />
                                    ABRIR EN ANTIGRAVITY
                                </a>
                                <button
                                    onClick={() => handleDevolver(mensaje)}
                                    className="flex-1 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
                                >
                                    <ArrowLeft size={20} />
                                    DEVOLVER
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}


            {/* Popup devolver a validadores */}
            {showDevolver && mensajeDevolver && (
                <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full">
                        <div className="p-6">
                            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <ArrowLeft size={24} />
                                DEVOLVER A VALIDADORES
                            </h2>

                            <div className="mb-4 p-3 bg-gray-50 rounded-lg text-sm">
                                <p><strong>Mensaje:</strong> #{mensajeDevolver.id}</p>
                                <p><strong>Derivado por:</strong> {mensajeDevolver.derivado_por}</p>
                            </div>

                            <div className="mb-6">
                                <h3 className="text-sm font-bold text-gray-700 mb-2">
                                    EXPLICACIÓN PARA REVISAR JUNTOS:
                                </h3>
                                <textarea
                                    value={explicacion}
                                    onChange={(e) => setExplicacion(e.target.value)}
                                    className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none text-sm"
                                    placeholder="Ej: Hablemos mañana sobre esto. El formato 10_44 no está en la normativa oficial..."
                                    autoFocus
                                />
                            </div>

                            <div className="flex gap-3">
                                <button
                                    onClick={() => {
                                        setShowDevolver(false);
                                        setExplicacion('');
                                        setMensajeDevolver(null);
                                    }}
                                    className="flex-1 py-3 px-4 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-semibold border border-gray-300"
                                >
                                    CANCELAR
                                </button>
                                <button
                                    onClick={confirmarDevolver}
                                    disabled={!explicacion.trim()}
                                    className="flex-1 py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    DEVOLVER Y BLOQUEAR
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
