/**
 * JavaScript diseñado para usarse en la vista create_edit_itinerary.html
 * Valida que la fecha de término no sea anterior a la fecha de inicio.
 */

document.addEventListener('DOMContentLoaded', () => {
    const fechaInicioInput = document.getElementById('fecha-inicio');
    const fechaTerminoInput = document.getElementById('fecha-termino');
    const form = document.getElementById('form-editar-itinerario');

    function validarFechas() {
        const fechaInicio = fechaInicioInput.value;
        const fechaTermino = fechaTerminoInput.value;

        // Limpia validación anterior
        fechaTerminoInput.classList.remove('is-invalid');
        fechaTerminoInput.setCustomValidity(''); // Quita mensaje de error nativo

        if (fechaInicio && fechaTermino && fechaTermino < fechaInicio) {
            fechaTerminoInput.classList.add('is-invalid'); // Añade estilo de error Bootstrap
            // Opcional: Añadir un div <div class="invalid-feedback"> en el HTML
            // const errorDiv = fechaTerminoInput.nextElementSibling;
            // if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
            //     errorDiv.textContent = 'La fecha de término no puede ser anterior a la fecha de inicio.';
            // }
            fechaTerminoInput.setCustomValidity('La fecha de término no puede ser anterior a la fecha de inicio.'); // Mensaje para validación HTML5
            return false; // Indica que la validación falló
        }
        return true; // Indica que la validación pasó
    }

    if(fechaInicioInput && fechaTerminoInput) {
        fechaInicioInput.addEventListener('change', validarFechas);
        fechaTerminoInput.addEventListener('change', validarFechas);
    }

    // Opcional: Validar también antes de enviar el formulario
    if (form) {
        form.addEventListener('submit', (event) => {
            if (!validarFechas()) {
                event.preventDefault(); // Detiene el envío si las fechas son inválidas
                alert('Error: La fecha de término no puede ser anterior a la fecha de inicio.'); // Alerta simple
                // O podrías hacer focus en el campo de fecha de término
            }
            // Aquí irían otras validaciones del formulario antes de enviar
        });
    }
});