import React, { useState } from 'react';
import { Send, AlertTriangle, User, Clock, CheckCircle2, XCircle, AlertOctagon, Info } from 'lucide-react';

const MensajeCard = ({ mensaje, onEnviar, onReportarError, bloqueado = false }) => {
    const [showReport, setShowReport] = useState(false);
    const [reportComment, setReportComment] = useState('');

    const getStatusConfig = (nivel) => {
        switch (nivel) {
            case 'COMPLETO': return { bg: 'bg-emerald-50', border: 'border-emerald-500', icon: '✅', label: 'MENSAJE COMPLETO', labelColor: 'text-emerald-700' };
            case 'SUGERENCIAS': return { bg: 'bg-blue-50', border: 'border-blue-500', icon: '💡', label: 'CON SUGERENCIAS', labelColor: 'text-blue-700' };
            case 'OBSERVACIONES': return { bg: 'bg-amber-50', border: 'border-amber-500', icon: '⚠️', label: 'PARA AJUSTES', labelColor: 'text-amber-700' };
            case 'IMPORTANTE': return { bg: 'bg-red-50', border: 'border-red-500', icon: '🚨', label: 'PARA REVISIÓN', labelColor: 'text-red-700' };
            default: return { bg: 'bg-gray-50', border: 'border-gray-300', icon: '📋', label: 'SIN CLASIFICAR', labelColor: 'text-gray-700' };
        }
    };

    const getScoreEmoji = (score) => {
        switch (score) {
            case 'COMPLETO': case 'IMPECABLE': return '🟢';
            case 'BUENO': case 'ACEPTABLE': return '🟡';
            case 'REGULAR': case 'INCOMPLETO': return '🟠';
            case 'INSUFICIENTE': return '🔴';
            case 'N/A': return '⚪';
            default: return '⚪';
        }
    };

    const getScoreBackgroundColor = (score) => {
        switch (score) {
            case 'COMPLETO': case 'IMPECABLE': return 'bg-emerald-50 border-emerald-200';
            case 'BUENO': case 'ACEPTABLE': return 'bg-yellow-50 border-yellow-200';
            case 'REGULAR': case 'INCOMPLETO': return 'bg-orange-50 border-orange-200';
            case 'INSUFICIENTE': return 'bg-red-50 border-red-200';
            default: return 'bg-gray-50 border-gray-200';
        }
    };

    const handleReportSubmit = () => {
        if (reportComment.trim()) {
            onReportarError(mensaje.id, reportComment);
            setShowReport(false);
            setReportComment('');
        }
    };

    const status = getStatusConfig(mensaje.nivel_general);

    return (
        <div className={`relative w-full rounded-2xl border-l-[5px] shadow-sm ${status.bg} ${status.border} overflow-hidden animate-slide-up`}>
            {/* Card Content */}
            <div className="bg-white/90 backdrop-blur-sm p-5 sm:p-6">
                {/* Status Header */}
                <div className="mb-4 pb-4 border-b border-gray-100">
                    <div className="flex items-center gap-2.5 mb-3">
                        <span className="text-xl">{status.icon}</span>
                        <h2 className={`text-base sm:text-lg font-bold ${status.labelColor}`}>
                            {status.label}
                        </h2>
                    </div>

                    {/* Metadata Grid */}
                    <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="bg-gray-50 rounded-lg p-2.5">
                            <p className="text-gray-400 text-xs font-semibold mb-0.5">Número</p>
                            <p className="font-bold text-gray-900 text-sm">#{mensaje.id}</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-2.5">
                            <p className="text-gray-400 text-xs font-semibold mb-0.5">Operador</p>
                            <p className="font-bold text-gray-900 text-sm truncate">{mensaje.operador}</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-2.5">
                            <p className="text-gray-400 text-xs font-semibold mb-0.5">Fecha/Hora</p>
                            <p className="font-bold text-gray-900 text-sm">{mensaje.fecha_hora}</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-2.5">
                            <p className="text-gray-400 text-xs font-semibold mb-0.5">Línea</p>
                            <p className="font-bold text-gray-900 text-sm truncate">{mensaje.linea}</p>
                        </div>
                    </div>

                    {mensaje.tipo_mensaje && (
                        <div className="mt-2.5 bg-gray-50 rounded-lg p-2.5">
                            <p className="text-gray-400 text-xs font-semibold mb-0.5">Tipo</p>
                            <p className="font-bold text-gray-900 text-sm uppercase tracking-wide">
                                {mensaje.tipo_mensaje.replace('_', ' ')}
                            </p>
                        </div>
                    )}
                </div>

                {/* Contenido del mensaje */}
                <div className="mb-5">
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                        Contenido del mensaje
                    </h3>
                    <div className="bg-gray-50 p-4 rounded-xl font-mono text-sm leading-relaxed text-gray-700 border border-gray-200">
                        {mensaje.contenido}
                    </div>
                </div>

                {/* Scores */}
                {mensaje.scores && Object.keys(mensaje.scores).length > 0 && (
                    <div className="mb-5">
                        <div className="grid grid-cols-3 gap-2 sm:gap-3">
                            {Object.entries(mensaje.scores).map(([key, data]) => (
                                <div key={key} className="bg-white p-3 sm:p-4 rounded-xl border border-gray-200 text-center shadow-sm">
                                    <div className="text-2xl sm:text-3xl mb-1.5">{getScoreEmoji(data.clasificacion)}</div>
                                    <p className="text-[10px] sm:text-xs font-bold text-gray-400 uppercase mb-0.5">
                                        {key === 'componentes' ? 'Componentes' :
                                            key === 'timing' ? 'Timing' :
                                                'Estructura'}
                                    </p>
                                    <p className="text-xs sm:text-sm font-bold text-gray-800">{data.clasificacion}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Timing */}
                {mensaje.timing && mensaje.scores?.timing && (
                    <div className="mb-5">
                        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            {getScoreEmoji(mensaje.scores.timing.clasificacion)} Timing
                        </h3>
                        <div className={`p-4 rounded-xl border ${getScoreBackgroundColor(mensaje.scores.timing.clasificacion)}`}>
                            <div className="grid grid-cols-2 gap-2 text-sm text-gray-800 mb-2">
                                {mensaje.timing.hora_programada && (
                                    <p>Hora programada: <strong>{mensaje.timing.hora_programada}</strong></p>
                                )}
                                {mensaje.timing.hora_envio && (
                                    <p>Hora de envío: <strong>{mensaje.timing.hora_envio}</strong></p>
                                )}
                                {mensaje.timing.tardanza_minutos !== undefined && (
                                    <p>Diferencia: <strong>{mensaje.timing.tardanza_minutos} min</strong></p>
                                )}
                                {mensaje.timing.minutos_demora && (
                                    <p>Demora reportada: <strong>{mensaje.timing.minutos_demora} min</strong></p>
                                )}
                            </div>
                            {mensaje.scores.timing.detalles && mensaje.scores.timing.detalles.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-gray-200/50">
                                    <p className="text-xs font-bold text-gray-500 mb-1.5">Evaluación:</p>
                                    {mensaje.scores.timing.detalles.map((detalle, i) => (
                                        <p key={i} className="text-xs text-gray-600 ml-2">• {detalle}</p>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Componentes incluidos */}
                {mensaje.componentes && Object.keys(mensaje.componentes).length > 0 && (
                    <div className="mb-5 bg-emerald-50 p-4 rounded-xl border border-emerald-200">
                        <h3 className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-2.5">
                            ✅ Componentes incluidos
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-sm text-emerald-900">
                            {mensaje.componentes.A && <p>• <strong>Tren:</strong> {mensaje.componentes.A}</p>}
                            {mensaje.componentes.B && <p>• <strong>Estado:</strong> {typeof mensaje.componentes.B === 'object' ? mensaje.componentes.B.estado : mensaje.componentes.B}</p>}
                            {mensaje.componentes.C && <p>• <strong>Contingencia:</strong> {typeof mensaje.componentes.C === 'object' ? mensaje.componentes.C.forma_comunicacion : mensaje.componentes.C}</p>}
                            {mensaje.componentes.D && <p>• <strong>Hora:</strong> {mensaje.componentes.D}</p>}
                            {mensaje.componentes.F && <p>• <strong>Código:</strong> {mensaje.componentes.F}</p>}
                        </div>
                    </div>
                )}

                {/* Observaciones IMPORTANTES */}
                {mensaje.clasificacion?.IMPORTANTE?.length > 0 && (
                    <div className="mb-4">
                        <h3 className="text-xs font-bold text-red-600 uppercase tracking-wider mb-2">
                            Errores importantes
                        </h3>
                        {mensaje.clasificacion.IMPORTANTE.map((item, i) => (
                            <div key={`imp-${i}`} className="flex items-start gap-2.5 text-red-700 bg-red-50 p-3 rounded-xl text-sm border border-red-200 mb-2">
                                <AlertOctagon size={16} className="mt-0.5 shrink-0" />
                                <span>{item}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Observaciones MEDIAS */}
                {mensaje.clasificacion?.OBSERVACIONES?.length > 0 && (
                    <div className="mb-4">
                        <h3 className="text-xs font-bold text-amber-600 uppercase tracking-wider mb-2">
                            Observaciones
                        </h3>
                        {mensaje.clasificacion.OBSERVACIONES.map((item, i) => (
                            <div key={`obs-${i}`} className="flex items-start gap-2.5 text-amber-700 bg-amber-50 p-3 rounded-xl text-sm border border-amber-200 mb-2">
                                <Info size={16} className="mt-0.5 shrink-0" />
                                <span>{item}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Sugerencias */}
                {mensaje.clasificacion?.SUGERENCIAS?.length > 0 && (
                    <div className="mb-5">
                        <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-2">
                            Sugerencias
                        </h3>
                        {mensaje.clasificacion.SUGERENCIAS.map((item, i) => (
                            <div key={`sug-${i}`} className="flex items-start gap-2.5 text-blue-700 bg-blue-50 p-3 rounded-xl text-sm border border-blue-200 mb-2">
                                <Info size={16} className="mt-0.5 shrink-0" />
                                <span>{item}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Botones de acción */}
                <div className="flex gap-3 pt-4 border-t border-gray-100">
                    <button
                        onClick={() => onEnviar(mensaje.id)}
                        disabled={bloqueado}
                        className={`flex-1 py-3 sm:py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2
                            ${bloqueado
                                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md hover:shadow-lg active:scale-[0.98]'
                            }`}
                    >
                        <CheckCircle2 size={18} />
                        ENVIAR
                    </button>

                    <button
                        onClick={() => setShowReport(true)}
                        disabled={bloqueado}
                        className={`flex-1 py-3 sm:py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2
                            ${bloqueado
                                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                : 'bg-red-600 hover:bg-red-700 text-white shadow-md hover:shadow-lg active:scale-[0.98]'
                            }`}
                    >
                        <AlertTriangle size={18} />
                        REPORTAR
                    </button>
                </div>
            </div>

            {/* Modal de reporte */}
            {showReport && (
                <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-scale-in">
                        <div className="p-5 sm:p-6">
                            <h2 className="text-lg sm:text-xl font-bold text-red-700 mb-4 flex items-center gap-2">
                                <AlertTriangle size={22} />
                                Reportar error del sistema
                            </h2>

                            {/* Info del mensaje */}
                            <div className="mb-4 p-3 bg-gray-50 rounded-xl text-sm border border-gray-200">
                                <p><strong>Mensaje:</strong> #{mensaje.id} - {mensaje.linea}</p>
                                <p><strong>Operador:</strong> {mensaje.operador}</p>
                                <p><strong>Fecha derivación:</strong> {new Date().toLocaleString('es-AR')}</p>
                            </div>

                            {/* Texto del mensaje */}
                            <div className="mb-4">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                                    Texto del mensaje
                                </h3>
                                <div className="bg-gray-50 p-3 rounded-xl font-mono text-sm border border-gray-200">
                                    {mensaje.contenido}
                                </div>
                            </div>

                            {/* Observación del sistema */}
                            <div className="mb-4">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                                    Observación del sistema
                                </h3>
                                <div className="bg-amber-50 p-3 rounded-xl border border-amber-200 space-y-1.5 text-sm">
                                    {mensaje.clasificacion?.IMPORTANTE?.map((item, i) => (
                                        <div key={i} className="flex items-start gap-2 text-red-700">
                                            <span className="shrink-0">🔴</span>
                                            <span>{item}</span>
                                        </div>
                                    ))}
                                    {mensaje.clasificacion?.OBSERVACIONES?.map((item, i) => (
                                        <div key={i} className="flex items-start gap-2 text-amber-700">
                                            <span className="shrink-0">🟡</span>
                                            <span>{item}</span>
                                        </div>
                                    ))}
                                    {mensaje.clasificacion?.SUGERENCIAS?.map((item, i) => (
                                        <div key={i} className="flex items-start gap-2 text-blue-700">
                                            <span className="shrink-0">💡</span>
                                            <span>{item}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Comentario del validador */}
                            <div className="mb-6">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                                    Tu comentario
                                </h3>
                                <textarea
                                    value={reportComment}
                                    onChange={(e) => setReportComment(e.target.value)}
                                    className="w-full h-28 p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-400 focus:border-red-400
                                               outline-none resize-none text-sm bg-gray-50 focus:bg-white placeholder:text-gray-400"
                                    placeholder="Explicá por qué el sistema se equivocó..."
                                    autoFocus
                                />
                            </div>

                            {/* Botones */}
                            <div className="flex gap-3">
                                <button
                                    onClick={() => {
                                        setShowReport(false);
                                        setReportComment('');
                                    }}
                                    className="flex-1 py-3 px-4 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl font-semibold text-sm border border-gray-200"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleReportSubmit}
                                    disabled={!reportComment.trim()}
                                    className="flex-1 py-3 px-4 bg-red-600 hover:bg-red-700 text-white rounded-xl font-semibold text-sm
                                               disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
                                >
                                    Derivar a Ariel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MensajeCard;
