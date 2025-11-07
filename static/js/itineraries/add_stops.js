
// Tipos de lugares para buscar (comida, turísticos, etc.)
const TIPOS_LUGARES = [
    'restaurant', 'cafe', 'bar', 'bakery', // Comida y bebida
    'tourist_attraction', 'museum', 'art_gallery', // Turísticos
    'park', 'shopping_mall', 'movie_theater', // Entretenimiento
    'point_of_interest', 'establishment' // Generales
];

// Sistema de categorías principales
const CATEGORIAS_PRINCIPALES = [
    'Museos', 'Galerías de Arte', 'Puntos de Interés', 'Atracciones Turísticas', 
    'Sitios Históricos', 'Iglesias y Templos', 'Teatros', 'Parques de Diversiones',
    'Zoológicos', 'Acuarios', 'Estadios', 'Cines', 'Vida Nocturna', 'Parques y Plazas',
    'Maravillas Naturales', 'Zonas de Acampar', 'Restaurantes', 'Cafeterías', 
    'Bares y Cantinas', 'Panaderías'
];

// Mapeo de tipos de Google Places a categorías principales
const MAPEO_CATEGORIAS = {
    'museum': 'Museos',
    'art_gallery': 'Galerías de Arte',
    'tourist_attraction': 'Atracciones Turísticas',
    'point_of_interest': 'Puntos de Interés',
    'landmark': 'Puntos de Interés',
    'church': 'Iglesias y Templos',
    'hindu_temple': 'Iglesias y Templos',
    'mosque': 'Iglesias y Templos',
    'synagogue': 'Iglesias y Templos',
    'place_of_worship': 'Iglesias y Templos',
    'historic_site': 'Sitios Históricos',
    'amusement_park': 'Parques de Diversiones',
    'aquarium': 'Acuarios',
    'zoo': 'Zoológicos',
    'stadium': 'Estadios',
    'movie_theater': 'Cines',
    'night_club': 'Vida Nocturna',
    'bar': 'Vida Nocturna',
    'casino': 'Vida Nocturna',
    'park': 'Parques y Plazas',
    'natural_feature': 'Maravillas Naturales',
    'campground': 'Zonas de Acampar',
    'restaurant': 'Restaurantes',
    'cafe': 'Cafeterías',
    'bakery': 'Panaderías',
    'shopping_mall': 'Centros Comerciales'
};

/**
 * FUNCIÓN: Determinar Categoría Principal
 * Propósito: Mapea los tipos de Google Places a categorías personalizadas
 * Parámetros: types - Array de tipos del lugar
 * Retorno: String con la categoría principal
 */
function determinarCategoriaPrincipal(types) {
    if (!types || !Array.isArray(types)) return 'Puntos de Interés';

    for (let type of types) {
        if (MAPEO_CATEGORIAS[type]) {
            return MAPEO_CATEGORIAS[type];
        }
    }

    // Si no encuentra coincidencia, buscar en tipos más genéricos
    if (types.includes('park') || types.includes('natural_feature')) {
        return 'Parques y Plazas';
    } else if (types.includes('restaurant') || types.includes('food')) {
        return 'Restaurantes';
    } else if (types.includes('cafe') || types.includes('bakery')) {
        return 'Cafeterías';
    } else if (types.includes('bar') || types.includes('night_club')) {
        return 'Bares y Cantinas';
    } else if (types.includes('store') || types.includes('shopping_mall')) {
        return 'Comercios';
    } else {
        return 'Puntos de Interés';
    }
}

// Exponer la función en el scope global para que otras partes del frontend puedan usarla
try {
    if (typeof window !== 'undefined') {
        window.determinarCategoriaPrincipal = determinarCategoriaPrincipal;
        // Alias para compatibilidad con versiones anteriores que usaban determinarCategoria
        window.determinarCategoria = determinarCategoriaPrincipal;
    }
} catch (e) {
    // En entornos donde window no existe, ignorar silenciosamente
}

// 1. DESCOMENTA Y ASEGÚRATE QUE ESTA FUNCIÓN ESTÉ DISPONIBLE
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
 * FUNCIÓN CENTRALIZADA: Añadir Lugar al Itinerario
 * Propósito: Añade un lugar al 'miItinerarioActual[currentDay]'
 * validando duplicados.
 * Parámetros: placeData (un objeto JS con {id, nombre, categoria, imagen, lat, lng})
 */
function addPlaceToItineraryFromData(placeData) {
    const nuevoLugar = {
        id: parseInt(placeData.id, 10),
        nombre: placeData.nombre,
        categoria: placeData.categoria,
        imagen: placeData.imagen,
        lat: placeData.lat || null,
        lng: placeData.lng || null,
    };

    // Asegura que exista el array del día seleccionado
    if (!miItinerarioActual[currentDay]) {
        miItinerarioActual[currentDay] = [];
    }

    // Validación básica: id y nombre son obligatorios
    if (!nuevoLugar.id || !nuevoLugar.nombre || nuevoLugar.nombre.toString().trim() === '') {
        alert('No se puede añadir un lugar vacío. Asegúrate de que el lugar tenga nombre e ID válidos.');
        return; // No añadir
    }

    // Validación de duplicados
    if (miItinerarioActual[currentDay].some(l => parseInt(l.id, 10) === nuevoLugar.id)) {
        alert('Este lugar ya está en tu itinerario para este día.');
        return; // No añadir
    }

    miItinerarioActual[currentDay].push(nuevoLugar);
    actualizarListaItinerario(); // Refresca la UI
    
    // (Opcional) Notificación de éxito
    // alert(`${nuevoLugar.nombre} ha sido agregado.`);
}

/**
 * 2. Lógica para el mapa
 */
// Variables globales del mapa
let map;
let markers = [];

/**
 * Código del mapa
 */

// Ejemplo seguro y sencillo:
window.initMap = function() {
    const el = document.getElementById('mapa-buscador');
    if (!el) {
        console.warn('Elemento #mapa-buscador no encontrado. No se inicializa el mapa.');
        return;
    }

    const cdmx = { lat: 19.4326, lng: -99.1332 };
    map = new google.maps.Map(el, {
        zoom: 10,
        center: cdmx
    });

    // Evita variables globales implícitas — explícitas en window si necesitas acceso desde otras partes
    window.placesService = new google.maps.places.PlacesService(map);
    window.detailsService = new google.maps.places.PlacesService(map);

    // Actualiza marcadores si ya hay datos cargados
    actualizarMarcadores();
};

// Función para actualizar los marcadores en el mapa
function actualizarMarcadores() {
    // Si el mapa aún no se ha inicializado, no hagas nada
    if (!map) return;

    // a. Limpia los marcadores antiguos
    markers.forEach(marker => marker.setMap(null));
    markers = [];

    // b. Obtén las paradas del día actual
    const lugaresDelDia = miItinerarioActual[currentDay] || [];
    if (lugaresDelDia.length === 0) return; // No hay nada que dibujar

    const bounds = new google.maps.LatLngBounds(); // Para centrar el mapa en los marcadores

    // c. Itera sobre las paradas y crea marcadores
    lugaresDelDia.forEach((lugar, index) => {
        // **ASEGÚRATE** de que 'lugar' tenga 'lat' y 'lng'
        if (lugar.lat && lugar.lng) {
            const position = { 
                lat: parseFloat(lugar.lat), 
                lng: parseFloat(lugar.lng) 
            };
            
            const marker = new google.maps.Marker({
                position: position,
                map: map,
                title: lugar.nombre,
                label: (index + 1).toString() // Muestra el número de orden
            });
            
            markers.push(marker);
            bounds.extend(position); // Expande los límites del mapa para incluir este marcador
        }
    });

    // d. Centra y ajusta el zoom del mapa para mostrar todos los marcadores
    if (markers.length > 0) {
        map.fitBounds(bounds);
    }
    // Evita un zoom excesivo si solo hay un marcador
    if (markers.length === 1) {
        map.setZoom(15); 
    }
}


document.addEventListener('DOMContentLoaded', () => {



    // Referencias a los contenedores
    const recomendacionesContainer = document.getElementById('recomendaciones-aleatorias-container');
    const popularAmigosContainer = document.getElementById('popular-amigos-container');
    const miItinerarioLista = document.getElementById('mi-itinerario-lugares-lista');
    const buscadorLugares = document.getElementById('buscador-lugares-itinerario');
    const dropdownDiaButton = document.getElementById('dropdownMenuButton1');
    const dropdownDiaMenu = (dropdownDiaButton && dropdownDiaButton.nextElementSibling) || null;
    const searchResultsContainer = document.getElementById('search-results-container');
    const btnSiguiente = document.getElementById('btn-siguiente');

    // Referencias para la sección dinámica de día (plantilla ahora tiene un único contenedor)
    const seccionDias = document.getElementById('seccion-dias');
    const tituloDia = document.getElementById('titulo-dia');
    const lugaresDiaContainer = document.getElementById('lugares-dia');

    // Helper: mostrar/limpiar mensajes inline en la sección de días
    function clearInlineErrors() {
        if (!seccionDias) return;
        const existing = seccionDias.querySelector('.itinerario-inline-error');
        if (existing) existing.remove();
    }

    function showInlineError(message) {
        if (!seccionDias) {
            alert(message); // fallback
            return;
        }
        clearInlineErrors();
        const div = document.createElement('div');
        div.className = 'alert alert-danger itinerario-inline-error mt-2';
        div.role = 'alert';
        div.textContent = message;
        // Insertar arriba del contenedor de lugares para que sea visible
        seccionDias.insertBefore(div, seccionDias.firstChild);
        // Hacer scroll si está fuera de vista
        div.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Define el número máximo de días
    const MAX_DIAS = 3;


    if (!miItinerarioLista || !buscadorLugares) {
        console.warn("Elementos críticos faltan en DOM, abortando inicialización.");
        return;
    }    // Simulación de datos para demostración (el backend proporcionará esto)
    let lugaresRecomendadosData = []; // Esto se cargaría desde la API
    let lugaresPopularData = [];     // Esto se cargaría desde la API
    let miItinerarioActual = {};    // { dia: [lugares], dia2: [lugares] }
    let currentDay = 1; // Día actual seleccionado
    let searchTimeout;

    // ID del Itinerario (para cargar/guardar paradas)
    const ITINERARY_ID = document.body.dataset.itineraryId || null; // El backend debería pasar este ID
    // **ASEGÚRATE DE AÑADIR data-itinerary-id="{{ itinerary.id }}" AL <body> EN TU PLANTILLA DJANGO**

    // --- Funciones de Utilidad ---

    // Función para renderizar un lugar en la sección de recomendaciones/popular
    function renderLugarCard(container, lugar) {
        const col = document.createElement('div');
        col.classList.add('col');
        col.innerHTML = `
            <div class="card lugar-card">
                <img src="${lugar.imagen}" class="card-img-top" alt="${lugar.nombre}">
                <div class="card-body">
                    <h5 class="card-title-sm">${lugar.nombre}</h5>
                    <span class="badge categoria-badge categoria-${lugar.categoria.toLowerCase()}">${lugar.categoria}</span>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <button class="btn btn-sm btn-outline-info btn-ver" data-id="${lugar.id}">Ver</button>
                        <button class="btn btn-sm btn-outline-success btn-add"
                                data-id="${lugar.id}"
                                data-nombre="${lugar.nombre}"
                                data-categoria="${lugar.categoria}"
                                data-img="${lugar.imagen}">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(col);
    }

    // Función para renderizar un lugar en la lista de mi itinerario
    function renderLugarItinerario(lugar, index) {
        const item = document.createElement('div');
        item.classList.add('list-group-item', 'd-flex', 'align-items-center', 'lugar-itinerario-item');
        item.dataset.id = lugar.id; // Asume que 'lugar' tiene 'id'
        // **Verifica que 'lugar' tenga las propiedades 'imagen', 'nombre', 'categoria' que esperas**
        item.innerHTML = `
            <span class="orden-dia me-2">${index + 1}</span>
            <img src="${lugar.imagen || '/static/img/placeholder.png'}" alt="${lugar.nombre}" class="img-thumbnail me-3 lugar-itinerario-img">
            <div class="flex-grow-1">
                <h6 class="mb-0 lugar-itinerario-nombre">${lugar.nombre || 'Nombre no disponible'}</h6>
                <span class="badge categoria-badge categoria-${(lugar.categoria || 'general').toLowerCase()}-sm">${lugar.categoria || 'General'}</span>
            </div>
            <div class="ms-auto d-flex align-items-center">
                <button class="btn btn-sm btn-outline-secondary btn-mover-arriba me-1"><i class="fas fa-chevron-up"></i></button>
                <button class="btn btn-sm btn-outline-secondary btn-mover-abajo me-1"><i class="fas fa-chevron-down"></i></button>
                <button class="btn btn-sm btn-outline-danger btn-remove" data-id="${lugar.id}"><i class="fas fa-times"></i></button>
            </div>
        `;
        miItinerarioLista.appendChild(item);
    }

    // --- Carga Inicial de Datos  ---
    // --- MODIFICADO: Carga Inicial de Paradas Existentes ---
    async function cargarItinerarioActual() {
        if (!ITINERARY_ID) {
             console.warn("No Itinerary ID found for initial load.");
             miItinerarioActual = { '1': [] }; // Inicia vacío si no hay ID (modo creación pura)
             actualizarListaItinerario();
             actualizarDropdownDias();
             return;
        }
        try {
            // **NECESITAS CREAR ESTE ENDPOINT EN DJANGO**
            // Debe devolver JSON: [{ day_number: 1, placement: 1, touristic_place: {id: 101, name: "...", photo_url:"...", categories:[{name:"..."}] } }, ...]
            const response = await fetch(`/api/itineraries/${ITINERARY_ID}/stops/`); 
            if (!response.ok) throw new Error(`Error cargando paradas: ${response.statusText}`);
            const stopsData = await response.json();
            
            miItinerarioActual = {}; // Limpia antes de reconstruir
            stopsData.forEach(stop => {
                const day = stop.day_number;
                if (!miItinerarioActual[day]) {
                    miItinerarioActual[day] = [];
                }
                // Mapea los datos recibidos al formato que usa renderLugarItinerario
                miItinerarioActual[day].push({
                    id: stop.touristic_place.id,
                    nombre: stop.touristic_place.name,
                    // Toma la primera categoría o 'General'
                    categoria: stop.touristic_place.categories && stop.touristic_place.categories.length > 0 
                               ? stop.touristic_place.categories[0].name 
                               : 'General',
                    // Asume que tu TouristicPlaceSerializer devuelve una URL de imagen o null
                    imagen: stop.touristic_place.photo_url || '/static/img/placeholder.png', // **DEFINE 'photo_url' EN TU SERIALIZER/MODELO O CAMBIA ESTO**
                    // 'placement' no se guarda aquí, se deduce del orden en el array
                    lat: stop.touristic_place.lat, // **ASEGÚRATE DE QUE ESTOS CAMPOS EXISTAN**
                    lng: stop.touristic_place.long,  // **ASEGÚRATE DE QUE ESTOS CAMPOS EXISTAN**
                });
            });

            // Asegura que al menos el día 1 exista si no hay paradas
            if (Object.keys(miItinerarioActual).length === 0) {
                 miItinerarioActual = { '1': [] };
            } else {
                 // Asegura que los días estén ordenados y selecciona el primero existente
                 const days = Object.keys(miItinerarioActual).map(Number).sort((a, b) => a - b);
                 currentDay = days[0] || 1; 
            }

            actualizarListaItinerario();
            actualizarDropdownDias();

        } catch (error) {
            console.error("Error cargando itinerario existente:", error);
            miItinerarioActual = { '1': [] }; // Falla segura: itinerario vacío
            actualizarListaItinerario();
            actualizarDropdownDias();
        }
    }


    // --- Lógica del Itinerario (Columna Derecha) ---

    function actualizarListaItinerario() {
        // Limpia mensajes inline cada vez que actualizamos la vista
        clearInlineErrors();
        miItinerarioLista.innerHTML = ''; // Limpia la lista actual
        const lugaresDelDia = miItinerarioActual[currentDay] || [];
        lugaresDelDia.forEach((lugar, index) => renderLugarItinerario(lugar, index));

        // Ajustar el número de orden de los elementos
        miItinerarioLista.querySelectorAll('.orden-dia').forEach((span, index) => {
            span.textContent = index + 1;
        });

        // Actualiza la sección dinámica (título y listado de lugares visibles)
        try {
            if (tituloDia) {
                tituloDia.innerHTML = `<i class="fas fa-sun me-2 text-warning"></i>Día ${currentDay}`;
            }

            if (lugaresDiaContainer) {
                lugaresDiaContainer.innerHTML = ''; // Limpia
                const lugaresParaSeccion = miItinerarioActual[currentDay] || [];
                if (lugaresParaSeccion.length === 0) {
                    const p = document.createElement('p');
                    p.classList.add('text-muted');
                    p.textContent = 'No hay lugares para este día.';
                    lugaresDiaContainer.appendChild(p);
                    // Mensaje inline que indica la regla (se muestra sólo como pista, no es error al cargar)
                    const hint = document.createElement('small');
                    hint.classList.add('text-muted', 'd-block', 'mt-1');
                    hint.textContent = 'Un día no puede quedarse vacío si quieres guardarlo. Añade al menos una parada.';
                    lugaresDiaContainer.appendChild(hint);
                } else {
                    lugaresParaSeccion.forEach((lugar, index) => {
                        const div = document.createElement('div');
                        div.classList.add('d-flex', 'align-items-center', 'mb-2', 'lugar-seccion-item');
                        div.innerHTML = `
                            <img src="${lugar.imagen || '/static/img/placeholder.png'}" alt="${lugar.nombre || ''}" class="img-thumbnail me-2" style="width:48px;height:48px;object-fit:cover;">
                            <div class="flex-grow-1">
                                <strong class="d-block">${lugar.nombre || 'Sin nombre'}</strong>
                                <small class="text-muted">${lugar.categoria || ''}</small>
                            </div>
                            <span class="badge bg-secondary ms-2">${index + 1}</span>
                        `;
                        lugaresDiaContainer.appendChild(div);
                    });
                }
            }
        } catch (e) {
            console.error('Error actualizando la sección dinámica del día:', e);
        }

        // Actualiza los marcadores en el mapa
        actualizarMarcadores();
    }

    // Eliminar un día: solo permite eliminar el último día (cuenta regresiva)
    function eliminarUltimoDia(diaAEliminar) {
        const diasExistentes = Object.keys(miItinerarioActual).map(Number).sort((a, b) => a - b);
        if (diasExistentes.length <= 1) {
            alert('No se puede eliminar el único día.');
            return;
        }

        const ultimoDia = diasExistentes[diasExistentes.length - 1];
        if (diaAEliminar !== ultimoDia) {
            // Protección: solo se permite borrar el último día en cuenta regresiva
            alert('Sólo se puede eliminar el último día.');
            return;
        }

        // Eliminar la entrada del último día
        delete miItinerarioActual[diaAEliminar];

        // Reindexar los días para que queden 1..N sin huecos (manteniendo el orden)
        const diasOrdenados = Object.keys(miItinerarioActual).map(Number).sort((a, b) => a - b);
        const nuevoItinerario = {};
        diasOrdenados.forEach((d, idx) => {
            nuevoItinerario[idx + 1] = miItinerarioActual[d] || [];
        });
        miItinerarioActual = nuevoItinerario;

        // Ajusta currentDay si ahora está fuera de rango
        const nuevosDias = Object.keys(miItinerarioActual).map(Number);
        const maxNuevo = nuevosDias.length > 0 ? Math.max(...nuevosDias) : 1;
        if (currentDay > maxNuevo) currentDay = maxNuevo;

        // Actualiza vista
        actualizarDropdownDias();
        actualizarListaItinerario();
    }

    // --- MODIFICADA: actualizarDropdownDias ---
    function actualizarDropdownDias() {
        if (!dropdownDiaMenu) return; // Añade chequeo de seguridad
        dropdownDiaMenu.innerHTML = ''; // Limpiar opciones existentes
        
        const dias = Object.keys(miItinerarioActual).map(Number).sort((a, b) => a - b);
        
        // Si no hay días (ej. al cargar por primera vez y fallar), asegura el Día 1
        if (dias.length === 0) {
            miItinerarioActual[1] = [];
            dias.push(1);
        }

        const ultimoDia = dias.length > 0 ? Math.max(...dias) : 1;

        dias.forEach(diaNum => {
            const li = document.createElement('li');
            li.classList.add('dropdown-item-wrapper', 'd-flex', 'justify-content-between', 'align-items-center');
            
            // Enlace para seleccionar el día
            const a = document.createElement('a');
            a.classList.add('dropdown-item', 'flex-grow-1'); // Ocupa el espacio
            a.href = '#';
            a.textContent = `Día: ${diaNum}`;
            a.dataset.day = diaNum;
            li.appendChild(a);

            // Botón para eliminar el día: SOLO para el último día y si hay más de 1 día
            if (dias.length > 1 && diaNum === ultimoDia) {
                const btnEliminarDia = document.createElement('button');
                btnEliminarDia.classList.add('btn', 'btn-sm', 'btn-outline-danger', 'btn-eliminar-dia', 'ms-2');
                btnEliminarDia.innerHTML = '<i class="fas fa-trash-alt"></i>';
                btnEliminarDia.dataset.day = diaNum;
                // Previene que el menú se cierre al hacer clic en el botón
                btnEliminarDia.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    eliminarUltimoDia(parseInt(btnEliminarDia.dataset.day, 10));
                }); 
                li.appendChild(btnEliminarDia);
            }

            dropdownDiaMenu.appendChild(li);
        });

        // --- VALIDACIÓN DE 3 DÍAS ---
        // Añadir una opción para "Nuevo Día" solo si hay menos de MAX_DIAS
        if (dias.length < MAX_DIAS) {
            dropdownDiaMenu.appendChild(document.createElement('li')); // Divisor
            
            const liNuevoDia = document.createElement('li');
            const aNuevoDia = document.createElement('a');
            aNuevoDia.classList.add('dropdown-item', 'text-primary');
            aNuevoDia.href = '#';
            aNuevoDia.textContent = '+ Añadir Día';
            aNuevoDia.dataset.action = 'add-day';
            liNuevoDia.appendChild(aNuevoDia);
            dropdownDiaMenu.appendChild(liNuevoDia);
        } else {
             // Opcional: Muestra un mensaje de límite alcanzado
             const liLimite = document.createElement('li');
             liLimite.innerHTML = `<span class="dropdown-item-text text-muted small">Límite de ${MAX_DIAS} días alcanzado.</span>`;
             dropdownDiaMenu.appendChild(liLimite);
        }

        // Asegúrate de que currentDay sea válido
        if (!miItinerarioActual[currentDay]) {
            currentDay = dias[0] || 1;
        }
        dropdownDiaButton.textContent = `Día: ${currentDay}`;
    }

    // --- Manejo de Eventos ---

    // --- 4. MODIFICADO: Lógica de Búsqueda ---
    function buscarLugares(){
        clearTimeout(searchTimeout);
        const query = buscadorLugares.value.trim();
        searchResultsContainer.innerHTML = ''; // Limpia resultados

        if (query.length < 3) return;

        searchTimeout = setTimeout(async () => {
            try {
                // LLAMA A TU ENDPOINT DE BÚSQUEDA
                const response = await fetch(`/api/places/search/?query=${encodeURIComponent(query)}`);
                if (!response.ok) throw new Error(`Error en búsqueda: ${response.statusText}`);
                const results = await response.json();
                mostrarResultadosBusqueda(results); // Llama a la función para mostrar
            } catch (error) {
                console.error('Error al buscar lugares:', error);
                searchResultsContainer.innerHTML = '<p class="text-danger">Error al buscar.</p>';
            }
        }, 500);
    }
    buscadorLugares.addEventListener('input', () => {
        buscarLugares();
    });
    
    /**
     * FUNCIÓN CENTRALIZADA: Añadir Lugar al Itinerario
     * Propósito: Añade un lugar al 'miItinerarioActual[currentDay]'
     * validando duplicados.
     * Parámetros: placeData (un objeto JS con {id, nombre, categoria, imagen, lat, lng})
     */
    function addPlaceToItineraryFromData(placeData) {
        const nuevoLugar = {
            id: parseInt(placeData.id, 10),
            nombre: placeData.nombre,
            categoria: placeData.categoria,
            imagen: placeData.imagen,
            lat: placeData.lat || null,
            lng: placeData.lng || null,
        };

        // Asegura que exista el array del día seleccionado
        if (!miItinerarioActual[currentDay]) {
            miItinerarioActual[currentDay] = [];
        }

        // Validación básica: id y nombre son obligatorios
        if (!nuevoLugar.id || !nuevoLugar.nombre || nuevoLugar.nombre.toString().trim() === '') {
            alert('No se puede añadir un lugar vacío. Asegúrate de que el lugar tenga nombre e ID válidos.');
            return; // No añadir
        }

        // Validación de duplicados
        if (miItinerarioActual[currentDay].some(l => parseInt(l.id, 10) === nuevoLugar.id)) {
            alert('Este lugar ya está en tu itinerario para este día.');
            return; // No añadir
        }

        miItinerarioActual[currentDay].push(nuevoLugar);
        actualizarListaItinerario(); // Refresca la UI
        
        // (Opcional) Notificación de éxito
        // alert(`${nuevoLugar.nombre} ha sido agregado.`);
    }

    // NUEVA FUNCIÓN: Mostrar Resultados de Búsqueda
    function mostrarResultadosBusqueda(results) {
        searchResultsContainer.innerHTML = ''; // Limpia
        if (!results || results.length === 0) {
            searchResultsContainer.innerHTML = '<p class="text-muted">No se encontraron lugares.</p>';
            return;
        }
        results.forEach(lugar => {
            const div = document.createElement('div');
            div.classList.add('search-result-item', 'd-flex', 'justify-content-between', 'align-items-center', 'p-2', 'border-bottom');
            // **Verifica las propiedades devueltas por tu TouristicPlaceSerializer**
            const categoriaNombre = lugar.categories && lugar.categories.length > 0 ? lugar.categories[0].name : 'General';
            // **NECESITAS UNA URL DE IMAGEN EN TU TouristicPlaceSerializer, ej. 'photo_url'**
            // Preferimos 'photo_url' (proporcionado por el serializer); si no existe, usamos placeholder
            const imagenUrl = lugar.photo_url || lugar.photo || '/static/img/placeholder.png';

            // Construir HTML con imagen, categoría, dirección, rating y botones
            const imagenHTML = imagenUrl ? `<img src="${imagenUrl}" alt="${lugar.name || ''}" class="imagen-resultado">` : '<div class="imagen-placeholder"></div>';

            div.innerHTML = `
                <div class="d-flex align-items-start">
                    ${imagenHTML}
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <span class="badge categoria-badge" style="background: #e3f2fd; color: #1976d2; font-size: 0.7rem; margin-bottom: 5px;">
                                    ${categoriaNombre}
                                </span>
                                <h6 class="text-primary mb-0">${lugar.name || 'Sin nombre'}</h6>
                            </div>
                        </div>
                        <p class="mb-2 text-muted small">
                            <i class="fas fa-map-marker-alt me-1"></i>
                            ${lugar.address || 'Dirección no disponible'}
                        </p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-light text-dark">
                                <i class="fas fa-star text-warning me-1"></i>
                                ${lugar.rating || 'N/A'}
                            </span>
                            <div>
                                <!-- Hemos añadido data-description, data-phone, data-website, etc. -->
                                <!-- Nota: Usamos encodeURIComponent para datos que pueden tener comillas o caracteres especiales. -->
                                <button class="btn btn-outline-primary btn-sm me-1 btn-ver" 
                                        data-id="${lugar.id}"
                                        data-nombre="${lugar.name || 'Sin nombre'}"
                                        data-direccion="${lugar.address || 'Dirección no disponible'}"
                                        data-descripcion="${encodeURIComponent(lugar.description || 'Descripción no disponible.')}"
                                        data-website="${lugar.website || ''}"
                                        data-phone="${lugar.phone_number || ''}"
                                        data-rating="${lugar.external_api_rating || 'N/A'}"
                                        data-img="${imagenUrl}"
                                        
                                        data-categoria="${(categoriaNombre || 'General').toString().replace(/'/g, "\\'") }"
                                        data-lat="${lugar.lat || ''}"
                                        data-lng="${lugar.long || ''}">
                                    <i class="fas fa-info-circle me-1"></i>Info
                                </button>
                                <button class="btn btn-success btn-sm btn-add"
                                        data-id="${lugar.id}"
                                        data-nombre="${(lugar.name || 'Sin nombre').toString().replace(/'/g, "\\'") }"
                                        data-categoria="${(categoriaNombre || 'General').toString().replace(/'/g, "\\'") }"
                                        data-img="${imagenUrl}"
                                        data-lat="${lugar.lat || ''}"
                                        data-lng="${lugar.long || ''}">
                                    <i class="fas fa-plus me-1"></i>Agregar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            searchResultsContainer.appendChild(div);
        });
    }

    // Evento para añadir un lugar a "Mi Itinerario"
    document.addEventListener('click', async (event) => {
        // Evento para añadir un lugar (desde la tarjeta de búsqueda)
        if (event.target.classList.contains('btn-add') || event.target.closest('.btn-add')) {
            const btn = event.target.closest('.btn-add');
            
            // Simplemente extrae los datos y llama a la función central
            addPlaceToItineraryFromData({
                id: btn.dataset.id,
                nombre: btn.dataset.nombre,
                categoria: btn.dataset.categoria,
                imagen: btn.dataset.img,
                lat: btn.dataset.lat,
                lng: btn.dataset.lng
            }, miItinerarioActual);
        }

        // Evento para eliminar un lugar de "Mi Itinerario"
        if (event.target.classList.contains('btn-remove') || event.target.closest('.btn-remove')) {
            const btn = event.target.closest('.btn-remove');
            const lugarIdToRemove = btn.dataset.id;

            miItinerarioActual[currentDay] = miItinerarioActual[currentDay].filter(lugar => lugar.id != lugarIdToRemove);
            actualizarListaItinerario();
        }

        // Evento para cambiar de día en el dropdown
        if (event.target.classList.contains('dropdown-item') && event.target.dataset.day) {
            event.preventDefault();
            currentDay = parseInt(event.target.dataset.day);
            actualizarListaItinerario();
            dropdownDiaButton.textContent = `Día: ${currentDay}`;
        }

        // Evento para añadir un nuevo día
        if (event.target.classList.contains('dropdown-item') && event.target.dataset.action === 'add-day') {
            event.preventDefault();
            const newDay = Object.keys(miItinerarioActual).length + 1;
            miItinerarioActual[newDay] = [];
            currentDay = newDay;
            actualizarDropdownDias();
            actualizarListaItinerario();
            // Opcional: Llamada al backend para crear un nuevo día
        }

        // Evento para ver detalles del lugar
        if (event.target.classList.contains('btn-ver') || event.target.closest('.btn-ver')) {
        const btn = event.target.closest('.btn-ver');
        const dataset = btn.dataset;

        // Leemos los datos que guardamos en el botón
        const nombre = dataset.nombre;
        const direccion = dataset.direccion;
        const descripcion = decodeURIComponent(dataset.descripcion); // Decodificamos
        const website = dataset.website;
        const phone = dataset.phone;
        const rating = dataset.rating;
        const img = dataset.img;
        const lugarId = dataset.id; // ID interno

        // Referencias a tu modal (ya existen en tu HTML)
        const modalBody = document.getElementById('modalDetallesBody');
        const modalEl = document.getElementById('modalDetallesLugar');
        const btnAgregarModal = document.getElementById('btnAgregarDesdeModal');

        if (!modalBody || !modalEl) {
            alert(`Detalles para: ${nombre}\n${direccion}`); // Fallback
            return;
        }

        // 1. Construir el HTML interno del modal
        const imagenHTML = (img && img !== '/static/img/placeholder.png') 
            ? `<img src="${img}" class="imagen-principal" alt="${nombre}">` 
            : '';

        const websiteHTML = website 
            ? `<div class="contacto-item">
                <i class="fas fa-globe"></i>
                <span><a href="${website}" target="_blank">${website}</a></span>
            </div>` 
            : '';
        
        const phoneHTML = phone
            ? `<div class="contacto-item">
                <i class="fas fa-phone"></i>
                <span>${phone}</span>
            </div>`
            : '';

        const content = `
            <div class="detalle-lugar-card" data-place-id="${lugarId}">
                ${imagenHTML}
                <div class="detalle-lugar-body">
                    <div class="info-basica">
                        <div class="titulo-categoria-container">
                            <h3 class="titulo-lugar" data-place-id="${lugarId}">${nombre}</h3>
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

        // 2. Inyectar el HTML en el modal
        modalBody.innerHTML = content;

        // 3. Configurar el botón "Agregar" del modal (si existe)
        // (Tu función 'agregarAItinerario' usa el SDK de Google para
        // obtener la 'categoria', lat/lng. Sería mejor pasarle esto también)
        if (btnAgregarModal && modalEl) {
            
            // Recolecta los datos para la función de añadir
            const placeDataParaModal = {
                id: dataset.id,
                nombre: dataset.nombre,
                categoria: dataset.categoria, // <-- ¡Ahora existe!
                imagen: dataset.img,
                lat: dataset.lat,             // <-- ¡Ahora existe!
                lng: dataset.lng              // <-- ¡Ahora existe!
            };

            // 1. Quita cualquier listener 'onclick' anterior para evitar bugs
            btnAgregarModal.onclick = null; 
            
            // 2. Asigna el nuevo listener
            btnAgregarModal.onclick = function() {
                // 3. Llama a la MISMA función central
                addPlaceToItineraryFromData(placeDataParaModal,miItinerarioActual);
                
                // 4. Cierra el modal
                try {
                    const bsModal = bootstrap.Modal.getInstance(modalEl);
                    if (bsModal) bsModal.hide();
                } catch (e) {}
            };
        }

        // 4. Mostrar el modal
        try {
            const bsModal = new bootstrap.Modal(modalEl);
            bsModal.show();
        } catch (e) {
            console.error("Error al mostrar modal de Bootstrap", e);
        }
}

        // Evento para botón Atrás
        if (event.target.classList.contains('boton-atras')) {
            window.history.back(); // Vuelve a la página anterior
        }

        // Lógica para mover un elemento arriba/abajo en la lista
        if (event.target.classList.contains('btn-mover-arriba') || event.target.closest('.btn-mover-arriba')) {
            const btn = event.target.closest('.btn-mover-arriba');
            const item = btn.closest('.lugar-itinerario-item');
            const lugarId = item.dataset.id;
            const index = miItinerarioActual[currentDay].findIndex(l => l.id == lugarId);

            if (index > 0) {
                const [movedItem] = miItinerarioActual[currentDay].splice(index, 1);
                miItinerarioActual[currentDay].splice(index - 1, 0, movedItem);
                actualizarListaItinerario();
                // Opcional: LLAMADA AL BACKEND para actualizar el orden
            }
        }

        if (event.target.classList.contains('btn-mover-abajo') || event.target.closest('.btn-mover-abajo')) {
            const btn = event.target.closest('.btn-mover-abajo');
            const item = btn.closest('.lugar-itinerario-item');
            const lugarId = item.dataset.id;
            const index = miItinerarioActual[currentDay].findIndex(l => l.id == lugarId);

            if (index < miItinerarioActual[currentDay].length - 1) {
                const [movedItem] = miItinerarioActual[currentDay].splice(index, 1);
                miItinerarioActual[currentDay].splice(index + 1, 0, movedItem);
                actualizarListaItinerario();
                // Opcional: LLAMADA AL BACKEND para actualizar el orden
            }
        }

    });

    // --- MODIFICADO: Guardado Final (Botón Siguiente) ---
    btnSiguiente.addEventListener('click', async () => {
        console.log("Guardando itinerario:", miItinerarioActual);
        if (!ITINERARY_ID) {
             alert("Error: No se pudo identificar el itinerario a guardar.");
             return;
        }

        // Formatear datos para la API (con validaciones para evitar enviar paradas vacías)
        const stopsPayload = [];
        let invalidFound = false;
        for (const day in miItinerarioActual) {
            const dayArr = miItinerarioActual[day] || [];
            dayArr.forEach((lugar, index) => {
                // Validación: lugar y su id deben existir
                if (!lugar || lugar.id === undefined || lugar.id === null || isNaN(parseInt(lugar.id, 10))) {
                    invalidFound = true;
                    return;
                }

                // Añade solo entradas válidas
                stopsPayload.push({
                    touristic_place: parseInt(lugar.id, 10),
                    day_number: parseInt(day, 10),
                    placement: index + 1
                });
            });
        }

        if (invalidFound) {
            // Mostrar mensaje inline en la UI en lugar de alert
            showInlineError('Hay una o más paradas con datos incompletos (ID o nombre faltante). Revisa y elimina las paradas vacías antes de guardar.');
            // Restaurar estado del botón
            btnSiguiente.disabled = false;
            btnSiguiente.textContent = 'Siguiente';
            return;
        }

        if (stopsPayload.length === 0) {
            // Mostrar mensaje inline en la UI para indicar que el día no puede estar vacío
            showInlineError('No hay paradas para guardar. Añade al menos una parada al día actual antes de continuar.');
            btnSiguiente.disabled = false;
            btnSiguiente.textContent = 'Siguiente';
            return;
        }

        // LLAMADA AL BACKEND: Usa PATCH para actualizar solo las paradas
        const csrftoken = getCookie('csrftoken'); // **ASEGÚRATE QUE ESTÉ ACTIVO**
        const apiUrl = `/api/itineraries/${ITINERARY_ID}/stops/`; 

        // Deshabilita botón y muestra carga
        btnSiguiente.disabled = true;
        btnSiguiente.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        try {
            const response = await fetch(apiUrl, {
                method: 'PATCH', // PATCH es ideal para actualizar solo una parte (las paradas)
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken // **ASEGÚRATE QUE ESTÉ ACTIVO**
                },
                body: JSON.stringify({
                    stops: stopsPayload // Envía solo el array de paradas
                })
            });

            // Habilita botón
            btnSiguiente.disabled = false;
            btnSiguiente.textContent = 'Siguiente';

            if (!response.ok) {
                 const errorData = await response.json();
                 throw new Error(JSON.stringify(errorData));
            }
            const data = await response.json();
            console.log('Itinerario guardado:', data);
            alert('Paradas del itinerario guardadas con éxito!');
            
            // **DEFINE LA URL DE REDIRECCIÓN FINAL**
            // Por ejemplo, a una página que muestre el itinerario completo
            window.location.href = `/itinerary/${ITINERARY_ID}/view/`; // Cambia '/view/' por tu URL real

        } catch (error) {
            console.error('Error al guardar el itinerario:', error);
            alert(`Hubo un error al guardar las paradas: ${error.message}`);
            // Habilita botón en caso de error
             btnSiguiente.disabled = false;
             btnSiguiente.textContent = 'Siguiente';
        }
    });

    

    // --- Inicializar la página ---
    cargarItinerarioActual();


});