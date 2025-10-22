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
                // Redireccionamiento, aun no implementado
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

/******************************************************************************************/
/*************************Inicio de sesión simple con fetch API****************************/
/******************************************************************************************/
const formSimpleLogin = document.getElementById('form-simple-login'); // ID del nuevo form
const mensajeSimpleLoginDiv = document.getElementById('mensaje-login'); // Div para mensajes

if (formSimpleLogin && mensajeSimpleLoginDiv) {
    formSimpleLogin.addEventListener('submit', function(event) {
        event.preventDefault();

        mensajeSimpleLoginDiv.textContent = ''; // Limpia mensajes
        mensajeSimpleLoginDiv.style.color = 'black';

        const formData = new FormData(formSimpleLogin);
        const csrftoken = getCookie('csrftoken');
        const loginUrl = '/login/'; // URL de la vista de login definida en settings/urls.py

        fetch(loginUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                 return response.json().then(errData => {
                     throw { status: response.status, data: errData };
                 });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                mensajeSimpleLoginDiv.textContent = data.message;
                mensajeSimpleLoginDiv.style.color = 'green';
                // Redirige después del login exitoso
                window.location.href = data.redirect_url || '/'; // Redirige a la URL proporcionada o a la raíz
            } else if (data.status === 'info') {
                 // Caso: Ya estaba logueado
                 mensajeSimpleLoginDiv.textContent = data.message;
                 mensajeSimpleLoginDiv.style.color = 'blue';
                 window.location.href = data.redirect_url || '/';
            }
        })
        .catch(error => {
            console.error('Error en el inicio de sesión:', error);
            if (error.status === 400 && error.data && error.data.errors) {
                // Muestra errores de validación (ej. contraseña incorrecta)
                let errorMsg = '';
                if (error.data.errors.__all__) { // Error general de AuthenticationForm
                     errorMsg = error.data.errors.__all__[0];
                } else { // Errores por campo (es raro en login, pero por si acaso)
                     for (const field in error.data.errors) {
                         errorMsg += `${field}: ${error.data.errors[field][0]} `;
                     }
                }
                mensajeSimpleLoginDiv.textContent = errorMsg.trim() || 'Usuario o contraseña incorrectos.';
            } else {
                mensajeSimpleLoginDiv.textContent = 'Ocurrió un error inesperado.';
            }
            mensajeSimpleLoginDiv.style.color = 'red';
        });
    });
} else {
     if (!formSimpleLogin) console.error("Formulario con ID 'form-simple-login' no encontrado.");
     if (!mensajeSimpleLoginDiv) console.error("Div con ID 'mensaje-login' no encontrado.");
}