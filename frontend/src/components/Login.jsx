import React, { useState } from 'react';
import { login } from '../services/api';
import { User, Lock, AlertCircle, Train } from 'lucide-react';

const Login = ({ onLoginSuccess }) => {
    const [usuario, setUsuario] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await login(usuario, password);
            if (data.ok) {
                onLoginSuccess(data.nombre);
            } else {
                setError('Credenciales incorrectas. Verificá usuario y contraseña.');
            }
        } catch (err) {
            console.error(err);
            setError('Error de conexión con el servidor');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4">
            <div className="w-full max-w-md animate-fade-in">
                {/* Logo / Branding */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-lg mb-4">
                        <Train className="text-white" size={32} />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
                        Validación SOFSE
                    </h1>
                    <p className="text-gray-500 mt-1 text-sm">
                        Sistema de Validación de Mensajes Ferroviarios
                    </p>
                </div>

                {/* Card */}
                <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                    {error && (
                        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center gap-2.5 animate-fade-in">
                            <AlertCircle size={18} className="shrink-0" />
                            <span className="text-sm font-medium">{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                                Usuario
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <User size={18} className="text-gray-400" />
                                </div>
                                <input
                                    type="text"
                                    value={usuario}
                                    onChange={(e) => setUsuario(e.target.value)}
                                    className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl
                                               focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:bg-white
                                               outline-none text-sm placeholder:text-gray-400"
                                    placeholder="Ingresá tu usuario"
                                    required
                                    autoComplete="username"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                                Contraseña
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <Lock size={18} className="text-gray-400" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl
                                               focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:bg-white
                                               outline-none text-sm placeholder:text-gray-400"
                                    placeholder="Tu contraseña"
                                    required
                                    autoComplete="current-password"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={`w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600
                                       hover:from-blue-700 hover:to-indigo-700
                                       text-white font-semibold rounded-xl shadow-md
                                       hover:shadow-lg active:scale-[0.98]
                                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                                       ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Ingresando...
                                </span>
                            ) : (
                                'Ingresar'
                            )}
                        </button>
                    </form>
                </div>

                {/* Footer */}
                <p className="text-center text-xs text-gray-400 mt-6">
                    SOFSE - Operadora Ferroviaria
                </p>
            </div>
        </div>
    );
};

export default Login;
