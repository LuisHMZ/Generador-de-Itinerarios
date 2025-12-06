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

// --- VARIABLES GLOBALES PARA EL MAPA ---
let map = null;
let markers = [];
let directionsService = null;
let directionsRenderer = null;

// ===================================================
// FUNCIONES GLOBALES DEL MAPA
// ===================================================

/**
 * 1. Callback de Google: Inicializa el mapa
 */
function initMap() {
    try {
        // Usa el ID del mapa de tu HTML: "map-preview"
        map = new google.maps.Map(document.getElementById('map-preview'), {
            center: { lat: 19.432608, lng: -99.133209 }, // Centro en CDMX
            zoom: 10,
            // (puedes añadir más opciones de estilo aquí)
        });
        
        // Inicializa los servicios de ruta
        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({
            map: map,
            suppressMarkers: true // Oculta los marcadores A, B, C de Google
        });
        
        console.log("-> Mapa y servicios (incluyendo Directions) listos.");

    } catch (e) {
        console.error("Error al inicializar el mapa: ", e);
    }
}


/**
 * 2. Dibuja los marcadores para una lista de lugares
 * (Modificado para aceptar la lista como parámetro)
 */
function actualizarMarcadores(lugaresDelDia) {
    if (!map) {
        console.warn("actualizarMarcadores: El mapa no está listo.");
        return; 
    }
    
    // Limpiar marcadores antiguos
    markers.forEach(marker => marker.setMap(null));
    markers = [];

    if (!lugaresDelDia || lugaresDelDia.length === 0) {
        return; // No hay marcadores que dibujar
    }

    const bounds = new google.maps.LatLngBounds(); // Para centrar el mapa

    for (const [index, lugar] of lugaresDelDia.entries()) {
        
        if (lugar.lat && lugar.lng) {
            const position = {
                lat: parseFloat(lugar.lat),
                lng: parseFloat(lugar.lng)
            };

            const marker = new google.maps.Marker({
                position: position,
                map: map,
                label: {
                    text: (index + 1).toString(),
                    color: "white",
                    fontWeight: "bold"
                },
                title: lugar.nombre
            });
            markers.push(marker);
            bounds.extend(position); // Extiende los límites para el zoom
        }
    }

    // Centra y ajusta el zoom del mapa a los marcadores
    if (lugaresDelDia.length > 0) {
        map.fitBounds(bounds);
    }
}


/**
 * 3. Dibuja la ruta en el mapa
 * (Modificado para aceptar la lista como parámetro)
 */
async function dibujarRutaActual(lugaresDelDia) {
    if (!directionsService || !directionsRenderer) {
        console.warn("dibujarRutaActual: El servicio de rutas no está listo.");
        return;
    }
    
    // Limpiar ruta anterior
    directionsRenderer.setDirections({ routes: [] });

    // Filtrar lugares que SÍ tienen coordenadas
    const paradasConCoordenadas = lugaresDelDia.filter(lugar => {
        return lugar.lat && lugar.lng && 
               lugar.lat.toString().trim() !== '' && 
               lugar.lng.toString().trim() !== '';
    });

    if (paradasConCoordenadas.length < 2) {
        return; // No hay ruta que dibujar
    }

    // Preparar la solicitud
    const origin = paradasConCoordenadas[0];
    const destination = paradasConCoordenadas[paradasConCoordenadas.length - 1];
    const waypoints = paradasConCoordenadas.slice(1, -1).map(lugar => ({
        location: new google.maps.LatLng(parseFloat(lugar.lat), parseFloat(lugar.lng)),
        stopover: true
    }));

    const request = {
        origin: new google.maps.LatLng(parseFloat(origin.lat), parseFloat(origin.lng)),
        destination: new google.maps.LatLng(parseFloat(destination.lat), parseFloat(destination.lng)),
        waypoints: waypoints,
        travelMode: 'WALKING'
    };

    // Llamar a la API
    try {
        const response = await directionsService.route(request);
        if (response.status === 'OK') {
            directionsRenderer.setDirections(response); // Dibuja la ruta
        } else {
            console.warn("No se pudo calcular la ruta: " + response.status);
        }
    } catch (error) {
        console.error("Error al llamar a Directions API:", error);
    }
}

/**
 * Añade un event listener al botón de publicar itinerario (ID = 'boton_publicar_itinerario')
 * Cuando se hace clic, envía una solicitud POST a la API para publicar el itinerario
 * Endpoint: /api/itineraries/<itinerary_id>/publish/
 * La información debe pasar primero por un serializador en el backend para validación y procesamiento.
 * Luego, el backend debe actualizar el estado del itinerario a "publicado" y devolver una respuesta adecuada.
 */
document.addEventListener('DOMContentLoaded', () => {

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

	// Recoger los datos de lat y long de los lugares del itinerario
	const lugaresDelDia = [];
	const lugarCards = document.querySelectorAll('.card-lugar-itinerario');
	lugarCards.forEach(card => {
		const data = card.dataset;
		lugaresDelDia.push({
			nombre: data.nombre || '',
			lat: data.lat || '',
			lng: data.lng || ''
		});
	});

	// Actualizar marcadores y ruta en el mapa
	actualizarMarcadores(lugaresDelDia);
	dibujarRutaActual(lugaresDelDia);

});


