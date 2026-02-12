import React, { useEffect, useState } from 'react';
import { getLineasDisponibles, seleccionarLinea } from '../services/api';
import { Train, Loader2 } from 'lucide-react';

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
                setError('Error de conexión');
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
                onLineaSeleccionada(data.mensajes);
            } else {
                alert('Error al seleccionar la línea');
            }
        } catch (err) {
            alert('Error de conexión');
        } finally {
            setSelecting('');
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64">
                <Loader2 className="animate-spin text-blue-600 mb-4" size={48} />
                <p className="text-gray-500">Cargando líneas disponibles...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 text-center">
                <div className="bg-red-50 text-red-600 p-4 rounded-lg inline-block">
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8 flex flex-col items-center justify-center">
            <div className="max-w-4xl w-full">
                <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center flex items-center justify-center gap-3">
                    <Train size={32} className="text-blue-600" />
                    Selecciona una Línea para Validar
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {Object.entries(lineas).map(([nombre, cantidad]) => (
                        <button
                            key={nombre}
                            onClick={() => handleSelect(nombre)}
                            disabled={selecting !== ''}
                            className={`
                relative p-8 rounded-xl shadow-sm border-2 transition-all duration-300
                flex flex-col items-center justify-center gap-4 group
                ${selecting === nombre
                                    ? 'bg-blue-50 border-blue-500 scale-95'
                                    : 'bg-white border-gray-200 hover:border-blue-400 hover:shadow-md hover:-translate-y-1'
                                }
              `}
                        >
                            {selecting === nombre && (
                                <div className="absolute inset-0 bg-white/50 flex items-center justify-center rounded-xl z-10">
                                    <Loader2 className="animate-spin text-blue-600" size={32} />
                                </div>
                            )}

                            <div className="text-xl font-semibold text-gray-800">{nombre}</div>
                            <div className="bg-blue-100 text-blue-800 px-4 py-1 rounded-full text-sm font-medium">
                                {cantidad} mensajes pendientes
                            </div>
                        </button>
                    ))}
                </div>

                {Object.keys(lineas).length === 0 && (
                    <div className="text-center text-gray-500 mt-12 bg-white p-6 rounded-lg shadow-sm">
                        <p>No hay mensajes pendientes en ninguna línea por el momento.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SelectorLinea;
