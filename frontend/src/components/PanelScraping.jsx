import React, { useState, useEffect } from 'react';
import { Download, ChevronDown, ChevronUp, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { scrapingSanMartin } from '../services/api';

const PanelScraping = ({ usuario, lineaActual }) => {
    // ⚠️ TODOS los hooks ANTES de cualquier return condicional (regla de React)
    const [abierto, setAbierto] = useState(false);
    const [vpnUser, setVpnUser] = useState(usuario || '');
    const [vpnPassword, setVpnPassword] = useState('');
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');
    const [loading, setLoading] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [error, setError] = useState('');

    // Calcular fecha de hoy en DD/MM/YYYY
    const hoyStr = () => {
        const hoy = new Date();
        const d = String(hoy.getDate()).padStart(2, '0');
        const m = String(hoy.getMonth() + 1).padStart(2, '0');
        const y = hoy.getFullYear();
        return `${d}/${m}/${y}`;
    };

    // Inicializar fechas con hoy
    useEffect(() => {
        const h = hoyStr();
        setFechaInicio(h);
        setFechaFin(h);
    }, []);

    // Cargar último resultado guardado
    useEffect(() => {
        const guardado = localStorage.getItem('ultimoScrapingSanMartin');
        if (guardado) {
            try {
                setResultado(JSON.parse(guardado));
            } catch (e) {
                // ignorar
            }
        }
    }, []);

    // Solo mostrar para San Martín — return condicional DESPUÉS de todos los hooks
    const esSanMartin = lineaActual && lineaActual.toLowerCase().includes('san mart');
    if (!esSanMartin) return null;

    const handleImportar = async () => {
        setError('');
        setResultado(null);

        if (!vpnUser.trim() || !vpnPassword.trim()) {
            setError('Ingresá usuario y contraseña VPN.');
            return;
        }
        if (!fechaInicio || !fechaFin) {
            setError('Ingresá las fechas de búsqueda.');
            return;
        }

        setLoading(true);
        try {
            const res = await scrapingSanMartin(vpnUser, vpnPassword, fechaInicio, fechaFin);
            if (res.ok) {
                const r = {
                    nuevos:     res.nuevos,
                    duplicados: res.duplicados,
                    errores:    res.errores,
                    timestamp:  res.timestamp,
                };
                setResultado(r);
                localStorage.setItem('ultimoScrapingSanMartin', JSON.stringify(r));
                setVpnPassword(''); // Limpiar contraseña por seguridad
            } else {
                setError(res.error || 'Error desconocido al importar.');
            }
        } catch (e) {
            const msg = e?.response?.data?.error || e?.message || 'Error de conexión.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    const formatTimestamp = (ts) => {
        if (!ts) return '';
        try {
            const d = new Date(ts);
            return d.toLocaleString('es-AR', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        } catch (e) {
            return ts;
        }
    };

    return (
        <div className="mb-4 border border-blue-200 rounded-xl overflow-hidden bg-white shadow-sm">
            {/* Header colapsable */}
            <button
                onClick={() => setAbierto(!abierto)}
                className="w-full flex items-center justify-between px-4 py-3 bg-blue-50 hover:bg-blue-100 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <Download size={18} className="text-blue-600" />
                    <span className="font-semibold text-blue-800 text-sm">
                        Importar mensajes desde SOFSE
                    </span>
                    {resultado && (
                        <span className="text-xs text-blue-500 ml-1">
                            · Último: {formatTimestamp(resultado.timestamp)}
                        </span>
                    )}
                </div>
                {abierto
                    ? <ChevronUp size={18} className="text-blue-600" />
                    : <ChevronDown size={18} className="text-blue-600" />
                }
            </button>

            {/* Contenido */}
            {abierto && (
                <div className="p-4 space-y-3">
                    {/* Usuario VPN */}
                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                            Usuario VPN
                        </label>
                        <input
                            type="text"
                            value={vpnUser}
                            onChange={e => setVpnUser(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                            placeholder="Tu usuario del portal VPN"
                            autoComplete="off"
                            disabled={loading}
                        />
                    </div>

                    {/* Contraseña VPN */}
                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                            Contraseña VPN
                        </label>
                        <input
                            type="password"
                            value={vpnPassword}
                            onChange={e => setVpnPassword(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                            placeholder="Tu contraseña del portal VPN"
                            autoComplete="new-password"
                            disabled={loading}
                        />
                    </div>

                    {/* Fechas */}
                    <div className="flex gap-2">
                        <div className="flex-1">
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                                Desde
                            </label>
                            <input
                                type="text"
                                value={fechaInicio}
                                onChange={e => setFechaInicio(e.target.value)}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                                placeholder="DD/MM/AAAA"
                                disabled={loading}
                            />
                        </div>
                        <div className="flex-1">
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                                Hasta
                            </label>
                            <input
                                type="text"
                                value={fechaFin}
                                onChange={e => setFechaFin(e.target.value)}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                                placeholder="DD/MM/AAAA"
                                disabled={loading}
                            />
                        </div>
                    </div>

                    {/* Botón importar */}
                    <button
                        onClick={handleImportar}
                        disabled={loading}
                        className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300
                                   text-white rounded-lg font-semibold text-sm flex items-center
                                   justify-center gap-2 transition-colors"
                    >
                        {loading ? (
                            <>
                                <Loader size={16} className="animate-spin" />
                                Importando mensajes...
                            </>
                        ) : (
                            <>
                                <Download size={16} />
                                Importar mensajes
                            </>
                        )}
                    </button>

                    {/* Error */}
                    {error && (
                        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                    )}

                    {/* Resultado exitoso */}
                    {resultado && !error && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                            <div className="flex items-center gap-2 mb-1">
                                <CheckCircle size={16} className="text-green-600" />
                                <span className="text-sm font-semibold text-green-800">
                                    Importación completada
                                </span>
                            </div>
                            <div className="flex gap-4 text-sm text-green-700">
                                <span>✅ {resultado.nuevos} nuevos</span>
                                <span>⟳ {resultado.duplicados} duplicados</span>
                                {resultado.errores > 0 && (
                                    <span>⚠️ {resultado.errores} errores</span>
                                )}
                            </div>
                            {resultado.nuevos > 0 && (
                                <p className="text-xs text-green-600 mt-1">
                                    Los mensajes nuevos ya están disponibles para validar.
                                </p>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default PanelScraping;
