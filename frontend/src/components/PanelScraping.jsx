import React, { useState, useEffect } from 'react';
import { Download, ChevronDown, ChevronUp, AlertCircle, CheckCircle, Loader, Globe, Search } from 'lucide-react';
import { scrapingIniciar, scrapingExtraer } from '../services/api';

const PanelScraping = ({ usuario, lineaActual }) => {
    // ---- Hooks (SIEMPRE antes de cualquier return condicional) ----
    const [abierto, setAbierto] = useState(false);
    const [vpnUser, setVpnUser] = useState(usuario || '');
    const [vpnPassword, setVpnPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [resultado, setResultado] = useState(null);

    // Paso actual: 'login' o 'extraer'
    const [paso, setPaso] = useState('login');
    const [browserAbierto, setBrowserAbierto] = useState(false);
    const [urlLogin, setUrlLogin] = useState('');

    // Cargar último resultado guardado
    useEffect(() => {
        const guardado = localStorage.getItem('ultimoScrapingSanMartin');
        if (guardado) {
            try {
                setResultado(JSON.parse(guardado));
            } catch (e) { /* ignorar */ }
        }
    }, []);

    // ---- Return condicional DESPUÉS de todos los hooks ----
    const esSanMartin = lineaActual && lineaActual.toLowerCase().includes('san mart');
    if (!esSanMartin) return null;

    // ---- Handlers ----

    const handleAbrirPortal = async () => {
        setError('');
        setResultado(null);

        if (!vpnUser.trim() || !vpnPassword.trim()) {
            setError('Ingresá usuario y contraseña VPN.');
            return;
        }

        setLoading(true);
        try {
            const res = await scrapingIniciar(vpnUser, vpnPassword);
            if (res.ok) {
                setBrowserAbierto(true);
                setPaso('extraer');
                setUrlLogin(res.url || '');
                setVpnPassword(''); // Limpiar por seguridad
            } else {
                setError(res.error || res.mensaje || 'Error al abrir el portal.');
            }
        } catch (e) {
            const msg = e?.response?.data?.error || e?.message || 'Error de conexión.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleExtraer = async () => {
        setError('');
        setResultado(null);
        setLoading(true);

        try {
            const res = await scrapingExtraer();
            if (res.ok) {
                const r = {
                    nuevos:     res.nuevos,
                    duplicados: res.duplicados,
                    errores:    res.errores,
                    timestamp:  res.timestamp,
                    url_leida:  res.url_leida,
                };
                setResultado(r);
                localStorage.setItem('ultimoScrapingSanMartin', JSON.stringify(r));
            } else {
                setError(res.error || 'No se encontraron mensajes. Asegurate de estar en la página de mensajes.');
            }
        } catch (e) {
            const msg = e?.response?.data?.error || e?.message || 'Error de conexión.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleVolver = () => {
        setPaso('login');
        setBrowserAbierto(false);
        setError('');
        setResultado(null);
    };

    const formatTimestamp = (ts) => {
        if (!ts) return '';
        try {
            const d = new Date(ts);
            return d.toLocaleString('es-AR', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        } catch (e) { return ts; }
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
                    {browserAbierto && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                            Chrome abierto
                        </span>
                    )}
                    {resultado && !browserAbierto && (
                        <span className="text-xs text-blue-500 ml-1">
                            {'\u00b7'} {formatTimestamp(resultado.timestamp)}
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

                    {/* ========== PASO 1: Login ========== */}
                    {paso === 'login' && (
                        <>
                            <p className="text-xs text-gray-500">
                                Ingresá tus credenciales del portal VPN. Se abrirá Chrome automáticamente para hacer login.
                            </p>

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
                                    onKeyDown={e => e.key === 'Enter' && !loading && handleAbrirPortal()}
                                />
                            </div>

                            {/* Botón abrir portal */}
                            <button
                                onClick={handleAbrirPortal}
                                disabled={loading}
                                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300
                                           text-white rounded-lg font-semibold text-sm flex items-center
                                           justify-center gap-2 transition-colors"
                            >
                                {loading ? (
                                    <>
                                        <Loader size={16} className="animate-spin" />
                                        Abriendo Chrome y logueando...
                                    </>
                                ) : (
                                    <>
                                        <Globe size={16} />
                                        Abrir portal VPN
                                    </>
                                )}
                            </button>
                        </>
                    )}

                    {/* ========== PASO 2: Extraer ========== */}
                    {paso === 'extraer' && (
                        <>
                            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                                <p className="text-sm text-blue-800 font-medium mb-1">
                                    Chrome abierto y logueado
                                </p>
                                <ol className="text-xs text-blue-700 space-y-1 list-decimal list-inside">
                                    <li>Navegá a la página de <strong>mensajes</strong> de tu línea en el Chrome que se abrió</li>
                                    <li>Cuando estés en el listado de mensajes, volvé acá y tocá el botón</li>
                                </ol>
                            </div>

                            {/* Botón extraer */}
                            <button
                                onClick={handleExtraer}
                                disabled={loading}
                                className="w-full py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-green-300
                                           text-white rounded-lg font-semibold text-sm flex items-center
                                           justify-center gap-2 transition-colors"
                            >
                                {loading ? (
                                    <>
                                        <Loader size={16} className="animate-spin" />
                                        Leyendo mensajes...
                                    </>
                                ) : (
                                    <>
                                        <Search size={16} />
                                        Extraer mensajes de la página actual
                                    </>
                                )}
                            </button>

                            {/* Botón volver */}
                            <button
                                onClick={handleVolver}
                                disabled={loading}
                                className="w-full py-1.5 text-gray-500 hover:text-gray-700 text-xs
                                           font-medium transition-colors"
                            >
                                Volver al login
                            </button>
                        </>
                    )}

                    {/* ========== Error ========== */}
                    {error && (
                        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                    )}

                    {/* ========== Resultado exitoso ========== */}
                    {resultado && !error && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                            <div className="flex items-center gap-2 mb-1">
                                <CheckCircle size={16} className="text-green-600" />
                                <span className="text-sm font-semibold text-green-800">
                                    Importación completada
                                </span>
                            </div>
                            <div className="flex gap-4 text-sm text-green-700">
                                <span>{resultado.nuevos} nuevos</span>
                                <span>{resultado.duplicados} duplicados</span>
                                {resultado.errores > 0 && (
                                    <span>{resultado.errores} errores</span>
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
