import React, { useState } from 'react';
import MensajeCard from './MensajeCard';
import { validarMensaje } from '../services/api';
import { ArrowLeft, CheckCircle, Sparkles } from 'lucide-react';
import MensajesBloqueados from './MensajesBloqueados';
import PanelScraping from './PanelScraping';

const ValidadorMensajes = ({ mensajesIniciales, usuario, lineaActual = '', onCambiarLinea: onVolverSelector }) => {
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
                setCompletedCount(prev => prev + 1);
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
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8 animate-fade-in">
                <div className="bg-white rounded-2xl shadow-lg border border-gray-100 max-w-md mx-auto p-10">
                    <div className="bg-emerald-100 p-4 rounded-2xl mb-6 inline-flex">
                        <Sparkles className="text-emerald-600" size={40} />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-3">¡Todo al día!</h2>
                    <p className="text-gray-500 text-sm mb-8 leading-relaxed">
                        Validaste <strong>{completedCount}</strong> mensaje{completedCount !== 1 ? 's' : ''} en esta sesión.
                        No hay más pendientes en esta línea.
                    </p>
                    <button
                        onClick={onVolverSelector}
                        className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700
                                   text-white font-semibold py-3 px-8 rounded-xl shadow-md hover:shadow-lg
                                   transition-all flex items-center gap-2 mx-auto active:scale-[0.98]"
                    >
                        <ArrowLeft size={18} />
                        Volver al selector
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto animate-fade-in">
            {/* Header */}
            <div className="mb-5 flex items-center justify-between">
                <button
                    onClick={onVolverSelector}
                    className="flex items-center gap-2 text-gray-500 hover:text-gray-800 font-medium text-sm
                               px-3 py-2 rounded-lg hover:bg-white transition-all"
                >
                    <ArrowLeft size={18} />
                    <span className="hidden sm:inline">Cambiar línea</span>
                </button>
                <div className="text-right">
                    <p className="text-xs text-gray-400 font-medium">Validando como</p>
                    <p className="font-bold text-gray-900 text-sm">{usuario}</p>
                </div>
            </div>

            {/* Panel de Scraping VPN (solo San Martín) */}
            <PanelScraping
                usuario={usuario}
                lineaActual={lineaActual}
            />

            {/* Acordeón de mensajes bloqueados */}
            <MensajesBloqueados
                mensajes={mensajesBloqueados}
                onVerDetalle={handleVerDetalleBloqueado}
            />

            {/* Validación normal */}
            {loading ? (
                <div className="text-center py-16">
                    <div className="h-10 w-10 mx-auto animate-spin rounded-full border-4 border-blue-200 border-t-blue-600 mb-4"></div>
                    <p className="text-gray-500 text-sm font-medium">Procesando...</p>
                </div>
            ) : mensajes.length === 0 ? (
                <div className="text-center py-16">
                    <p className="text-gray-500">No hay más mensajes para validar</p>
                </div>
            ) : (
                <>
                    {/* Progress Bar */}
                    <div className="mb-4 bg-white rounded-xl border border-gray-200 p-3 sm:p-4 flex justify-between items-center shadow-sm">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center gap-1.5">
                                <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse-soft"></div>
                                <span className="text-sm font-semibold text-gray-700">
                                    #{currentIndex + 1} de {mensajes.length}
                                </span>
                            </div>
                            {/* Mini progress bar */}
                            <div className="hidden sm:flex w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className="bg-blue-500 rounded-full transition-all duration-500"
                                    style={{ width: `${((currentIndex + 1) / mensajes.length) * 100}%` }}
                                />
                            </div>
                        </div>
                        <div className="flex items-center gap-1.5 text-sm text-gray-500">
                            <CheckCircle size={14} className="text-emerald-500" />
                            <span className="font-medium">{completedCount} validados</span>
                        </div>
                    </div>

                    {mensajeActual && (
                        <MensajeCard
                            key={mensajeActual.id}
                            mensaje={mensajeActual}
                            onEnviar={handleEnviar}
                            onReportarError={handleReportarError}
                        />
                    )}
                </>
            )}

            {/* Modal detalle mensaje bloqueado */}
            {mostrarDetalleBloqueado && mensajeBloqueadoDetalle && (
                <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-scale-in">
                        <div className="p-5 sm:p-6">
                            <div className="flex justify-between items-start mb-4">
                                <h2 className="text-lg font-bold text-gray-900">
                                    Mensaje bloqueado
                                </h2>
                                <button
                                    onClick={() => setMostrarDetalleBloqueado(false)}
                                    className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-all"
                                >
                                    ✕
                                </button>
                            </div>

                            <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                                <p className="font-bold text-amber-800 mb-2 text-sm">
                                    ⚠️ Este mensaje requiere revisión con Ariel
                                </p>
                                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                                    <p className="text-xs font-bold text-blue-600 mb-1">
                                        Explicación de Ariel:
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
                                className="mt-4 w-full bg-gray-800 hover:bg-gray-900 text-white py-3 rounded-xl font-semibold text-sm transition-all"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ValidadorMensajes;
