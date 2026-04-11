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
    editandoId: null
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
 * Carga marcas agrupadas por día desde la API
 */
async function cargarMarcasAgrupadas() {
    try {
        toggleLoading(true);
        const response = await fetch(`${API_BASE}/agrupadas`);
        
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
            row.innerHTML = `
                <td></td>
                <td>
                    <span class="badge badge-${marca.tipo.toLowerCase()}">
                        ${marca.tipo === 'ENTRADA' ? '🟢' : '🔴'} ${marca.tipo}
                    </span>
                </td>
                <td style="font-weight: 500;">${formatearHora(marca.hora)}</td>
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
}

/**
 * Maneja el envío del formulario (crear o actualizar marca)
 */
async function handleSubmitMarca(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    const marca = {
        fecha: formData.get('fecha'),
        tipo: formData.get('tipo'),
        hora: formData.get('hora') + ':00', // Agregar segundos
        observacion: formData.get('observacion') || null
    };
    
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
        cancelarEdicion();
        cargarMarcasAgrupadas();
        
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
        document.getElementById('hora').value = marca.hora.substring(0, 5); // HH:MM
        document.getElementById('observacion').value = marca.observacion || '';
        
        // Cambiar estado a edición
        state.editandoId = id;
        document.getElementById('tituloFormulario').textContent = '✏️ Editar Marca';
        document.getElementById('btnSubmit').textContent = 'Actualizar Marca';
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
    document.getElementById('btnSubmit').textContent = 'Registrar Marca';
    document.getElementById('btnCancelarEdicion').style.display = 'none';
    document.getElementById('formMarca').reset();
    document.getElementById('fecha').valueAsDate = new Date();
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

// Exponer funciones globalmente para los botones inline
window.editarMarca = editarMarca;
window.eliminarMarca = eliminarMarca;
