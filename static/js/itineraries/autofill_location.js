document.addEventListener('DOMContentLoaded', () => {
    const inputUbicacion = document.getElementById('ubicacion-principal');
    // Crea un div para mostrar sugerencias (añádelo al HTML si no existe)
    let suggestionsDiv = document.getElementById('suggestions-ubicacion');
    if (!suggestionsDiv) {
        suggestionsDiv = document.createElement('div');
        suggestionsDiv.id = 'suggestions-ubicacion';
        suggestionsDiv.classList.add('list-group', 'position-absolute', 'w-100', 'mt-1'); // Clases Bootstrap
        suggestionsDiv.style.zIndex = "10"; // Para que esté sobre otros elementos
        inputUbicacion.parentNode.style.position = 'relative'; // El contenedor necesita ser relativo
        inputUbicacion.parentNode.appendChild(suggestionsDiv);
    }

    let debounceTimer;

    inputUbicacion.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = inputUbicacion.value.trim();
        suggestionsDiv.innerHTML = ''; // Limpia sugerencias anteriores

        if (query.length < 3) { // No buscar si es muy corto
            return;
        }

        debounceTimer = setTimeout(() => {
            // ¡CAMBIA LA URL DEL FETCH!
            fetch(`/api/geocode/autocomplete/?query=${encodeURIComponent(query)}`) 
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(suggestions => { // 'suggestions' es ahora la lista devuelta por Django
                    suggestionsDiv.innerHTML = '';
                    if (suggestions && suggestions.length > 0) {
                        suggestions.forEach(result => {
                            const suggestionItem = document.createElement('a');
                            suggestionItem.href = '#';
                            suggestionItem.classList.add('list-group-item', 'list-group-item-action');
                            // Adapta al formato devuelto por tu API Django
                            suggestionItem.textContent = result.description; 
                            suggestionItem.addEventListener('click', (e) => {
                                e.preventDefault();
                                inputUbicacion.value = result.description;
                                suggestionsDiv.innerHTML = '';
                                // Aquí necesitarías otra llamada a la API si quieres lat/lon
                                // O tu API de Django podría devolverlos directamente
                            });
                            suggestionsDiv.appendChild(suggestionItem);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching autocomplete suggestions:', error);
                    suggestionsDiv.innerHTML = '';
                });
        }, 300); // Espera 300ms después de que el usuario deja de escribir
    });

    // Ocultar sugerencias si se hace clic fuera
    document.addEventListener('click', (event) => {
        if (!inputUbicacion.contains(event.target) && !suggestionsDiv.contains(event.target)) {
            suggestionsDiv.innerHTML = '';
        }
    });
});