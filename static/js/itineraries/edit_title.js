// Espera a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
    // Obtiene referencias a los elementos del DOM
    const spanTitulo = document.getElementById('nombre-itinerario-titulo');
    const inputTitulo = document.getElementById('input-editar-titulo');
    const botonEditar = document.getElementById('boton-editar-titulo');
    const botonGuardar = document.getElementById('boton-guardar-titulo');

    // Verifica si todos los elementos existen antes de añadir listeners
    if (spanTitulo && inputTitulo && botonEditar && botonGuardar) {

        // --- Funciones ---
        // Función para cambiar a modo edición
        function activarEdicion() {
            const textoActual = spanTitulo.textContent.trim(); // Obtiene el texto actual
            spanTitulo.classList.add('d-none');           // Oculta el span
            botonEditar.classList.add('d-none');         // Oculta el lápiz

            inputTitulo.value = textoActual;             // Pone el texto en el input
            inputTitulo.classList.remove('d-none');      // Muestra el input
            botonGuardar.classList.remove('d-none');     // Muestra el check (guardar)
            inputTitulo.focus();                         // Pone el cursor en el input
        }

        // Función para guardar y salir del modo edición
        function guardarEdicion() {
            const nuevoTexto = inputTitulo.value.trim(); // Obtiene el nuevo texto
            spanTitulo.textContent = nuevoTexto || "[Nombre del Itinerario]"; // Actualiza el span (o pone placeholder si está vacío)
            spanTitulo.classList.remove('d-none');       // Muestra el span
            botonEditar.classList.remove('d-none');     // Muestra el lápiz

            inputTitulo.classList.add('d-none');         // Oculta el input
            botonGuardar.classList.add('d-none');       // Oculta el check (guardar)

            // Obtener el ID oculto del itinerario (asumiendo que tiene id="itinerary_id_hidden" o similar)
            // const itinerarioIdInput = document.querySelector('input[name="itinerary_id"]');
            // const itinerarioId = itinerarioIdInput ? itinerarioIdInput.value : null;

            // AQUÍ es donde el equipo de backend llamaría a la función
            // para enviar 'nuevoTexto' y el ID del itinerario a Django
            // Ejemplo: if (itinerarioId) { enviarTituloAlBackend(itinerarioId, nuevoTexto); }
            console.log("Título guardado (simulado):", nuevoTexto);
            // console.log("ID del Itinerario (simulado):", itinerarioId); // Para pruebas
        }


        // --- Event Listeners ---
        // Clic en el botón Editar (lápiz)
        botonEditar.addEventListener('click', (event) => {
            event.preventDefault(); // Evita que el enlace '#' recargue la página
            activarEdicion();
        });

        // Clic en el botón Guardar (check)
        botonGuardar.addEventListener('click', (event) => {
            event.preventDefault();
            guardarEdicion();
        });

        // Guardar también al presionar Enter en el input
        inputTitulo.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault(); // Evita enviar el formulario principal
                guardarEdicion();
            }
        });

        // Opcional: Guardar si se pierde el foco del input
        inputTitulo.addEventListener('blur', () => {
            // Pequeño retraso para permitir hacer clic en el botón guardar
            setTimeout(() => {
                // Solo guarda si el input todavía está visible (por si ya se hizo clic en guardar)
                if (!inputTitulo.classList.contains('d-none')) {
                    guardarEdicion();
                }
            }, 100);
        });
    } else {
        console.error("No se encontraron todos los elementos necesarios para la edición del título.");
    }
}); // Fin del DOMContentLoaded