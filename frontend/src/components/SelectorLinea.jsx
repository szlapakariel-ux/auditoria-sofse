import React, { useEffect, useState } from 'react';
import { getLineasDisponibles, seleccionarLinea } from '../services/api';
import { Train, Loader2, ArrowRight, AlertCircle } from 'lucide-react';

const SelectorLinea = ({ onLineaSeleccionada }) => {
    const [lineas, setLineas] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selecting, setSelecting] = useState('');

    useEffect(() => {
        const fetchLineas = async () => {
            try {
                const data = await getLineasDisponibles();
                if (data.ok) {
                    setLineas(data.lineas);
                } else {
                    setError('Error al cargar líneas disponibles');
                }
            } catch (err) {
                setError('Error de conexión con el servidor');
            } finally {
                setLoading(false);
            }
        };
        fetchLineas();
    }, []);

    const handleSelect = async (linea) => {
        setSelecting(linea);
        try {
            const data = await seleccionarLinea(linea);
            if (data.ok) {
                onLineaSeleccionada(data.mensajes, linea);
            } else {
                alert('Error al seleccionar la línea');
            }
        } catch (err) {
            alert('Error de conexión');
        } finally {
            setSelecting('');
        }
    };

    // Colores por línea (para distinguir visualmente)
    const lineaColors = {
        default: { bg: 'from-blue-500 to-blue-700', light: 'bg-blue-50', badge: 'bg-blue-100 text-blue-700', border: 'border-blue-200' },
    };

    const getColor = () => lineaColors.default;

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 animate-fade-in">
                <div className="relative">
                    <Loader2 className="animate-spin text-blue-600" size={40} />
                </div>
                <p className="text-gray-500 mt-4 text-sm font-medium">Cargando líneas...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-64 animate-fade-in">
                <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center max-w-sm">
                    <AlertCircle className="text-red-500 mx-auto mb-3" size={32} />
                    <p className="text-red-700 font-medium">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-4 text-sm text-red-600 hover:text-red-800 font-semibold underline"
                    >
                        Reintentar
                    </button>
                </div>
            </div>
        );
    }

    const lineasArr = Object.entries(lineas);

    return (
        <div className="py-4 sm:py-8 animate-fade-in">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="text-center mb-8 sm:mb-10">
                    <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-lg mb-4">
                        <Train size={28} className="text-white" />
                    </div>
                    <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
                        Seleccioná una línea
                    </h2>
                    <p className="text-gray-500 mt-2 text-sm">
                        Elegí la línea ferroviaria para comenzar a validar mensajes
                    </p>
                </div>

                {/* Grid de líneas */}
                {lineasArr.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
                        {lineasArr.map(([nombre, cantidad], index) => {
                            const colors = getColor();
                            const isSelecting = selecting === nombre;

                            return (
                                <button
                                    key={nombre}
                                    onClick={() => handleSelect(nombre)}
                                    disabled={selecting !== ''}
                                    className={`
                                        relative group p-6 sm:p-7 rounded-2xl border-2 transition-all duration-300
                                        flex flex-col items-center justify-center gap-3 text-center
                                        ${isSelecting
                                            ? 'bg-blue-50 border-blue-400 scale-[0.97]'
                                            : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-lg hover:-translate-y-1 active:scale-[0.97]'
                                        }
                                    `}
                                    style={{ animationDelay: `${index * 80}ms` }}
                                >
                                    {isSelecting && (
                                        <div className="absolute inset-0 bg-white/70 backdrop-blur-sm flex items-center justify-center rounded-2xl z-10">
                                            <Loader2 className="animate-spin text-blue-600" size={28} />
                                        </div>
                                    )}

                                    {/* Nombre de la línea */}
                                    <h3 className="text-lg font-bold text-gray-900 leading-tight group-hover:text-blue-700 transition-colors">
                                        {nombre}
                                    </h3>

                                    {/* Badge de cantidad */}
                                    <div className={`${colors.badge} px-4 py-1.5 rounded-full text-sm font-semibold`}>
                                        {cantidad} pendiente{cantidad !== 1 ? 's' : ''}
                                    </div>

                                    {/* Arrow indicator */}
                                    <ArrowRight
                                        size={16}
                                        className="text-gray-300 group-hover:text-blue-500 group-hover:translate-x-1 transition-all absolute right-4 top-1/2 -translate-y-1/2 hidden sm:block"
                                    />
                                </button>
                            );
                        })}
                    </div>
                ) : (
                    <div className="text-center bg-white rounded-2xl p-10 border border-gray-200 shadow-sm">
                        <div className="text-4xl mb-3">
                            &#10024;
                        </div>
                        <h3 className="font-bold text-gray-800 text-lg mb-1">Todo al día</h3>
                        <p className="text-gray-500 text-sm">
                            No hay mensajes pendientes en ninguna línea.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SelectorLinea;
