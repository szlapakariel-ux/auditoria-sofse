import React, { useState } from 'react';
import { Send, AlertTriangle, User, Clock, CheckCircle2, XCircle, AlertOctagon, Info } from 'lucide-react';

const MensajeCard = ({ mensaje, onEnviar, onReportarError, bloqueado = false }) => {
    const [showReport, setShowReport] = useState(false);
    const [reportComment, setReportComment] = useState('');

    const getStatusStyle = (nivel) => {
        switch (nivel) {
            case 'COMPLETO': return 'bg-green-50 border-green-500';
            case 'SUGERENCIAS': return 'bg-blue-50 border-blue-500';
            case 'OBSERVACIONES': return 'bg-yellow-50 border-yellow-500';
            case 'IMPORTANTE': return 'bg-red-50 border-red-500';
            default: return 'bg-gray-50 border-gray-300';
        }
    };

    const getStatusIcon = (nivel) => {
        switch (nivel) {
            case 'COMPLETO': return '🟢';
            case 'SUGERENCIAS': return '🔵';
            case 'OBSERVACIONES': return '🟡';
            case 'IMPORTANTE': return '🔴';
            default: return '⚪';
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
            case 'COMPLETO': case 'IMPECABLE': return 'bg-green-50 border-green-200';
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

    const containerClass = `relative w-full rounded-xl border-l-[6px] shadow-sm p-6 mb-6 bg-white ${getStatusStyle(mensaje.nivel_general)}`;

    return (
        <div className={containerClass}>
            {/* Header con estado visual */}
            <div className="mb-4 pb-4 border-b border-gray-200">
                <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">{getStatusIcon(mensaje.nivel_general)}</span>
                    <h2 className="text-lg font-bold text-gray-800">
                        {mensaje.nivel_general === 'IMPORTANTE' ? 'MENSAJE PARA REVISIÓN' :
                            mensaje.nivel_general === 'OBSERVACIONES' ? 'MENSAJE PARA AJUSTES' :
                                mensaje.nivel_general === 'SUGERENCIAS' ? 'MENSAJE CON SUGERENCIAS' :
                                    'MENSAJE COMPLETO'}
                    </h2>
                </div>

                {/* Info del mensaje */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p className="text-gray-500 font-medium">📋 Número</p>
                        <p className="font-bold text-gray-800">#{mensaje.id}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 font-medium">👤 Operador</p>
                        <p className="font-bold text-gray-800">{mensaje.operador}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 font-medium">🕐 Fecha/Hora</p>
                        <p className="font-bold text-gray-800">{mensaje.fecha_hora}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 font-medium">📍 Línea</p>
                        <p className="font-bold text-gray-800">{mensaje.linea}</p>
                    </div>
                </div>

                {mensaje.tipo_mensaje && (
                    <div className="mt-2 text-sm">
                        <p className="text-gray-500 font-medium">📄 Tipo</p>
                        <p className="font-bold text-gray-800 uppercase tracking-wide">{mensaje.tipo_mensaje.replace('_', ' ')}</p>
                    </div>
                )}
            </div>

            {/* Contenido del mensaje */}
            <div className="mb-6">
                <h3 className="text-sm font-bold text-gray-600 mb-2">📄 CONTENIDO DEL MENSAJE</h3>
                <div className="bg-gray-50 p-4 rounded-lg font-mono text-sm leading-relaxed text-gray-700 border border-gray-200">
                    {mensaje.contenido}
                </div>
            </div>

            {/* Scores */}
            <div className="mb-6">
                <div className="grid grid-cols-3 gap-4">
                    {mensaje.scores && Object.entries(mensaje.scores).map(([key, data]) => (
                        <div key={key} className="bg-white p-4 rounded-lg border border-gray-200 text-center">
                            <div className="text-3xl mb-2">{getScoreEmoji(data.clasificacion)}</div>
                            <p className="text-xs font-bold text-gray-500 uppercase mb-1">
                                {key === 'componentes' ? '📦 COMPONENTES' :
                                    key === 'timing' ? '⏱️ TIMING' :
                                        '✍️ ESTRUCTURA'}
                            </p>
                            <p className="text-sm font-bold text-gray-800">{data.clasificacion}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Timing */}
            {mensaje.timing && mensaje.scores?.timing && (
                <div className="mb-6">
                    <h3 className="text-sm font-bold text-gray-700 mb-2">
                        {getScoreEmoji(mensaje.scores.timing.clasificacion)} TIMING
                    </h3>
                    <div className={`p-4 rounded-lg border ${getScoreBackgroundColor(mensaje.scores.timing.clasificacion)}`}>
                        <div className="grid grid-cols-2 gap-2 text-sm text-gray-800 mb-2">
                            {mensaje.timing.hora_programada && (
                                <p>• <strong>Hora programada:</strong> {mensaje.timing.hora_programada}</p>
                            )}
                            {mensaje.timing.hora_envio && (
                                <p>• <strong>Hora de envío:</strong> {mensaje.timing.hora_envio}</p>
                            )}
                            {mensaje.timing.tardanza_minutos !== undefined && (
                                <p>• <strong>Diferencia:</strong> {mensaje.timing.tardanza_minutos} min después</p>
                            )}
                            {mensaje.timing.minutos_demora && (
                                <p>• <strong>Demora reportada:</strong> {mensaje.timing.minutos_demora} min</p>
                            )}
                        </div>
                        {mensaje.scores.timing.detalles && mensaje.scores.timing.detalles.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-300">
                                <p className="text-xs font-bold text-gray-600 mb-1">EVALUACIÓN:</p>
                                {mensaje.scores.timing.detalles.map((detalle, i) => (
                                    <p key={i} className="text-xs text-gray-700">• {detalle}</p>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Componentes incluidos */}
            {mensaje.componentes && Object.keys(mensaje.componentes).length > 0 && (
                <div className="mb-6 bg-green-50 p-4 rounded-lg border border-green-200">
                    <h3 className="text-sm font-bold text-green-800 mb-3">✅ COMPONENTES INCLUIDOS</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm text-green-900">
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
                    <h3 className="text-sm font-bold text-red-700 mb-2">🔴 ERRORES IMPORTANTES</h3>
                    {mensaje.clasificacion.IMPORTANTE.map((item, i) => (
                        <div key={`imp-${i}`} className="flex items-start gap-2 text-red-700 bg-red-50 p-3 rounded-md text-sm border border-red-200 mb-2">
                            <AlertOctagon size={18} className="mt-0.5 shrink-0" />
                            <span>{item}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Observaciones MEDIAS */}
            {mensaje.clasificacion?.OBSERVACIONES?.length > 0 && (
                <div className="mb-4">
                    <h3 className="text-sm font-bold text-yellow-700 mb-2">🟡 OBSERVACIONES</h3>
                    {mensaje.clasificacion.OBSERVACIONES.map((item, i) => (
                        <div key={`obs-${i}`} className="flex items-start gap-2 text-yellow-700 bg-yellow-50 p-3 rounded-md text-sm border border-yellow-200 mb-2">
                            <Info size={18} className="mt-0.5 shrink-0" />
                            <span>{item}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Sugerencias */}
            {mensaje.clasificacion?.SUGERENCIAS?.length > 0 && (
                <div className="mb-6">
                    <h3 className="text-sm font-bold text-blue-700 mb-2">💡 SUGERENCIAS</h3>
                    {mensaje.clasificacion.SUGERENCIAS.map((item, i) => (
                        <div key={`sug-${i}`} className="flex items-start gap-2 text-blue-700 bg-blue-50 p-3 rounded-md text-sm border border-blue-200 mb-2">
                            <Info size={18} className="mt-0.5 shrink-0" />
                            <span>{item}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Botones de acción */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
                <button
                    onClick={() => onEnviar(mensaje.id)}
                    disabled={bloqueado}
                    className={`flex-1 py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 ${bloqueado
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'
                        }`}
                >
                    <CheckCircle2 size={20} />
                    ENVIAR
                </button>

                <button
                    onClick={() => setShowReport(true)}
                    disabled={bloqueado}
                    className={`flex-1 py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 ${bloqueado
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-red-600 hover:bg-red-700 text-white'
                        }`}
                >
                    <AlertTriangle size={20} />
                    REPORTAR ERROR
                </button>
            </div>

            {/* Modal de reporte */}
            {showReport && (
                <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <h2 className="text-xl font-bold text-red-700 mb-4 flex items-center gap-2">
                                <AlertTriangle size={24} />
                                REPORTAR ERROR DEL SISTEMA
                            </h2>

                            {/* Info del mensaje */}
                            <div className="mb-4 p-3 bg-gray-50 rounded-lg text-sm">
                                <p><strong>Mensaje:</strong> #{mensaje.id} - {mensaje.linea}</p>
                                <p><strong>Operador:</strong> {mensaje.operador}</p>
                                <p><strong>Fecha derivación:</strong> {new Date().toLocaleString('es-AR')}</p>
                            </div>

                            {/* Texto del mensaje */}
                            <div className="mb-4">
                                <h3 className="text-sm font-bold text-gray-700 mb-2">TEXTO DEL MENSAJE:</h3>
                                <div className="bg-gray-100 p-3 rounded-lg font-mono text-sm border border-gray-300">
                                    {mensaje.contenido}
                                </div>
                            </div>

                            {/* Observación del sistema */}
                            <div className="mb-4">
                                <h3 className="text-sm font-bold text-gray-700 mb-2">OBSERVACIÓN DEL SISTEMA:</h3>
                                <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-300 space-y-1 text-sm">
                                    {mensaje.clasificacion?.IMPORTANTE?.map((item, i) => (
                                        <div key={i} className="flex items-start gap-2 text-red-700">
                                            <span>🔴</span>
                                            <span>{item}</span>
                                        </div>
                                    ))}
                                    {mensaje.clasificacion?.OBSERVACIONES?.map((item, i) => (
                                        <div key={i} className="flex items-start gap-2 text-yellow-700">
                                            <span>🟡</span>
                                            <span>{item}</span>
                                        </div>
                                    ))}
                                    {mensaje.clasificacion?.SUGERENCIAS?.map((item, i) => (
                                        <div key={i} className="flex items-start gap-2 text-blue-700">
                                            <span>💡</span>
                                            <span>{item}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Comentario del validador */}
                            <div className="mb-6">
                                <h3 className="text-sm font-bold text-gray-700 mb-2">COMENTARIO DEL VALIDADOR:</h3>
                                <textarea
                                    value={reportComment}
                                    onChange={(e) => setReportComment(e.target.value)}
                                    className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none resize-none text-sm"
                                    placeholder="Explicá por qué el sistema se equivocó en su evaluación..."
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
                                    className="flex-1 py-3 px-4 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-semibold border border-gray-300"
                                >
                                    CANCELAR
                                </button>
                                <button
                                    onClick={handleReportSubmit}
                                    disabled={!reportComment.trim()}
                                    className="flex-1 py-3 px-4 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    DERIVAR A ARIEL
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
