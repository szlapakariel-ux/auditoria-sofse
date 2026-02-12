import { useState } from 'react';
import { ChevronDown, ChevronUp, Lock, Eye } from 'lucide-react';

export default function MensajesBloqueados({ mensajes, onVerDetalle }) {
    const [expandido, setExpandido] = useState(false);

    if (!mensajes || mensajes.length === 0) {
        return null;
    }

    return (
        <div className="mb-6">
            {/* Header colapsable */}
            <button
                onClick={() => setExpandido(!expandido)}
                className="w-full bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4 flex items-center justify-between hover:bg-yellow-100 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <Lock className="text-yellow-700" size={24} />
                    <div className="text-left">
                        <h3 className="font-bold text-yellow-800 text-lg">
                            MENSAJES BLOQUEADOS - REVISIÓN CON ARIEL
                        </h3>
                        <p className="text-sm text-yellow-600">
                            {mensajes.length} mensaje{mensajes.length !== 1 ? 's' : ''} pendiente{mensajes.length !== 1 ? 's' : ''} de revisar juntos
                        </p>
                    </div>
                </div>
                {expandido ? (
                    <ChevronUp className="text-yellow-700" size={24} />
                ) : (
                    <ChevronDown className="text-yellow-700" size={24} />
                )}
            </button>

            {/* Contenido expandible */}
            {expandido && (
                <div className="mt-2 bg-yellow-50 border-2 border-yellow-300 border-t-0 rounded-b-lg p-4 space-y-3">
                    {mensajes.map((mensaje, index) => (
                        <div
                            key={mensaje.id}
                            className="bg-white p-4 rounded-lg border border-yellow-200 shadow-sm"
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <p className="font-bold text-gray-800">
                                        🟡 Mensaje #{mensaje.id}
                                    </p>
                                    <p className="text-sm text-gray-600">
                                        {mensaje.operador} | {mensaje.fecha_hora}
                                    </p>
                                </div>
                                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded font-semibold">
                                    BLOQUEADO
                                </span>
                            </div>

                            <div className="mb-3 p-3 bg-blue-50 rounded border border-blue-200">
                                <p className="text-xs font-bold text-blue-700 mb-1">
                                    💬 EXPLICACIÓN DE ARIEL:
                                </p>
                                <p className="text-sm text-blue-800">
                                    {mensaje.explicacion_ariel || 'Sin explicación'}
                                </p>
                            </div>

                            <button
                                onClick={() => onVerDetalle(mensaje)}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
                            >
                                <Eye size={18} />
                                VER MENSAJE COMPLETO
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
