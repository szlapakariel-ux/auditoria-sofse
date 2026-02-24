/**
 * bookmarklet.js — Enviar mensajes SOFSE a Auditoría
 * ===================================================
 * Este script se ejecuta en el contexto de la página del portal VPN SOFSE.
 * Lee los div.panel-mensaje de la página actual y los envía al backend.
 *
 * INSTALACIÓN:
 *   1. Crear un favorito nuevo en Chrome
 *   2. En "URL" pegar el contenido minificado (ver abajo)
 *   3. Navegar al portal VPN → mensajes → tocar el favorito
 *
 * La versión minificada para bookmarklet está al final de este archivo.
 */

(function() {
    // ===== CONFIGURACIÓN =====
    // Cambiar esta URL a la de tu backend en Render
    var BACKEND = 'https://auditoria-sofse.onrender.com';
    var TOKEN = 'sofse2026';
    // =========================

    // Verificar que estamos en una página con mensajes
    var paneles = document.querySelectorAll('div.panel-mensaje');
    if (paneles.length === 0) {
        alert('No se encontraron mensajes en esta página.\n\nAsegurate de estar en la página de mensajes del portal SOFSE.');
        return;
    }

    // Extraer mensajes
    var mensajes = [];
    paneles.forEach(function(panel) {
        try {
            var idMensaje = panel.getAttribute('data-id_mensaje') || '';
            var titulo = panel.querySelector('h3.panel-title');
            var tituloTxt = titulo ? titulo.textContent.trim() : '';

            // fecha y hora
            var matchFH = tituloTxt.match(/(\d{2}\/\d{2}\/\d{4})\s+(\d{2}:\d{2}:\d{2})/);
            var fecha = matchFH ? matchFH[1] : '';
            var hora = matchFH ? matchFH[2] : '';

            // numero de mensaje
            var matchNum = tituloTxt.match(/#(\d+)/);
            var numeroMensaje = matchNum ? matchNum[1] : '';

            // linea
            var spanLinea = panel.querySelector('span.hidden-sm');
            var linea = spanLinea ? spanLinea.textContent.trim() : '';

            // criticidad
            var lblCrit = panel.querySelector('span.label-criticidad');
            var criticidad = lblCrit ? lblCrit.textContent.trim() : '';

            // tipificacion y estado desde inputs
            var tipificacion = '', estadoMsg = '';
            panel.querySelectorAll('input.form-control').forEach(function(inp) {
                var val = inp.value || '';
                if (/DEMORA|CANCELACI|REDUCIDO|SUSPENDIDO/.test(val)) tipificacion = val;
                if (/^(Nuevo|Modificaci|Baja)/.test(val)) estadoMsg = val;
            });

            // contenido
            var textarea = panel.querySelector('textarea.form-control');
            var contenido = textarea ? textarea.textContent.trim() : '';

            // operador
            var divOp = panel.querySelector('div[style*="font-size: 11px"]');
            var operador = divOp ? divOp.textContent.trim().replace('Operador: ', '') : '';

            // grupos
            var grupos = [];
            var selGrupos = panel.querySelector('select.selector-js');
            if (selGrupos) {
                selGrupos.querySelectorAll('option[selected]').forEach(function(o) {
                    grupos.push(o.textContent.trim());
                });
            }

            mensajes.push({
                id_mensaje: idMensaje,
                numero_mensaje: numeroMensaje,
                fecha: fecha,
                hora: hora,
                fecha_hora: fecha + ' ' + hora,
                linea: linea,
                criticidad: criticidad,
                tipificacion: tipificacion,
                estado: estadoMsg,
                contenido: contenido,
                operador: operador,
                grupos: grupos,
                estado_sms: '',
                estado_email: ''
            });
        } catch(e) {
            // ignorar mensajes que no se pudieron parsear
        }
    });

    if (mensajes.length === 0) {
        alert('Se encontraron paneles pero no se pudo extraer ningún mensaje.');
        return;
    }

    // Confirmar envío
    if (!confirm('Se encontraron ' + mensajes.length + ' mensajes.\n\n¿Enviar a Auditoría SOFSE?')) {
        return;
    }

    // Enviar al backend
    fetch(BACKEND + '/api/scraping/importar?token=' + TOKEN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            mensajes: mensajes,
            pagina_url: window.location.href
        })
    })
    .then(function(r) { return r.json(); })
    .then(function(res) {
        if (res.ok) {
            alert(
                'Importación completada\n\n' +
                '✅ ' + res.nuevos + ' nuevos\n' +
                '⟳ ' + res.duplicados + ' duplicados' +
                (res.errores > 0 ? '\n⚠️ ' + res.errores + ' errores' : '')
            );
        } else {
            alert('Error: ' + (res.error || 'Error desconocido'));
        }
    })
    .catch(function(e) {
        alert('Error de conexión: ' + e.message + '\n\nVerificá que el servidor esté activo.');
    });
})();

/**
 * VERSIÓN MINIFICADA PARA BOOKMARKLET:
 * Copiar la siguiente línea como URL del favorito.
 * IMPORTANTE: Cambiar BACKEND_URL por la URL real de tu app en Render.
 *
 * javascript:void(function(){var B='https://auditoria-sofse.onrender.com',T='sofse2026',p=document.querySelectorAll('div.panel-mensaje');if(!p.length){alert('No se encontraron mensajes en esta página.');return}var m=[];p.forEach(function(panel){try{var id=panel.getAttribute('data-id_mensaje')||'',t=panel.querySelector('h3.panel-title'),tt=t?t.textContent.trim():'',mf=tt.match(/(\d{2}\/\d{2}\/\d{4})\s+(\d{2}:\d{2}:\d{2})/),f=mf?mf[1]:'',h=mf?mf[2]:'',mn=tt.match(/#(\d+)/),n=mn?mn[1]:'',sl=panel.querySelector('span.hidden-sm'),l=sl?sl.textContent.trim():'',lc=panel.querySelector('span.label-criticidad'),c=lc?lc.textContent.trim():'',tp='',es='';panel.querySelectorAll('input.form-control').forEach(function(i){var v=i.value||'';if(/DEMORA|CANCELACI|REDUCIDO|SUSPENDIDO/.test(v))tp=v;if(/^(Nuevo|Modificaci|Baja)/.test(v))es=v});var ta=panel.querySelector('textarea.form-control'),co=ta?ta.textContent.trim():'',dop=panel.querySelector('div[style*="font-size: 11px"]'),op=dop?dop.textContent.trim().replace('Operador: ',''):'',g=[];var sg=panel.querySelector('select.selector-js');if(sg)sg.querySelectorAll('option[selected]').forEach(function(o){g.push(o.textContent.trim())});m.push({id_mensaje:id,numero_mensaje:n,fecha:f,hora:h,fecha_hora:f+' '+h,linea:l,criticidad:c,tipificacion:tp,estado:es,contenido:co,operador:op,grupos:g,estado_sms:'',estado_email:''})}catch(e){}});if(!m.length){alert('No se pudo extraer ningún mensaje.');return}if(!confirm(m.length+' mensajes encontrados.\n\n¿Enviar a Auditoría?'))return;fetch(B+'/api/scraping/importar?token='+T,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensajes:m,pagina_url:location.href})}).then(function(r){return r.json()}).then(function(r){if(r.ok)alert('✅ '+r.nuevos+' nuevos\n⟳ '+r.duplicados+' duplicados'+(r.errores>0?'\n⚠️ '+r.errores+' errores':''));else alert('Error: '+(r.error||'desconocido'))}).catch(function(e){alert('Error: '+e.message)})})();
 */
