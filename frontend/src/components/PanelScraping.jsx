import React, { useState, useEffect } from 'react';
import { Download, ChevronDown, ChevronUp, CheckCircle, BookOpen, ExternalLink, Copy } from 'lucide-react';

// URL del backend — en producción usa el mismo dominio, en dev usa localhost
const BACKEND_URL = import.meta.env.VITE_API_URL || '';
const IMPORT_TOKEN = 'sofse2026';

// Bookmarklet minificado — se genera con la URL del backend actual
const generarBookmarklet = (backendUrl, token) => {
    return `javascript:void(function(){var B='${backendUrl}',T='${token}',p=document.querySelectorAll('div.panel-mensaje');if(!p.length){alert('No se encontraron mensajes en esta p\\u00e1gina.');return}var m=[];p.forEach(function(panel){try{var id=panel.getAttribute('data-id_mensaje')||'',t=panel.querySelector('h3.panel-title'),tt=t?t.textContent.trim():'',mf=tt.match(/(\\d{2}\\/\\d{2}\\/\\d{4})\\s+(\\d{2}:\\d{2}:\\d{2})/),f=mf?mf[1]:'',h=mf?mf[2]:'',mn=tt.match(/#(\\d+)/),n=mn?mn[1]:'',sl=panel.querySelector('span.hidden-sm'),l=sl?sl.textContent.trim():'',lc=panel.querySelector('span.label-criticidad'),c=lc?lc.textContent.trim():'',tp='',es='';panel.querySelectorAll('input.form-control').forEach(function(i){var v=i.value||'';if(/DEMORA|CANCELACI|REDUCIDO|SUSPENDIDO/.test(v))tp=v;if(/^(Nuevo|Modificaci|Baja)/.test(v))es=v});var ta=panel.querySelector('textarea.form-control'),co=ta?ta.textContent.trim():'',dop=panel.querySelector('div[style*="font-size: 11px"]'),op=dop?dop.textContent.trim().replace('Operador: ',''):'',g=[];var sg=panel.querySelector('select.selector-js');if(sg)sg.querySelectorAll('option[selected]').forEach(function(o){g.push(o.textContent.trim())});m.push({id_mensaje:id,numero_mensaje:n,fecha:f,hora:h,fecha_hora:f+' '+h,linea:l,criticidad:c,tipificacion:tp,estado:es,contenido:co,operador:op,grupos:g,estado_sms:'',estado_email:''})}catch(e){}});if(!m.length){alert('No se pudo extraer ning\\u00fan mensaje.');return}if(!confirm(m.length+' mensajes encontrados.\\n\\n\\u00bfEnviar a Auditor\\u00eda?'))return;fetch(B+'/api/scraping/importar?token='+T,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensajes:m,pagina_url:location.href})}).then(function(r){return r.json()}).then(function(r){if(r.ok)alert('\\u2705 '+r.nuevos+' nuevos\\n\\u27f3 '+r.duplicados+' duplicados'+(r.errores>0?'\\n\\u26a0\\ufe0f '+r.errores+' errores':''));else alert('Error: '+(r.error||'desconocido'))}).catch(function(e){alert('Error: '+e.message)})})();`;
};

const PanelScraping = ({ usuario, lineaActual }) => {
    const [abierto, setAbierto] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [copiado, setCopiado] = useState(false);

    // Cargar último resultado guardado
    useEffect(() => {
        const guardado = localStorage.getItem('ultimoScrapingSanMartin');
        if (guardado) {
            try {
                setResultado(JSON.parse(guardado));
            } catch (e) { /* ignorar */ }
        }
    }, []);

    // Solo mostrar para San Martín
    const esSanMartin = lineaActual && lineaActual.toLowerCase().includes('san mart');
    if (!esSanMartin) return null;

    // Detectar URL del backend actual
    const currentBackend = BACKEND_URL || window.location.origin;
    const bookmarkletCode = generarBookmarklet(currentBackend, IMPORT_TOKEN);

    const handleCopiarBookmarklet = async () => {
        try {
            await navigator.clipboard.writeText(bookmarkletCode);
            setCopiado(true);
            setTimeout(() => setCopiado(false), 2000);
        } catch (e) {
            // Fallback para mobile
            const ta = document.createElement('textarea');
            ta.value = bookmarkletCode;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            setCopiado(true);
            setTimeout(() => setCopiado(false), 2000);
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
                    {resultado && (
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
                <div className="p-4 space-y-4">
                    {/* Instrucciones */}
                    <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                        <h4 className="font-semibold text-blue-800 text-sm mb-2 flex items-center gap-1">
                            <BookOpen size={14} />
                            Pasos para importar mensajes
                        </h4>
                        <ol className="text-xs text-blue-700 space-y-1.5 list-decimal list-inside">
                            <li>
                                <strong>Primero</strong>: Agregá el bookmarklet a tus favoritos (una sola vez, ver abajo)
                            </li>
                            <li>
                                Abrí el <a
                                    href="https://portalvpn.sofse.gob.ar"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="underline font-medium"
                                >
                                    portal VPN SOFSE <ExternalLink size={10} className="inline" />
                                </a> y logueate con tu usuario
                            </li>
                            <li>Navegá a la página de <strong>mensajes</strong> de tu línea</li>
                            <li>Tocá el favorito <strong>"Enviar a Auditoría"</strong></li>
                            <li>Confirmá el envío y listo</li>
                        </ol>
                    </div>

                    {/* Bookmarklet para copiar/instalar */}
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                        <h4 className="font-semibold text-gray-700 text-sm mb-2">
                            Instalar bookmarklet
                        </h4>

                        {/* En desktop: arrastrar a la barra de favoritos */}
                        <p className="text-xs text-gray-500 mb-2">
                            <strong>PC:</strong> Arrastrá este botón a tu barra de favoritos:
                        </p>
                        <div className="mb-3">
                            <a
                                href={bookmarkletCode}
                                onClick={(e) => e.preventDefault()}
                                className="inline-block px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-semibold
                                           hover:bg-green-700 transition-colors cursor-grab active:cursor-grabbing"
                                title="Arrastrá este botón a tu barra de favoritos"
                            >
                                Enviar a Auditoría
                            </a>
                        </div>

                        {/* En mobile: copiar y crear favorito manual */}
                        <p className="text-xs text-gray-500 mb-2">
                            <strong>Celular:</strong> Copiá el código y creá un favorito con esa URL:
                        </p>
                        <button
                            onClick={handleCopiarBookmarklet}
                            className="flex items-center gap-2 px-3 py-1.5 bg-gray-200 hover:bg-gray-300
                                       rounded text-xs font-medium text-gray-700 transition-colors"
                        >
                            <Copy size={12} />
                            {copiado ? 'Copiado!' : 'Copiar código del bookmarklet'}
                        </button>
                    </div>

                    {/* Último resultado */}
                    {resultado && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                            <div className="flex items-center gap-2 mb-1">
                                <CheckCircle size={16} className="text-green-600" />
                                <span className="text-sm font-semibold text-green-800">
                                    Última importación
                                </span>
                                <span className="text-xs text-green-600">
                                    {formatTimestamp(resultado.timestamp)}
                                </span>
                            </div>
                            <div className="flex gap-4 text-sm text-green-700">
                                <span>{resultado.nuevos} nuevos</span>
                                <span>{resultado.duplicados} duplicados</span>
                                {resultado.errores > 0 && (
                                    <span>{resultado.errores} errores</span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default PanelScraping;
