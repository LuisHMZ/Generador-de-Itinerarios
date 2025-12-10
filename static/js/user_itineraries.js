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
 * --- 2. LÓGICA DE ELIMINACIÓN CON SWEETALERT2 ---
 * Esta función debe ser GLOBAL (window.) porque se llama desde el HTML
 * usando onclick="abrirModalBorrar(...)"
 */
window.abrirModalBorrar = function(id, title) {
    Swal.fire({
        title: '¿Estás seguro?',
        html: `¿Deseas eliminar el itinerario <strong>${title}</strong>?<br><small class="text-danger">Esta acción no se puede deshacer.</small>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Crear un formulario dinámico y enviarlo
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/itineraries/delete/${id}/`;
            
            // Agregar el token CSRF
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = getCookie('csrftoken');
            form.appendChild(csrfInput);
            
            // Agregar al DOM y enviar
            document.body.appendChild(form);
            form.submit();
        }
    });
};

/**
 * --- 3. FUNCIÓN AUXILIAR PARA OBTENER COOKIES ---
 */
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

window.cambiarPrivacidad = async function(id, nuevaPrivacidad) {
    try {
        const response = await fetch(`/api/itineraries/${id}/privacy/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
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