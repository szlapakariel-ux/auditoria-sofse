import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import SelectorLinea from './components/SelectorLinea';
import ValidadorMensajes from './components/ValidadorMensajes';
import PanelErrores from './components/PanelErrores';
import { getSession, logout } from './services/api';
import { LogOut, LayoutDashboard, Bug, Train } from 'lucide-react';

function App() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [currentView, setCurrentView] = useState('login'); // login, selector, validator, errors
    const [mensajes, setMensajes] = useState([]);
    const [lineaActual, setLineaActual] = useState('');

    useEffect(() => {
        checkSession();

        // Keep-alive ping cada 10 min para que Render free no apague el servicio
        const keepAlive = setInterval(() => {
            fetch('/health').catch(() => {});
        }, 10 * 60 * 1000); // 10 minutos
        return () => clearInterval(keepAlive);
    }, []);

    const checkSession = async () => {
        try {
            const data = await getSession();
            if (data.ok) {
                setUser(data.nombre);
                setCurrentView('selector');
            } else {
                setCurrentView('login');
            }
        } catch (err) {
            console.error('Session check failed', err);
            setCurrentView('login');
        } finally {
            setLoading(false);
        }
    };

    const handleLoginSuccess = (nombre) => {
        setUser(nombre);
        setCurrentView('selector');
    };

    const handleLogout = async () => {
        try {
            await logout();
            setUser(null);
            setCurrentView('login');
            setMensajes([]);
        } catch (err) {
            console.error('Logout failed', err);
        }
    };

    const handleLineaSeleccionada = (mensajesCargados, nombreLinea = '') => {
        setMensajes(mensajesCargados);
        setLineaActual(nombreLinea);
        setCurrentView('validator');
    };

    const handleCambiarLinea = () => {
        setMensajes([]);
        setLineaActual('');
        setCurrentView('selector');
    };

    if (loading) {
        return (
            <div className="flex h-screen w-full items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50">
                <div className="text-center">
                    <div className="h-12 w-12 mx-auto animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
                    <p className="mt-4 text-sm text-gray-500 font-medium">Cargando...</p>
                </div>
            </div>
        );
    }

    if (currentView === 'login') {
        return <Login onLoginSuccess={handleLoginSuccess} />;
    }

    return (
        <div className="min-h-screen bg-[#f0f4f8]">
            {/* Navbar */}
            <nav className="bg-white/80 backdrop-blur-lg border-b border-gray-200/60 sticky top-0 z-50 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-14 sm:h-16">
                        {/* Left: Logo + Admin Nav */}
                        <div className="flex items-center gap-3">
                            <div className="flex-shrink-0 flex items-center gap-2.5">
                                <div className="h-9 w-9 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-md">
                                    <Train size={18} className="text-white" />
                                </div>
                                <div className="hidden sm:block">
                                    <span className="font-bold text-lg text-gray-900 tracking-tight">
                                        SOFSE
                                    </span>
                                    <span className="text-gray-400 font-normal text-sm ml-1.5">
                                        Validación
                                    </span>
                                </div>
                            </div>

                            {/* Ariel's Admin Tools */}
                            {user === 'Ariel' && (
                                <div className="hidden md:flex ml-6 gap-1">
                                    <button
                                        onClick={() => setCurrentView('selector')}
                                        className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                                            currentView === 'selector' || currentView === 'validator'
                                                ? 'bg-blue-50 text-blue-700 shadow-sm'
                                                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                                        }`}
                                    >
                                        <div className="flex items-center gap-2">
                                            <LayoutDashboard size={16} />
                                            Validación
                                        </div>
                                    </button>
                                    <button
                                        onClick={() => setCurrentView('errors')}
                                        className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                                            currentView === 'errors'
                                                ? 'bg-red-50 text-red-700 shadow-sm'
                                                : 'text-gray-500 hover:text-red-600 hover:bg-red-50'
                                        }`}
                                    >
                                        <div className="flex items-center gap-2">
                                            <Bug size={16} />
                                            Errores
                                        </div>
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Right: User Info + Logout */}
                        <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2.5">
                                <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    <span className="text-blue-700 font-bold text-sm">
                                        {user?.charAt(0)?.toUpperCase()}
                                    </span>
                                </div>
                                <div className="hidden sm:block text-right">
                                    <p className="text-sm font-semibold text-gray-900 leading-tight">{user}</p>
                                    <p className="text-xs text-emerald-600 font-medium flex items-center gap-1 justify-end">
                                        <span className="h-1.5 w-1.5 bg-emerald-500 rounded-full inline-block"></span>
                                        Conectado
                                    </p>
                                </div>
                            </div>
                            <div className="h-6 w-px bg-gray-200 hidden sm:block"></div>
                            <button
                                onClick={handleLogout}
                                className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-all"
                                title="Cerrar Sesión"
                            >
                                <LogOut size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Mobile Admin Nav for Ariel */}
            {user === 'Ariel' && (
                <div className="md:hidden bg-white border-b border-gray-200 px-4 py-2 flex gap-2 sticky top-14 z-40">
                    <button
                        onClick={() => setCurrentView('selector')}
                        className={`flex-1 py-2 rounded-lg text-xs font-semibold text-center transition-all ${
                            currentView === 'selector' || currentView === 'validator'
                                ? 'bg-blue-50 text-blue-700'
                                : 'text-gray-500 hover:bg-gray-50'
                        }`}
                    >
                        Validación
                    </button>
                    <button
                        onClick={() => setCurrentView('errors')}
                        className={`flex-1 py-2 rounded-lg text-xs font-semibold text-center transition-all ${
                            currentView === 'errors'
                                ? 'bg-red-50 text-red-700'
                                : 'text-gray-500 hover:bg-red-50'
                        }`}
                    >
                        Panel Errores
                    </button>
                </div>
            )}

            {/* Main Content */}
            <main className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
                <div className="animate-fade-in">
                    {currentView === 'selector' && (
                        <SelectorLinea onLineaSeleccionada={handleLineaSeleccionada} />
                    )}

                    {currentView === 'validator' && (
                        <ValidadorMensajes
                            mensajesIniciales={mensajes}
                            usuario={user}
                            lineaActual={lineaActual}
                            onCambiarLinea={handleCambiarLinea}
                        />
                    )}

                    {currentView === 'errors' && user === 'Ariel' && (
                        <PanelErrores />
                    )}
                </div>
            </main>
        </div>
    );
}

export default App;
