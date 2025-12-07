document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-editar-itinerario');
    
    // Referencias al modal
    const modalEl = document.getElementById('confirmEditModal');
    const btnConfirmar = document.getElementById('btnConfirmarGuardado');
    let confirmModal = null;
    if (modalEl) {
        confirmModal = new bootstrap.Modal(modalEl);
    }

    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault(); // Siempre prevenimos el envío default

            // Normalizamos el valor para evitar diferencias de mayúsculas/espacios
            const status = (form.dataset.itineraryStatus || '').toString().toLowerCase().trim(); // Leemos lo que pusimos en el HTML

            // LÓGICA DE INTERCEPCIÓN
            // Solo mostramos el modal si está PUBLICADO
            if (status === 'published') {
                if (confirmModal) {
                    confirmModal.show();
                } else {
                    // Fallback si falla el modal
                    if(confirm("Al editar, este itinerario pasará a Borrador. ¿Continuar?")){
                         enviarDatosItinerario(form);
                    }
                }
            } else {
                // Si es borrador o nuevo, guardamos directo
                await enviarDatosItinerario(form);
            }
        });
    }

    // Listener del botón "Sí, guardar" dentro del Modal
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', async () => {
            if (confirmModal) confirmModal.hide();
            await enviarDatosItinerario(form);
        });
    }
});

/**
 * Función que realiza el POST real al servidor.
 * (Refactorización de tu antigua función saveItinerary)
 */
async function enviarDatosItinerario(form) {
    const itineraryId = form.dataset.itineraryId;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Feedback visual
    const textoOriginal = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

    // 1. URL
    let url = '/itineraries/create/';
    if (itineraryId) {
        url = `/itineraries/${itineraryId}/edit/`;
    }

    // 2. FORMDATA
    const formData = new FormData(form);

    // 3. FETCH
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al guardar');
        }

        const data = await response.json();

        if (data.success && data.redirect_url) {
            // REEMPLAZO: En lugar de redirigir de golpe, mostramos éxito
            Swal.fire({
                title: '¡Excelente!',
                text: data.message || 'Itinerario guardado correctamente',
                icon: 'success',
                timer: 1500, // Se cierra solo en 1.5 segundos
                showConfirmButton: false
            }).then(() => {
                // Redirigir cuando se cierre la alerta
                window.location.href = data.redirect_url;
            });
        } else {
            // REEMPLAZO DE ALERT ERROR
            Swal.fire({
                title: 'Error',
                text: 'No se pudo guardar el itinerario.',
                icon: 'error'
            });
        }

    } catch (error) {
        console.error('Error:', error);
        alert(`Hubo un error: ${error.message}`);
    } finally {
        // Restaurar botón
        submitBtn.disabled = false;
        submitBtn.innerHTML = textoOriginal;
    }
}

// Función auxiliar para obtener la cookie CSRF (Necesaria para Django POST/PUT/PATCH/DELETE)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Registro seguro de listeners y función de validación de fechas.
// Evitamos errores si los elementos no existen (por ejemplo en otras páginas).
document.addEventListener('DOMContentLoaded', () => {
    const fechaInicioInput = document.getElementById('fecha-inicio');
    const fechaTerminoInput = document.getElementById('fecha-termino');

    if (fechaInicioInput) fechaInicioInput.addEventListener('change', validarFechas);
    if (fechaTerminoInput) fechaTerminoInput.addEventListener('change', validarFechas);

    // Ejecutar validación inicial para ajustar min/max si ya hay valores
    validarFechas();
});

function validarFechas() {

    const MAX_DIAS = 3; // Máximo de días permitidos entre inicio y término (Regla de Negocio)
    const fechaInicioInput = document.getElementById('fecha-inicio');
    const fechaTerminoInput = document.getElementById('fecha-termino');

    if (!fechaInicioInput || !fechaTerminoInput) return true; // Si no existen los campos, la validación pasa

    const fechaInicio = fechaInicioInput.value;
    const fechaTermino = fechaTerminoInput.value;

    // Si la fecha de inicio ya fue seleccionada se habilita la fecha de término
    if (fechaInicio) {
        fechaTerminoInput.disabled = false;
        fechaTerminoInput.min = fechaInicio; // Establece la fecha mínima permitida

        // Establece la fecha máxima permitida según la regla de negocio
        const fechaFinal = new Date(fechaInicio);
        fechaFinal.setDate(fechaFinal.getDate() + MAX_DIAS);
        const year = fechaFinal.getFullYear();
        const month = String(fechaFinal.getMonth() + 1).padStart(2, '0');
        const day = String(fechaFinal.getDate()).padStart(2, '0');
        fechaTerminoInput.max = `${year}-${month}-${day}`;
        
    } else {
        fechaTerminoInput.disabled = true;
        fechaTerminoInput.value = ''; // Limpia el valor si se deshabilita
    }

    fechaTerminoInput.classList.remove('is-invalid');
    fechaTerminoInput.setCustomValidity('');

    if (fechaInicio && fechaTermino) {
        const inicio = new Date(fechaInicio);
        const termino = new Date(fechaTermino);

        if (termino < inicio) {
            fechaTerminoInput.classList.add('is-invalid');
            fechaTerminoInput.setCustomValidity('La fecha de término no puede ser anterior a la fecha de inicio.');
            return false;
        }
    }

    return true;
}
