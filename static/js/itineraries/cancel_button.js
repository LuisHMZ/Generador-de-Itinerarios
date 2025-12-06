document.addEventListener('DOMContentLoaded', () => {
    const botonCancelar = document.querySelector('.boton-cancelar');

    if (botonCancelar) {
        botonCancelar.addEventListener('click', () => {
            // Opción 1: Volver a la página anterior en el historial
            // window.history.back();

            // Opción 2: Redirigir a una página específica (ej. la lista de itinerarios)
            window.location.href = '/itineraries'; // <-- CAMBIA A TU URL CORRECTA
        });
    }
});