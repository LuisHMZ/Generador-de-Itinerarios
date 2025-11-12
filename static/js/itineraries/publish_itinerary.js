// publish_itinerary.js
/**
 * JavaScript para manejar la publicación del itinerario
 * después de la previsualización en preview_itinerary.html
 */

// Función auxiliar para obtener la cookie CSRF (compatible con Django)
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

/**
 * Añade un event listener al botón de publicar itinerario (ID = 'boton_publicar_itinerario')
 * Cuando se hace clic, envía una solicitud POST a la API para publicar el itinerario
 * Endpoint: /api/itineraries/<itinerary_id>/publish/
 * La información debe pasar primero por un serializador en el backend para validación y procesamiento.
 * Luego, el backend debe actualizar el estado del itinerario a "publicado" y devolver una respuesta adecuada.
 */



document.addEventListener('DOMContentLoaded', () => {
	// Buscamos el botón (por si se carga el script antes del DOM)
	const boton = document.getElementById('boton_publicar_itinerario');
	if (!boton) return; // No hay botón en esta página

	boton.addEventListener('click', async (e) => {
		e.preventDefault();

		// Confirmación opcional antes de publicar
		if (!confirm('¿Quieres publicar este itinerario? Esta acción hará que sea visible públicamente.')) {
			return;
		}

		// Obtener el ID del itinerario desde el body (consistente con otros scripts)
		const ITINERARY_ID = document.body.dataset.itineraryId || null;
		console.log(`ITINERARY_ID: ${ITINERARY_ID}`);
		if (!ITINERARY_ID) {
			alert('No se pudo identificar el itinerario a publicar.');
			return;
		}

		const csrftoken = getCookie('csrftoken');

		// Estado visual: deshabilitar botón y mostrar spinner
		const previousHTML = boton.innerHTML;
		boton.disabled = true;
		boton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Publicando...';

		try {
			const response = await fetch(`/api/itineraries/${ITINERARY_ID}/publish/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken
				},
				body: JSON.stringify({}) // No hace falta enviar datos, pero dejamos un JSON vacío por claridad
			});

			boton.disabled = false;
			boton.innerHTML = previousHTML; // Restaurar texto

			if (response.ok) {
				// Intenta leer la respuesta para mostrar detalles
				let data = null;
				try { data = await response.json(); } catch (e) { /* no JSON */ }

				alert(data && data.detail ? data.detail : 'Itinerario publicado con éxito.');

				// Redirigir a la vista pública/preview del itinerario
				// Suposición razonable: la ruta pública es /itineraries/<id>/
				// Por ahora redirigimos al home
				window.location.href = '/home/';
			} else {
				let errorData;
				try { errorData = await response.json(); } catch (e) { errorData = { detail: response.statusText }; }
				console.error('Error al publicar itinerario:', response.status, errorData);
				alert(`No se pudo publicar: ${errorData.detail || response.statusText}`);
			}

		} catch (error) {
			console.error('Error de red al publicar itinerario:', error);
			boton.disabled = false;
			boton.innerHTML = previousHTML;
			alert('Ocurrió un error de red al intentar publicar. Revisa tu conexión e inténtalo de nuevo.');
		}
	});

	/**
	 * Manejo del modal de detalles del lugar
	 * Similar al modal en add_stops.js
	 */

	// 1. Encontrar el cuerpo del modal
    const modalBody = document.getElementById('modalDetallesBody');
	const modalElement = document.getElementById('modalDetallesLugar');
    if (!modalBody || !modalElement) return;

    // 2. INICIALIZAR LA INSTANCIA DEL MODAL DE BOOTSTRAP 5
    // Lo creamos una vez y luego solo lo mostramos/ocultamos
    const bootstrapModal = new bootstrap.Modal(modalElement); // <-- AÑADIDO

    // 3. CAMBIAR EL TRIGGER: Buscar los botones, no las tarjetas
    const lugarBtns = document.querySelectorAll('.btn.btn-sm.btn-outline-info.btn-ver-stop'); // <-- CAMBIADO

    // 4. Añadir un listener a CADA tarjeta
    lugarBtns.forEach(btn => {
        btn.addEventListener('click', () => {

			// 5. ENCONTRAR LA TARJETA PADRE
            // Los datos están en la tarjeta, no en el botón
            const card = btn.closest('.card-lugar-itinerario'); // <-- AÑADIDO
            if (!card) return; // Salir si no se encuentra la tarjeta
            
            // 6. Leer los datos desde los atributos data-*
            const data = card.dataset;
            const nombre = data.nombre;
            const img = data.img;
            const direccion = data.direccion;
            const descripcion = data.descripcion;
            const website = data.website;
            const phone = data.phone;
            const rating = data.rating;

            // 7. Construir el HTML (similar al modal de add_stops)
            const imagenHTML = (img && img !== '/static/img/placeholder.png') 
                ? `<img src="${img}" class="imagen-principal" alt="${nombre}">` : '';

            const websiteHTML = website 
                ? `<div class="contacto-item"><i class="fas fa-globe"></i>
                   <span><a href="${website}" target="_blank">${website}</a></span></div>` : '';
            
            const phoneHTML = phone
                ? `<div class="contacto-item"><i class="fas fa-phone"></i>
                   <span>${phone}</span></div>` : '';

            const content = `
                <div class="detalle-lugar-card">
                    ${imagenHTML}
                    <div class="detalle-lugar-body">
                        <div class="info-basica">
                            <div class="titulo-categoria-container">
                                <h3 class="titulo-lugar">${nombre}</h3>
                            </div>
                            <div class="rating-container">
                                <div class="rating-numero">${rating}</div>
                                <div class="reseñas-count">Rating (API)</div>
                            </div>
                        </div>
                        <div class="direccion-item">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${direccion}</span>
                        </div>
                        ${phoneHTML}
                        ${websiteHTML}
                        <hr>
                        <p class="descripcion-lugar">${descripcion}</p>
                    </div>
                </div>
            `;
            
            // 8. Inyectar el HTML en el modal
            modalBody.innerHTML = content;

			// 9. Mostrar el modal usando la instancia de Bootstrap creada antes
			bootstrapModal.show(); // <-- AÑADIDO: Esta es la solución
        });
    });

});

