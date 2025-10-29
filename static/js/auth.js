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
const form = document.getElementById('form-simple-register');
const alertSuccessDivReg = document.getElementById('alert-success');
const alertErrorDivReg = document.getElementById('alert-error');
const successMessageSpanReg = document.getElementById('success-message');
const errorMessageSpanReg = document.getElementById('error-message');

function showAlert(alertElement, message) {
        alertElement.style.display = 'block';
        if (alertElement === alertSuccessDivReg) {
            successMessageSpanReg.textContent = message;
        } else {
            errorMessageSpanReg.textContent = message;
        }
        setTimeout(() => alertElement.style.display = 'none', 5000);
    }
function showFieldError(input, message) {
        const errorMsg = input.parentElement.querySelector('.error-msg');
        if (message) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            if (errorMsg) {
                errorMsg.textContent = message;
                errorMsg.style.display = 'block';
            }
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            if (errorMsg) {
                errorMsg.textContent = '';
                errorMsg.style.display = 'none';
            }
        }
    }

    // === VALIDACIONES INDIVIDUALES ===
    function validateEmail(input) {
        const value = input.value.trim();
        if (!value) return 'El correo es obligatorio y debe contener un "@" y un dominio.';
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Ingresa un correo válido.';
        return '';
    }

    function validatePassword(input) {
        if (input.value.length < 8) return 'La contraseña debe tener al menos 8 caracteres.';
        return '';
    }

    function validateConfirmPassword() {
        const pass = document.getElementById('id_password1').value;
        const confirm = document.getElementById('id_password2').value;
        if (!confirm) return 'Confirma tu contraseña.';
        if (pass !== confirm) return 'Las contraseñas no coinciden.';
        return '';
    }

    function validateAge(input) {
        if (!input.value) return 'La fecha de nacimiento es obligatoria.';
        const birthDate = new Date(input.value);
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        const m = today.getMonth() - birthDate.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
        if (age < 18) return 'Debes ser mayor de 18 años.';
        return '';
    }

    function validateRequired(input) {
        if (input.hasAttribute('required') && !input.value.trim()) return 'Este campo es obligatorio.';
        return '';
    }

    // === VALIDAR CAMPO EN TIEMPO REAL ===
    function validarCampo(input) {
        let mensaje = '';

        if (input.id === 'id_email') mensaje = validateEmail(input);
        else if (input.id === 'id_password1') mensaje = validatePassword(input);
        else if (input.id === 'id_password2') mensaje = validateConfirmPassword(input);
        else if (input.id === 'id_birth_date') mensaje = validateAge(input);
        else mensaje = validateRequired(input);

        showFieldError(input, mensaje);
        return mensaje === '';
    }

if (formSimpleRegister && alertSuccessDivReg && alertErrorDivReg) { // Verifica que ambos elementos existan
    formSimpleRegister.addEventListener('submit', function(event) {
        event.preventDefault(); // Evita recarga de página
        console.log("Ejecutando validación frontend...");
        alertSuccessDivReg.style.display = 'none';
        alertErrorDivReg.style.display = 'none';
        errorMessageSpanReg.textContent = '';

        let formValid = true;
        // Necesitamos obtener los inputs aquí DENTRO del listener
        const inputs = formSimpleRegister.querySelectorAll('.form-control');

        inputs.forEach(input => {
            // Revalida cada campo y actualiza su estado visual
            if (!validarCampo(input)) { // validarCampo ahora devuelve true/false
                console.log(`Error de validación Frontend en campo: ${input.id || input.name}`);
                formValid = false; // Si CUALQUIER campo falla, el form no es válido
            }
        });
        if (!formValid) {
            console.log("Validación Frontend falló. Envío a Django cancelado.");
            showAlert(alertErrorDivReg, 'Por favor, corrige los errores antes de continuar.');
             // Opcional: Scroll al primer error
            const firstError = formSimpleRegister.querySelector('.is-invalid');
            if(firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center'});

            return; 
        }
        console.log("Validación Frontend OK. Enviando a Django...");
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
                if (successMessageSpanReg) successMessageSpanReg.textContent = data.message || '¡Registro exitoso!'; // Mensaje Backend
                if (alertSuccessDivReg) alertSuccessDivReg.style.display = 'block';
                if (alertErrorDivReg) alertErrorDivReg.style.display = 'none';
                formSimpleRegister.reset();
                //setTimeout(() => { window.location.href = '/login/'; }, 3000);
            } else {
                if (errorMessageSpanReg) errorMessageSpanReg.textContent = data.message || 'Ocurrió un error inesperado.';
                if (alertErrorDivReg) alertErrorDivReg.style.display = 'block';
                if (alertSuccessDivReg) alertSuccessDivReg.style.display = 'none';
            }
        })
        .catch(error => {
            // Selecciona los elementos de alerta DENTRO del catch para asegurar que existan
    const alertErrorDiv = document.getElementById('alert-error');
    const errorMessageSpan = document.getElementById('error-message');
    const alertSuccessDiv = document.getElementById('alert-success'); // Para ocultarlo si estaba visible

    let generalErrorMessage = 'Ocurrió un error. Por favor, revisa el formulario.'; // Mensaje por defecto

    // Limpia errores frontend previos de los campos antes de mostrar los del backend
    const form = document.getElementById('form-simple-register'); // Necesitamos el form aquí
    if (form) {
        form.querySelectorAll('.form-group.error-field').forEach(el => {
            el.classList.remove('error-field');
            const errorMsgSpan = el.querySelector('.error-msg');
            if (errorMsgSpan) errorMsgSpan.textContent = '';
        });
    }

    // Comprueba si es un error 400 con datos de validación de Django
    if (error.status === 400 && error.data && error.data.errors) {
        const errors = error.data.errors;
        let firstErrorField = null;
        generalErrorMessage = 'Por favor, corrige los errores marcados.'; // Mensaje específico para errores de validación

        // Itera sobre los errores devueltos por Django (form.errors)
        for (const fieldName in errors) {
            const fieldErrors = errors[fieldName];
            // Construye el selector para encontrar el div.form-group correcto
            // Usa el atributo data-field-name que pusimos en el HTML
            const formGroup = form ? form.querySelector(`.form-group[data-field-name="${fieldName}"]`) : null;

            if (formGroup && fieldErrors.length > 0) {
                // Obtiene el input DENTRO del formGroup
                const input = formGroup.querySelector('.form-control');
                if (input) {
                    // Usa la función showFieldError para mostrar el error específico de Django
                    // Asegúrate que fieldErrors[0] tenga el mensaje (puede ser un string o un objeto con .message)
                    let message = fieldErrors[0].message ? fieldErrors[0].message : fieldErrors[0];
                    showFieldError(input, message);
                    if (!firstErrorField) firstErrorField = formGroup; // Guarda el primer campo con error
                }
            } else if (fieldName === '__all__' && fieldErrors.length > 0) {
                // Error general del formulario (no asociado a un campo específico)
                // Ejemplo: "El usuario ya existe" si no está ligado a 'username'
                generalErrorMessage = fieldErrors[0].message || fieldErrors[0];
            }
        }
        // Opcional: Hacer scroll al primer campo con error
        // if(firstErrorField) firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center'});

    } else if (error.data && error.data.message) {
        // Error del servidor (ej. 500) que envió un mensaje JSON
        generalErrorMessage = error.data.message;
    } else if (error.message) {
        // Error de red (ej. no se pudo conectar) u otro error de JavaScript
        generalErrorMessage = 'Ocurrió un error de conexión. Inténtalo de nuevo.';
    }

    // Muestra el mensaje de error general en la alerta roja
    if (errorMessageSpan) {
        errorMessageSpan.textContent = generalErrorMessage;
    }
    if (alertErrorDiv) {
        alertErrorDiv.style.display = 'block'; // Muestra la alerta general de error
    }
    // Asegúrate de que la alerta de éxito esté oculta
    if (alertSuccessDiv) {
        alertSuccessDiv.style.display = 'none';
    }
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
            let generalErrorMessage = 'Ocurrió un error inesperado.';
            if (error.status === 403 && error.data && error.data.message) {
                // Error específico: Email no verificado (o permiso denegado)
                generalErrorMessage = error.data.message; // Usa el mensaje del backend
                mensajeSimpleLoginDiv.textContent = generalErrorMessage;
            }
            else if (error.status === 400 && error.data && error.data.errors) {
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