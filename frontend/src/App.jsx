import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import SelectorLinea from './components/SelectorLinea';
import ValidadorMensajes from './components/ValidadorMensajes';
import PanelErrores from './components/PanelErrores';
import { getSession, logout } from './services/api';
import { LogOut, LayoutDashboard, Bug } from 'lucide-react';

function App() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [currentView, setCurrentView] = useState('login'); // login, selector, validator, errors
    const [mensajes, setMensajes] = useState([]);
    const [lineaActual, setLineaActual] = useState('');

    useEffect(() => {
        checkSession();
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
            <div className="flex h-screen w-full items-center justify-center bg-gray-50">
                <div className="h-16 w-16 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600"></div>
            </div>
        );
    }

    if (currentView === 'login') {
        return <Login onLoginSuccess={handleLoginSuccess} />;
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Navbar */}
            <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center gap-4">
                            <div className="flex-shrink-0 flex items-center gap-2">
                                <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                                    <span className="text-white font-bold">V</span>
                                </div>
                                <span className="font-bold text-xl text-gray-800 hidden sm:block">Validación Ferroviaria</span>
                            </div>

                            {/* Ariel's Admin Tools */}
                            {user === 'Ariel' && (
                                <div className="hidden md:flex ml-8 space-x-4">
                                    <button
                                        onClick={() => setCurrentView('selector')}
                                        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'selector' || currentView === 'validator'
                                                ? 'bg-gray-100 text-gray-900'
                                                : 'text-gray-500 hover:text-gray-700'
                                            }`}
                                    >
                                        <div className="flex items-center gap-2">
                                            <LayoutDashboard size={18} />
                                            Validación
                                        </div>
                                    </button>
                                    <button
                                        onClick={() => setCurrentView('errors')}
                                        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'errors'
                                                ? 'bg-red-50 text-red-700'
                                                : 'text-gray-500 hover:text-red-600'
                                            }`}
                                    >
                                        <div className="flex items-center gap-2">
                                            <Bug size={18} />
                                            Panel Errores
                                        </div>
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="text-right hidden sm:block">
                                <p className="text-sm font-medium text-gray-900">{user}</p>
                                <p className="text-xs text-green-600 font-medium">● Conectado/a</p>
                            </div>
                            <button
                                onClick={handleLogout}
                                className="p-2 ml-2 text-gray-400 hover:text-red-600 rounded-full hover:bg-red-50 transition-colors"
                                title="Cerrar Sesión"
                            >
                                <LogOut size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
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
            </main>
        </div>
    );
}

export default App;
