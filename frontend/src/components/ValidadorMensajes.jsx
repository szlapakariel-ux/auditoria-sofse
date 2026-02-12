import React, { useState } from 'react';
import MensajeCard from './MensajeCard';
import { validarMensaje } from '../services/api';
import { ArrowLeft, CheckCircle } from 'lucide-react';
import MensajesBloqueados from './MensajesBloqueados';

const ValidadorMensajes = ({ mensajesIniciales, usuario, onCambiarLinea: onVolverSelector }) => {
    const [mensajes, setMensajes] = useState(mensajesIniciales || []);
    const [loading, setLoading] = useState(false);
    const [completedCount, setCompletedCount] = useState(0);
    const [currentIndex, setCurrentIndex] = useState(0);

    // Estados para mensajes bloqueados
    const [mensajesBloqueados, setMensajesBloqueados] = useState([]);
    const [mostrarDetalleBloqueado, setMostrarDetalleBloqueado] = useState(false);
    const [mensajeBloqueadoDetalle, setMensajeBloqueadoDetalle] = useState(null);

    React.useEffect(() => {
        if (mensajesIniciales && mensajesIniciales.length > 0) {
            // Separar bloqueados de normales
            const bloqueados = mensajesIniciales.filter(m => m.bloqueado === true);
            const normales = mensajesIniciales.filter(m => !m.bloqueado);

            // DEDUPLICAR por ID
            const bloqueadosUnicos = bloqueados.filter(
                (msg, index, self) => index === self.findIndex(m => m.id === msg.id)
            );
            const normalesUnicos = normales.filter(
                (msg, index, self) => index === self.findIndex(m => m.id === msg.id)
            );

            setMensajesBloqueados(bloqueadosUnicos);
            setMensajes(normalesUnicos);
            setCurrentIndex(0);
        }
    }, [mensajesIniciales]);

    const handleVerDetalleBloqueado = (mensaje) => {
        setMensajeBloqueadoDetalle(mensaje);
        setMostrarDetalleBloqueado(true);
    };

    // If no initial messages or all done
    const mensajeActual = mensajes[currentIndex];

    const handleEnviar = async (mensajeId) => {
        setLoading(true);
        try {
            const data = await validarMensaje(mensajeId, 'ENVIAR', '');

            if (data.ok) {
                if (data.nueva_tanda && data.nueva_tanda.length > 0) {
                    setMensajes(data.nueva_tanda);
                    setCurrentIndex(0);
                } else if (data.restantes > 0) {
                    setCurrentIndex(prev => prev + 1);
                } else {
                    alert('¡Terminaste todos los mensajes! Seleccioná otra línea.');
                    onVolverSelector();
                }
            }
        } catch (error) {
            console.error('Error al validar:', error);
            alert('Error al procesar el mensaje');
        } finally {
            setLoading(false);
        }
    };

    const handleReportarError = async (id, comentario) => {
        setLoading(true);
        try {
            const response = await validarMensaje(id, 'REPORTAR', comentario);
            if (response.ok) {
                setCompletedCount(prev => prev + 1);
                if (response.nueva_tanda && response.nueva_tanda.length > 0) {
                    setMensajes(response.nueva_tanda);
                    setCurrentIndex(0);
                } else if (response.restantes > 0) {
                    setCurrentIndex(prev => prev + 1);
                } else {
                    alert('¡Terminaste todos los mensajes!');
                    onVolverSelector();
                }
            }
        } catch (error) {
            alert('Error al reportar');
        } finally {
            setLoading(false);
        }
    };

    // If queue is empty or index out of bounds
    if (!mensajeActual) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8 bg-white rounded-xl shadow-lg border border-gray-100 max-w-2xl mx-auto mt-12">
                <div className="bg-green-100 p-4 rounded-full mb-6">
                    <CheckCircle className="text-green-600" size={48} />
                </div>
                <h2 className="text-3xl font-bold text-gray-800 mb-4">¡Todo al día!</h2>
                <p className="text-gray-500 text-lg mb-8">
                    Has validado {completedCount} mensajes en esta sesión.
                    No hay más mensajes pendientes en esta línea por ahora.
                </p>
                <button
                    onClick={onVolverSelector}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition-all flex items-center gap-2"
                >
                    <ArrowLeft size={20} />
                    Volver al Selector
                </button>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <button
                    onClick={onVolverSelector}
                    className="flex items-center gap-2 text-gray-600 hover:text-gray-800"
                >
                    <ArrowLeft size={20} />
                    Cambiar de Línea
                </button>
                <div className="text-right">
                    <p className="text-sm text-gray-600">Validando como</p>
                    <p className="font-bold text-gray-800">{usuario}</p>
                </div>
            </div>

            {/* Acordeón de mensajes bloqueados */}
            <MensajesBloqueados
                mensajes={mensajesBloqueados}
                onVerDetalle={handleVerDetalleBloqueado}
            />

            {/* Validación normal */}
            {loading ? (
                <div className="text-center py-12">
                    <p className="text-gray-600">Cargando mensajes...</p>
                </div>
            ) : mensajes.length === 0 ? (
                <div className="text-center py-12">
                    <p className="text-gray-600">No hay más mensajes para validar</p>
                </div>
            ) : (
                <>
                    <div className="mb-4 flex justify-between items-center">
                        <p className="text-sm text-gray-600">
                            Pendiente #{currentIndex + 1} de {mensajes.length} (Tanda Actual)
                        </p>
                        <p className="text-sm text-gray-600">
                            Validados hoy: {completedCount}
                        </p>
                    </div>

                    {mensajeActual && (
                        <MensajeCard
                            mensaje={mensajeActual}
                            onEnviar={handleEnviar}
                            onReportarError={handleReportarError}
                        />
                    )}
                </>
            )}

            {/* Modal detalle mensaje bloqueado */}
            {mostrarDetalleBloqueado && mensajeBloqueadoDetalle && (
                <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <h2 className="text-xl font-bold text-gray-800">
                                    Mensaje Bloqueado - Solo Lectura
                                </h2>
                                <button
                                    onClick={() => setMostrarDetalleBloqueado(false)}
                                    className="text-gray-500 hover:text-gray-700"
                                >
                                    ✕
                                </button>
                            </div>

                            <div className="mb-4 p-4 bg-yellow-50 border border-yellow-300 rounded-lg">
                                <p className="font-bold text-yellow-800 mb-2">
                                    ⚠️ ESTE MENSAJE ESTÁ BLOQUEADO
                                </p>
                                <p className="text-sm text-yellow-700 mb-2">
                                    Requiere revisión conjunta con Ariel antes de validarlo.
                                </p>
                                <div className="p-3 bg-blue-50 rounded border border-blue-200">
                                    <p className="text-xs font-bold text-blue-700 mb-1">
                                        EXPLICACIÓN DE ARIEL:
                                    </p>
                                    <p className="text-sm text-blue-800">
                                        {mensajeBloqueadoDetalle.explicacion_ariel}
                                    </p>
                                </div>
                            </div>

                            <MensajeCard
                                mensaje={mensajeBloqueadoDetalle}
                                onEnviar={() => { }}
                                onReportarError={() => { }}
                                bloqueado={true}
                            />

                            <button
                                onClick={() => setMostrarDetalleBloqueado(false)}
                                className="mt-4 w-full bg-gray-600 hover:bg-gray-700 text-white py-3 rounded-lg font-semibold"
                            >
                                CERRAR
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ValidadorMensajes;
