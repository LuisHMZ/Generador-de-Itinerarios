// static/js/auth.js

// Función auxiliar para obtener el valor de la cookie CSRF
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

const formSimpleRegister = document.getElementById('form-simple-register');
const mensajeSimpleRegisterDiv = document.getElementById('mensaje-simple-registro');

if (formSimpleRegister && mensajeSimpleRegisterDiv) { // Verifica que ambos elementos existan
    formSimpleRegister.addEventListener('submit', function(event) {
        event.preventDefault(); // Evita recarga de página

        mensajeSimpleRegisterDiv.textContent = ''; // Limpia mensajes anteriores
        mensajeSimpleRegisterDiv.style.color = 'black'; // Resetea color

        const formData = new FormData(formSimpleRegister);
        const csrftoken = getCookie('csrftoken');
        // Define la URL de tu vista de registro
        const registerUrl = '/register/'; // Ajusta si tu URL es diferente

        fetch(registerUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                // Cabecera para que Django sepa que es AJAX/Fetch
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData // Envía los datos del formulario
        })
        .then(response => {
            // Revisa si la respuesta fue OK (2xx) o si hubo error (4xx, 5xx)
            if (!response.ok) {
                 // Si no fue OK, intenta leer el cuerpo como JSON (para los errores)
                 return response.json().then(errData => {
                     // Lanza un objeto de error estructurado
                     throw { status: response.status, data: errData };
                 });
            }
            // Si fue OK, lee el cuerpo como JSON (para el mensaje de éxito)
            return response.json();
        })
        .then(data => {
            // Procesa la respuesta JSON de éxito
            if (data.status === 'success') {
                mensajeSimpleRegisterDiv.textContent = data.message;
                mensajeSimpleRegisterDiv.style.color = 'green';
                formSimpleRegister.reset(); // Limpia el formulario
                // Podrías redirigir después de un momento
                // setTimeout(() => { window.location.href = '/accounts/login/'; }, 2000);
            } else {
                 // Esto no debería pasar si la respuesta fue 'ok', pero por si acaso
                 mensajeSimpleRegisterDiv.textContent = data.message || 'Ocurrió un error inesperado.';
                 mensajeSimpleRegisterDiv.style.color = 'red';
            }
        })
        .catch(error => {
            // Maneja errores de red o la respuesta JSON de error del servidor
            console.error('Error en el registro:', error);
            if (error.status === 400 && error.data && error.data.errors) {
                // Muestra los errores de validación específicos del formulario
                let errorMsg = 'Error en el registro: ';
                const errors = error.data.errors;
                // Formatea los errores devueltos por form.errors
                for (const field in errors) {
                    errorMsg += `${field}: ${errors[field][0].message || errors[field][0]} `; // Toma el primer error de cada campo
                }
                mensajeSimpleRegisterDiv.textContent = errorMsg.trim();
            } else if (error.data && error.data.message) {
                 // Si el servidor envió un mensaje de error genérico
                 mensajeSimpleRegisterDiv.textContent = error.data.message;
            }
             else {
                // Error de red u otro error inesperado
                mensajeSimpleRegisterDiv.textContent = 'Ocurrió un error de conexión. Inténtalo de nuevo.';
            }
            mensajeSimpleRegisterDiv.style.color = 'red';
        });
    });
} else {
    // Ayuda para depurar si los elementos no se encuentran
    if (!formSimpleRegister) console.error("Formulario con ID 'form-simple-register' no encontrado.");
    if (!mensajeSimpleRegisterDiv) console.error("Div con ID 'mensaje-simple-registro' no encontrado.");
}