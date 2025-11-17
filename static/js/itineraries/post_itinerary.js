document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-editar-itinerario');

    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault(); // Previene el envío HTML tradicional

            // --- Realiza validaciones aquí (como la de fechas) ---
            const fechasValidas = validarFechas(); // Asume que tienes esta función del script anterior
            if (!fechasValidas) {
                alert('Por favor, corrige las fechas antes de continuar.');
                return; // Detiene si hay errores
            }


            // --- Recopila los datos del formulario ---
            const formData = new FormData(form);

            /**
             * Validación adicional de fechas por si el usuario manipula el HTML
             * Se asegura que la fecha de término no exceda el máximo permitido 
             * o que no sea anterior a la fecha de inicio.
             */
            const fechaInicio = formData.get('fecha-inicio');
            const fechaTermino = formData.get('fecha-termino');
            if (fechaInicio && fechaTermino) {
                const inicio = new Date(fechaInicio);
                const termino = new Date(fechaTermino);
                const MAX_DIAS = 3;
                const fechaMaxima = new Date(inicio);
                fechaMaxima.setDate(fechaMaxima.getDate() + MAX_DIAS);

                if (termino < inicio || termino > fechaMaxima) {
                    alert(`La fecha de término debe estar entre ${fechaInicio} y ${fechaMaxima.toISOString().split('T')[0]}.`);
                    return; // Detiene si las fechas no son válidas
                }
            }

            // Opcional: Puedes ver los datos que se enviarán en la consola
            // for (let [key, value] of formData.entries()) {
            //     console.log(`${key}: ${value}`);
            // }

            // --- Envía los datos al backend ---
            try {
                // Muestra algún indicador de carga (opcional)
                const botonSiguiente = form.querySelector('.boton-siguiente');
                botonSiguiente.disabled = true;
                botonSiguiente.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';

                // Determina si es crear (sin ID) o editar (con ID)
                const itineraryId = formData.get('itinerary_id'); // Obtiene el ID del campo oculto
                // Usar endpoints absolutos de la API para evitar rutas relativas dobles
                // Asume que el ViewSet está registrado en /api/itineraries/
                const url = itineraryId
                    ? `/api/itineraries/${itineraryId}/` // URL para EDITAR (PUT o PATCH)
                    : '/api/itineraries/';               // URL para CREAR (POST)
                const method = 'POST'; // Django maneja mejor los archivos con POST, incluso para actualizaciones
                
                const response = await fetch(url, {
                    method: method,
                    body: formData,
                    // Headers necesarios para Django (CSRF token, etc.) - El backend te dirá qué necesita
                     headers: {
                         'X-CSRFToken': getCookie('csrftoken'), // Función para obtener la cookie CSRF
                         // 'Content-Type': 'multipart/form-data' // FormData lo pone automáticamente
                    },
                });

                // --- Maneja la respuesta del backend ---
                botonSiguiente.disabled = false;
                botonSiguiente.textContent = 'Siguiente'; // Restaura el texto del botón

                if (response.ok) {
                    const result = await response.json(); // Lee la respuesta JSON del backend
                    console.log('Respuesta del servidor:', result);
                    alert('¡Itinerario guardado con éxito!');
                    // Redirige a la siguiente página (ej. añadir paradas o ver itinerario)
                    // El backend podría devolver la URL a la que redirigir en 'result.redirect_url'
                    // Redirige con ruta absoluta para evitar concatenaciones relativas
                    window.location.href = `/itineraries/${result.id}/add-stops/`;
                } else {
                    // Intenta leer el error del backend si lo envía en JSON
                    let errorData;
                    try {
                        errorData = await response.json();
                    } catch (e) {
                        errorData = { detail: 'Ocurrió un error al guardar. Inténtalo de nuevo.' };
                    }
                    console.error('Error del servidor:', response.status, errorData);
                    alert(`Error al guardar: ${errorData.detail || response.statusText}`);
                }

            } catch (error) {
                console.error('Error al enviar el formulario:', error);
                alert('Ocurrió un error de red al intentar guardar. Revisa tu conexión.');
                // Restaura el botón en caso de error de red
                const botonSiguiente = form.querySelector('.boton-siguiente');
                botonSiguiente.disabled = false;
                botonSiguiente.textContent = 'Siguiente';
            }
        });
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

    const fechaInicioInput = document.getElementById('fecha-inicio');
    const fechaTerminoInput = document.getElementById('fecha-termino');
    
    fechaInicioInput.addEventListener('change', validarFechas);
    
    function validarFechas() {

        const MAX_DIAS = 3; // Máximo de días permitidos entre inicio y término (Regla de Negocio)
        
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

        /**
         * Por mera lógica, esta sección del código nunca haría efecto
         * puesto que el código anterior ya establece min y max adecuados.
         * Sin embargo, se deja para validación adicional por si el usuario manipula el HTML.
         */

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

}); 