/**
 * Control Horario - JavaScript Frontend
 * 
 * Maneja toda la interacción con la API y actualización de la UI.
 * Funcionalidades:
 * - Crear, editar y eliminar marcas
 * - Listar marcas agrupadas por día
 * - Validación de formularios
 * - Manejo de errores
 */

const API_BASE = '/api/marcas';

// Estado de la aplicación
const state = {
    marcas: [],
    marcasAgrupadas: [],
    editandoId: null,
    estadisticasSemana: null,
    fechaReferenciaEstadisticas: null // null = semana actual
};

/**
 * Inicializa la aplicación cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando Control Horario...');
    
    // Configurar fecha actual por defecto
    document.getElementById('fecha').valueAsDate = new Date();
    
    // Event listeners
    document.getElementById('formMarca').addEventListener('submit', handleSubmitMarca);
    document.getElementById('btnCancelarEdicion').addEventListener('click', cancelarEdicion);
    
    // Cargar datos iniciales
    cargarMarcasAgrupadas();
    cargarEstadisticasSemana();
});

/**
 * Muestra mensaje de alerta temporal
 */
function mostrarAlerta(mensaje, tipo = 'success') {
    const alertaDiv = document.getElementById('alerta');
    alertaDiv.className = `alert alert-${tipo}`;
    alertaDiv.textContent = mensaje;
    alertaDiv.style.display = 'block';
    
    setTimeout(() => {
        alertaDiv.style.display = 'none';
    }, 5000);
}

/**
 * Muestra/oculta el spinner de carga
 */
function toggleLoading(mostrar) {
    const loading = document.getElementById('loading');
    loading.style.display = mostrar ? 'block' : 'none';
}

/**
 * Carga estadísticas de la semana actual
 */
async function cargarEstadisticasSemana() {
    try {
        // Construir URL con fecha de referencia si existe
        let url = `${API_BASE}/estadisticas/semana`;
        if (state.fechaReferenciaEstadisticas) {
            url += `?fecha=${state.fechaReferenciaEstadisticas}`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Error al cargar estadísticas');
        }
        
        state.estadisticasSemana = await response.json();
        renderizarEstadisticasSemana();
        
    } catch (error) {
        console.error('Error:', error);
        // No mostrar alerta para no molestar si falla
    }
}

/**
 * Renderiza las estadísticas semanales
 */
function renderizarEstadisticasSemana() {
    if (!state.estadisticasSemana) return;
    
    const stats = state.estadisticasSemana;
    
    // Actualizar valores
    document.getElementById('horasTrabajadas').textContent = stats.horas_trabajadas;
    
    // Actualizar horas requeridas (puede variar por feriados)
    const horasReqTexto = stats.horas_requeridas_str || '43:00';
    document.getElementById('horasRequeridas').textContent = horasReqTexto;
    
    document.getElementById('diferencia').textContent = stats.diferencia;
    document.getElementById('porcentaje').textContent = `${stats.porcentaje_completado}%`;
    document.getElementById('diasTrabajados').textContent = stats.dias_trabajados;
    
    // Actualizar Art.15
    if (stats.art15) {
        document.getElementById('art15HorasDisponibles').textContent = stats.art15.horas_disponibles;
    }
    
    // Actualizar fechas de la semana
    const fechaInicio = formatearFechaSemana(stats.fecha_inicio);
    const fechaFin = formatearFechaSemana(stats.fecha_fin);
    document.getElementById('rangoSemana').textContent = `${fechaInicio} - ${fechaFin}`;
    
    // Aplicar color según diferencia
    const difElement = document.getElementById('diferencia');
    const difCard = difElement.closest('.stat-card');
    
    if (stats.diferencia_decimal >= 0) {
        difCard.style.borderLeftColor = 'var(--success-color)';
        difElement.style.color = 'var(--success-color)';
    } else {
        difCard.style.borderLeftColor = 'var(--danger-color)';
        difElement.style.color = 'var(--danger-color)';
    }
    
    // Actualizar barra de progreso
    const porcentaje = Math.min(stats.porcentaje_completado, 100);
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = `${porcentaje}%`;
    
    if (porcentaje >= 100) {
        progressBar.style.backgroundColor = 'var(--success-color)';
    } else if (porcentaje >= 80) {
        progressBar.style.backgroundColor = 'var(--warning-color)';
    } else {
        progressBar.style.backgroundColor = 'var(--primary-color)';
    }
    
    // Actualizar leyenda con información de feriados
    const leyenda = document.getElementById('leyendaObjetivo');
    if (leyenda) {
        if (stats.feriados && stats.feriados.cantidad > 0) {
            const feriadosInfo = stats.feriados.fechas.map(f => f.nombre).join(', ');
            leyenda.innerHTML = `
                💡 <strong>Objetivo:</strong> ${horasReqTexto} semanales (Lunes a Domingo)
                <br>
                🎉 <strong>Feriados esta semana:</strong> ${stats.feriados.cantidad} — ${feriadosInfo}
                <br>
                📉 <strong>Ajuste:</strong> -${stats.feriados.ajuste_horas}h por feriados
            `;
        } else {
            leyenda.innerHTML = `💡 <strong>Objetivo:</strong> 43 horas semanales (Lunes a Domingo)`;
        }
    }

    renderizarProyeccionSalida();
}

/**
 * Carga marcas agrupadas por día para la semana de referencia actual
 */
async function cargarMarcasAgrupadas() {
    try {
        toggleLoading(true);

        // Calcular lunes y domingo de la semana de referencia
        const fechaRef = state.fechaReferenciaEstadisticas
            ? new Date(state.fechaReferenciaEstadisticas + 'T12:00:00')
            : new Date();
        const dia = fechaRef.getDay();
        const diffLunes = dia === 0 ? -6 : 1 - dia;
        const lunes = new Date(fechaRef);
        lunes.setDate(fechaRef.getDate() + diffLunes);
        const domingo = new Date(lunes);
        domingo.setDate(lunes.getDate() + 6);
        const desde = lunes.toISOString().split('T')[0];
        const hasta = domingo.toISOString().split('T')[0];

        // Actualizar rango en el encabezado del historial
        const rangoEl = document.getElementById('rangoSemanaHistorial');
        if (rangoEl) rangoEl.textContent = `${formatearFechaSemana(desde)} — ${formatearFechaSemana(hasta)}`;

        const response = await fetch(`${API_BASE}/agrupadas?fecha_desde=${desde}&fecha_hasta=${hasta}`);

        if (!response.ok) {
            throw new Error('Error al cargar marcas');
        }

        state.marcasAgrupadas = await response.json();
        renderizarMarcasAgrupadas();

    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta('Error al cargar las marcas', 'error');
    } finally {
        toggleLoading(false);
    }
}

/**
 * Renderiza la tabla de marcas agrupadas por día
 */
function renderizarMarcasAgrupadas() {
    const tbody = document.getElementById('listaMarcas');
    
    if (state.marcasAgrupadas.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <p>No hay marcas registradas</p>
                    <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                        Comienza registrando tu primera entrada o salida
                    </p>
                </td>
            </tr>
        `;
        renderizarProyeccionSalida();
        return;
    }
    
    tbody.innerHTML = '';
    
    state.marcasAgrupadas.forEach(dia => {
        // Fila de fecha (header del día)
        const fechaRow = document.createElement('tr');
        fechaRow.style.backgroundColor = '#f1f5f9';
        fechaRow.innerHTML = `
            <td colspan="6" style="font-weight: 600; padding: 0.875rem;">
                📅 ${formatearFecha(dia.fecha)} 
                <span style="color: #64748b; font-weight: 400; margin-left: 1rem;">
                    Total: ${dia.total_horas || '00:00'}
                </span>
            </td>
        `;
        tbody.appendChild(fechaRow);
        
        // Filas de marcas del día
        dia.marcas.forEach(marca => {
            const row = document.createElement('tr');

            // Determinar icono y badge según tipo
            let badgeClass, icono, textoTipo, contenidoHora;
            if (marca.tipo === 'ENTRADA') {
                badgeClass = 'badge-entrada';
                icono = '🟢';
                textoTipo = 'ENTRADA';
                contenidoHora = formatearHora(marca.hora);
            } else if (marca.tipo === 'SALIDA') {
                badgeClass = 'badge-salida';
                icono = '🔴';
                textoTipo = 'SALIDA';
                contenidoHora = formatearHora(marca.hora);
            } else if (marca.tipo === 'ART15') {
                badgeClass = 'badge-art15';
                icono = '⏰';
                textoTipo = 'ART. 15';
                const horasDecimal = marca.horas_art15 / 60;
                contenidoHora = `${formatearHora(marca.hora)} (${horasDecimal}h)`;
            }

            row.innerHTML = `
                <td></td>
                <td>
                    <span class="badge ${badgeClass}">
                        ${icono} ${textoTipo}
                    </span>
                </td>
                <td style="font-weight: 500;">${contenidoHora}</td>
                <td style="color: #64748b; font-size: 0.8125rem;">
                    ${marca.observacion || '-'}
                </td>
                <td style="font-size: 0.75rem; color: #94a3b8;">
                    ${formatearDateTime(marca.created_at)}
                </td>
                <td>
                    <button
                        onclick="editarMarca(${marca.id})"
                        class="btn btn-primary btn-small"
                        title="Editar">
                        ✏️
                    </button>
                    <button
                        onclick="eliminarMarca(${marca.id})"
                        class="btn btn-danger btn-small"
                        title="Eliminar"
                        style="margin-left: 0.5rem;">
                        🗑️
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    });

    renderizarProyeccionSalida();
}

/**
 * Maneja el envío del formulario (crear o actualizar marca)
 */
async function handleSubmitMarca(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const tipo = formData.get('tipo');
    
    const marca = {
        fecha: formData.get('fecha'),
        tipo: tipo,
        observacion: formData.get('observacion') || null
    };
    
    // Validar y agregar hora (siempre requerida)
    const hora = formData.get('hora');
    if (!hora) {
        mostrarAlerta('Debe ingresar la hora', 'error');
        return;
    }
    marca.hora = hora + ':00';  // Agregar segundos
    
    // Agregar horas Art.15 si es del tipo ART15
    if (tipo === 'ART15') {
        const horasArt15 = formData.get('horasArt15');
        if (!horasArt15) {
            mostrarAlerta('Debe seleccionar las horas a compensar', 'error');
            return;
        }
        marca.horas_art15 = parseFloat(horasArt15);
    } else {
        marca.horas_art15 = null;
    }
    
    try {
        let response;
        
        if (state.editandoId) {
            // Actualizar marca existente
            response = await fetch(`${API_BASE}/${state.editandoId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(marca)
            });
        } else {
            // Crear nueva marca
            response = await fetch(API_BASE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(marca)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar la marca');
        }
        
        const mensaje = state.editandoId 
            ? '✅ Marca actualizada correctamente' 
            : '✅ Marca registrada correctamente';
        
        mostrarAlerta(mensaje, 'success');
        form.reset();
        document.getElementById('fecha').valueAsDate = new Date();
        toggleCamposSegunTipo(); // Resetear campos
        cancelarEdicion();
        cargarMarcasAgrupadas();
        cargarEstadisticasSemana(); // Recargar estadísticas
        
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta(error.message, 'error');
    }
}

/**
 * Carga una marca para edición
 */
async function editarMarca(id) {
    try {
        const response = await fetch(`${API_BASE}/${id}`);
        
        if (!response.ok) {
            throw new Error('Error al cargar la marca');
        }
        
        const marca = await response.json();
        
        // Llenar el formulario
        document.getElementById('fecha').value = marca.fecha;
        document.getElementById('tipo').value = marca.tipo;
        
        // Configurar campos según el tipo
        if (marca.tipo === 'ART15') {
            // Es un Art.15
            const horasDecimal = marca.horas_art15 / 60;
            document.getElementById('horasArt15').value = horasDecimal;
            document.getElementById('hora').value = '';
        } else {
            // Es ENTRADA o SALIDA
            document.getElementById('hora').value = marca.hora.substring(0, 5); // HH:MM
            document.getElementById('horasArt15').value = '';
        }
        
        document.getElementById('observacion').value = marca.observacion || '';
        
        // Actualizar visibilidad de campos
        toggleCamposSegunTipo();
        
        // Cambiar estado a edición
        state.editandoId = id;
        document.getElementById('tituloFormulario').textContent = '✏️ Editar Marca';
        document.getElementById('btnSubmit').textContent = '💾 Actualizar Marca';
        document.getElementById('btnCancelarEdicion').style.display = 'inline-flex';
        
        // Scroll al formulario
        document.getElementById('formMarca').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta('Error al cargar la marca para editar', 'error');
    }
}

/**
 * Cancela la edición y resetea el formulario
 */
function cancelarEdicion() {
    state.editandoId = null;
    document.getElementById('tituloFormulario').textContent = '➕ Registrar Nueva Marca';
    document.getElementById('btnSubmit').textContent = '✅ Registrar Marca';
    document.getElementById('btnCancelarEdicion').style.display = 'none';
    document.getElementById('formMarca').reset();
    document.getElementById('fecha').valueAsDate = new Date();
    
    // Resetear a ENTRADA por defecto
    document.getElementById('tipo').value = 'ENTRADA';
    toggleCamposSegunTipo();
}

/**
 * Elimina una marca (con confirmación)
 */
async function eliminarMarca(id) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta marca?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Error al eliminar la marca');
        }
        
        mostrarAlerta('🗑️ Marca eliminada correctamente', 'success');
        cargarMarcasAgrupadas();
        cargarEstadisticasSemana(); // Recargar estadísticas
        
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta('Error al eliminar la marca', 'error');
    }
}

/**
 * Formatea una fecha para mostrar (ej: "Lunes 10 de Abril, 2026")
 */
function formatearFecha(fechaStr) {
    const fecha = new Date(fechaStr + 'T00:00:00');
    const opciones = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    return fecha.toLocaleDateString('es-UY', opciones);
}

/**
 * Formatea una fecha corta para rango de semana (ej: "Lun 6 Abr")
 */
function formatearFechaSemana(fechaStr) {
    const fecha = new Date(fechaStr + 'T00:00:00');
    const opciones = { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
    };
    return fecha.toLocaleDateString('es-UY', opciones);
}

/**
 * Formatea una hora (ej: "08:30")
 */
function formatearHora(horaStr) {
    return horaStr.substring(0, 5); // HH:MM
}

/**
 * Formatea fecha y hora completa
 */
function formatearDateTime(dateTimeStr) {
    const dt = new Date(dateTimeStr);
    return dt.toLocaleDateString('es-UY', { 
        day: '2-digit', 
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Cambia la semana de referencia para las estadísticas
 * @param {number} offset - Número de semanas a mover (-1 = anterior, +1 = siguiente)
 */
function cambiarSemana(offset) {
    let fechaRef = state.fechaReferenciaEstadisticas
        ? new Date(state.fechaReferenciaEstadisticas + 'T00:00:00')
        : new Date();
    fechaRef.setDate(fechaRef.getDate() + (offset * 7));
    state.fechaReferenciaEstadisticas = fechaRef.toISOString().split('T')[0];
    cargarEstadisticasSemana();
    cargarMarcasAgrupadas();
}

/**
 * Vuelve a la semana actual
 */
function irSemanaActual() {
    state.fechaReferenciaEstadisticas = null;
    document.getElementById('selectorFechaSemana').value = '';
    cargarEstadisticasSemana();
    cargarMarcasAgrupadas();
}

/**
 * Ir a una semana específica desde el selector de fecha
 */
function irSemanaEspecifica() {
    const fecha = document.getElementById('selectorFechaSemana').value;
    if (fecha) {
        state.fechaReferenciaEstadisticas = fecha;
        cargarEstadisticasSemana();
        cargarMarcasAgrupadas();
    }
}

/**
 * Muestra/oculta campos según el tipo de marca seleccionado
 */
function toggleCamposSegunTipo() {
    const tipo = document.getElementById('tipo').value;
    const grupoHora = document.getElementById('grupoHora');
    const grupoHorasArt15 = document.getElementById('grupoHorasArt15');
    const campoHora = document.getElementById('hora');
    const campoHorasArt15 = document.getElementById('horasArt15');
    
    if (tipo === 'ART15') {
        // Art.15: Mostrar AMBOS campos (hora + horas a compensar)
        grupoHora.style.display = 'block';
        grupoHorasArt15.style.display = 'block';
        campoHora.required = true;
        campoHorasArt15.required = true;
        
        // Cambiar label del campo hora
        grupoHora.querySelector('label').textContent = 'Hora del artículo';
    } else {
        // Entrada/Salida: Solo mostrar hora
        grupoHora.style.display = 'block';
        grupoHorasArt15.style.display = 'none';
        campoHora.required = true;
        campoHorasArt15.required = false;
        
        // Restaurar label original
        grupoHora.querySelector('label').textContent = 'Hora';
    }
}

/**
 * Convierte minutos desde medianoche a formato HH:MM
 */
function minToHHMM(totalMinutos) {
    const h = Math.floor(totalMinutos / 60);
    const m = Math.floor(totalMinutos % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/**
 * Calcula la proyección de salida para hoy basándose en la última ENTRADA
 * abierta y las estadísticas de la semana actual.
 *
 * La jornada estándar se calcula como horas_requeridas / días_laborables_semana
 * para respetar automáticamente la reducción por feriados.
 * Los días restantes para cubrir la semana también descuentan feriados futuros.
 */
function calcularProyeccionSalida() {
    if (!state.estadisticasSemana || !state.marcasAgrupadas.length) return null;

    const hoy = new Date().toISOString().split('T')[0];
    const diaHoy = state.marcasAgrupadas.find(d => d.fecha === hoy);
    if (!diaHoy) return null;

    // Última ENTRADA sin SALIDA posterior
    let ultimaEntrada = null;
    for (const marca of diaHoy.marcas) {
        if (marca.tipo === 'ENTRADA') ultimaEntrada = marca;
        else if (marca.tipo === 'SALIDA') ultimaEntrada = null;
    }
    if (!ultimaEntrada) return null;

    const [h, m] = ultimaEntrada.hora.split(':').map(Number);
    const entradaMin = h * 60 + m;

    const stats = state.estadisticasSemana;

    // Jornada diaria = horas requeridas / días laborables efectivos de la semana
    const diasLaboralesSemana = Math.max(1, 5 - (stats.feriados?.cantidad || 0));
    const jornadaDiariaMin = Math.round((stats.horas_requeridas * 60) / diasLaboralesSemana);
    const salidaEstandarMin = entradaMin + jornadaDiariaMin;

    // Horas faltantes para cerrar la semana (sesión abierta de hoy no contabilizada)
    const trabajadasMin = Math.round(stats.horas_trabajadas_decimal * 60);
    const requeridosMin = Math.round(stats.horas_requeridas * 60);
    const faltantesMin = requeridosMin - trabajadasMin;

    // Días laborables restantes (hoy inclusive) descontando feriados desde hoy
    const hoyDate = new Date(hoy + 'T12:00:00');
    const diaSemana = hoyDate.getDay(); // 0=Dom … 5=Vie … 6=Sab
    const diasBaseRestantes = (diaSemana >= 1 && diaSemana <= 5) ? (6 - diaSemana) : 0;
    const feriadosFuturos = (stats.feriados?.fechas || []).filter(f => f.fecha >= hoy).length;
    const diasRestantes = Math.max(1, diasBaseRestantes - feriadosFuturos);

    let salidaSemanalMin = null;
    if (faltantesMin > 0) {
        const horasHoyMin = Math.min(Math.round(faltantesMin / diasRestantes), 600);
        salidaSemanalMin = entradaMin + horasHoyMin;
    }

    return {
        horaEntrada: ultimaEntrada.hora.substring(0, 5),
        jornadaDiariaMin,
        salidaEstandarMin,
        salidaSemanalMin,
        salidaEstandar: minToHHMM(salidaEstandarMin),
        salidaSemanal: salidaSemanalMin !== null ? minToHHMM(salidaSemanalMin) : null,
        faltantesMin,
        diasRestantes,
        semanaCompletada: faltantesMin <= 0
    };
}

/**
 * Muestra u oculta la tarjeta de proyección de salida según si hay una
 * ENTRADA abierta hoy.
 */
function renderizarProyeccionSalida() {
    const card = document.getElementById('cardProyeccion');
    if (!card) return;

    const p = calcularProyeccionSalida();

    if (!p) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';

    const jornadaStr = minToHHMM(p.jornadaDiariaMin);
    const faltantesStr = minToHHMM(Math.abs(p.faltantesMin));

    const saldoHtml = p.semanaCompletada
        ? `✅ <strong>Semana completada.</strong> Superávit: <strong>${faltantesStr}</strong>`
        : `⚠️ Faltan <strong>${faltantesStr}</strong> para la semana — distribuido en ${p.diasRestantes} día${p.diasRestantes !== 1 ? 's' : ''} restante${p.diasRestantes !== 1 ? 's' : ''}`;

    let salidaSemanalHtml;
    if (p.semanaCompletada) {
        salidaSemanalHtml = `<div style="color: var(--success-color); font-size: 1.25rem; font-weight: 700;">¡Listo! 🎉</div>`;
    } else {
        const esMasTarde = p.salidaSemanalMin > p.salidaEstandarMin;
        const color = esMasTarde ? 'var(--danger-color)' : 'var(--success-color)';
        const flecha = esMasTarde ? '▲' : '▼';
        salidaSemanalHtml = `<div style="color: ${color}; font-size: 1.25rem; font-weight: 700;">${p.salidaSemanal} <span style="font-size: 0.7rem;">${flecha}</span></div>`;
    }

    document.getElementById('contenidoProyeccion').innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; text-align: center; margin-bottom: 0.5rem;">
            <div>
                <div style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em;">Entrada</div>
                <div style="font-size: 1.25rem; font-weight: 700;">${p.horaEntrada}</div>
            </div>
            <div style="border-left: 1px solid #a7f3d0; border-right: 1px solid #a7f3d0; padding: 0 0.25rem;">
                <div style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em;">⏱ Estándar</div>
                <div style="font-size: 1.25rem; font-weight: 700;">${p.salidaEstandar}</div>
                <div style="font-size: 0.65rem; color: var(--text-muted);">${jornadaStr}/día</div>
            </div>
            <div>
                <div style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em;">📊 Semana</div>
                ${salidaSemanalHtml}
                <div style="font-size: 0.65rem; color: var(--text-muted);">${p.diasRestantes} día${p.diasRestantes !== 1 ? 's' : ''} rest.</div>
            </div>
        </div>
        <div style="font-size: 0.75rem; color: #475569; padding: 0.35rem 0.6rem; background: white; border-radius: 0.25rem;">
            ${saldoHtml}
        </div>
    `;
}

// Exponer funciones globalmente para los botones inline
window.editarMarca = editarMarca;
window.eliminarMarca = eliminarMarca;
window.cambiarSemana = cambiarSemana;
window.irSemanaActual = irSemanaActual;
window.irSemanaEspecifica = irSemanaEspecifica;
window.toggleCamposSegunTipo = toggleCamposSegunTipo;
