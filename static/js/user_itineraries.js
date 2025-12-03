/* static/js/user_itineraries.js */

document.addEventListener('DOMContentLoaded', function() {
    console.log("-> JS de Mis Itinerarios cargado.");

    // --- 1. LÓGICA DE FILTROS ---
    const filterButtons = document.querySelectorAll('.filter-btn');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); 
            
            // UX: Actualizar estado visual de los botones
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // Redirección según el filtro
            const filter = this.getAttribute('data-filter');
            if (filter === 'all') {
                window.location.href = window.location.pathname; // Limpia la URL
            } else {
                window.location.href = `?status=${filter}`; // Recarga con filtro
            }
        });
    });
});

/**
 * --- 2. LÓGICA DEL MODAL DE BORRADO (SNIPPET) ---
 * Esta función debe ser GLOBAL (window.) porque se llama desde el HTML
 * usando onclick="abrirModalBorrar(...)"
 */
window.abrirModalBorrar = function(id, title) {
    // Estos IDs deben coincidir con tu snippet 'delete_modal.html'
    const nameSpan = document.getElementById('deleteItineraryName');
    const form = document.getElementById('deleteForm');
    const modalEl = document.getElementById('deleteModal');

    if (nameSpan && form && modalEl) {
        // 1. Poner el nombre en el texto
        nameSpan.textContent = title;
        
        // 2. Actualizar la acción del formulario
        // Asegúrate que esta URL coincida con tu urls.py
        form.action = `/itineraries/delete/${id}/`;
        
        // 3. Mostrar el modal usando Bootstrap
        const deleteModal = new bootstrap.Modal(modalEl);
        deleteModal.show();
    } else {
        console.error("Error: No se encontraron los elementos del snippet delete_modal.html");
    }
};

window.cambiarPrivacidad = async function(id, nuevaPrivacidad) {
    try {
        const response = await fetch(`/api/itineraries/${id}/privacy/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Tu función getCookie existente
            },
            body: JSON.stringify({ privacy: nuevaPrivacidad })
        });
        
        if (response.ok) {
            // Recargar para ver el cambio de icono (o actualizar el DOM manualmente)
            window.location.reload(); 
        } else {
            alert("Error al actualizar la privacidad.");
        }
    } catch (error) {
        console.error(error);
    }
};