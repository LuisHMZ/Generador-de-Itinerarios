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

/**
 * Función auxiliar para encontrar el div.form-group del captcha
 */
function getRecaptchaGroup() {
    // Busca el div.form-group que tiene el data-field-name="captcha"
    return document.querySelector('.form-group[data-field-name="captcha"]');
}

/**
 * Esta función es llamada por la API de Google cuando el usuario
 * completa el reCAPTCHA exitosamente. (Nombre definido en forms.py)
 */
window.onRecaptchaSuccess = function(token) {
    console.log("reCAPTCHA validado exitosamente por el usuario.");
    const formGroup = getRecaptchaGroup();
    if (formGroup) {
        // Añade la clase 'success-field' para el borde verde
        formGroup.classList.add('success-field');
        formGroup.classList.remove('error-field'); // Quita el rojo si estaba
        
        // Limpia el mensaje de error (si lo había)
        const errorMsgSpan = formGroup.querySelector('.error-msg');
        if (errorMsgSpan) {
            errorMsgSpan.textContent = '';
            errorMsgSpan.style.display = 'none';
        }
    }
};

/**
 * Esta función es llamada por la API de Google si el token
 * del reCAPTCHA expira (el usuario esperó demasiado).
 */
window.onRecaptchaExpired = function() {
    console.warn("reCAPTCHA expirado.");
    const formGroup = getRecaptchaGroup();
    if (formGroup) {
        // Quita el verde y vuelve a poner el rojo
        formGroup.classList.remove('success-field');
        formGroup.classList.add('error-field');
        
        // Muestra un mensaje de error
        const errorMsgSpan = formGroup.querySelector('.error-msg');
        if (errorMsgSpan) {
            errorMsgSpan.textContent = 'El Captcha ha expirado, por favor verifícalo de nuevo.';
            errorMsgSpan.style.display = 'block';
        }
    }
};

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
                    const message = fieldErrors[0].message || fieldErrors[0];
                    
                    // --- ¡CAMBIO IMPORTANTE AQUÍ! ---
                    // Manejo especial para el campo 'captcha'
                    if (fieldName === 'captcha') {
                        const formGroup = formSimpleRegister.querySelector(`.form-group[data-field-name="captcha"]`);
                        if (formGroup) {
                            const errorMsgSpan = formGroup.querySelector('.error-msg');
                            if (errorMsgSpan) {
                                errorMsgSpan.textContent = message; // Muestra "Este campo es requerido."
                                errorMsgSpan.style.display = 'block';
                            }
                            formGroup.classList.add('error-field'); // Opcional: estilizar el div
                            if (!firstErrorField) firstErrorField = formGroup;
                        }
                    } 
                    // Manejo de errores no ligados a un campo (ej. "__all__")
                    else if (fieldName === '__all__') {
                        generalErrorMessage = message;
                    } 
                    // Manejo normal para todos los demás campos (username, password, etc.)
                    else {
                        const formGroup = formSimpleRegister.querySelector(`.form-group[data-field-name="${fieldName}"]`);
                        if (formGroup) {
                            const input = formGroup.querySelector('.form-control');
                            if (input) {
                                showFieldError(input, message); // Usa la función existente
                                if (!firstErrorField) firstErrorField = formGroup;
                            }
                        }
                    }
                    // --- FIN DEL CAMBIO ---
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
const formSimpleLogin = document.getElementById('form-simple-login'); 
const alertSuccessDivLog = document.getElementById('alert-success-login'); 
const successMessageSpanLog = document.getElementById('success-message-login'); 
const alertErrorDivLog = document.getElementById('alert-error-login'); 
const errorMessageSpanLog = document.getElementById('error-message-login'); 

// --- Funciones de validación SÓLO para el login (ligeras) ---

/**
 * Muestra/oculta un mensaje de error debajo de un campo de formulario.
 * @param {HTMLElement} input - El elemento input.
 * @param {string} message - El mensaje de error (o "" para limpiar).
 */
function showLoginFieldError(input, message) {
    const formGroup = input.closest('.form-group');
    if (!formGroup) return;
    const errorMsgSpan = formGroup.querySelector('.error-msg');

    if (message) {
        formGroup.classList.add('error-field');
        if (errorMsgSpan) {
            errorMsgSpan.textContent = message;
            errorMsgSpan.style.display = 'block';
        }
    } else {
        formGroup.classList.remove('error-field');
        if (errorMsgSpan) {
            errorMsgSpan.textContent = '';
            errorMsgSpan.style.display = 'none';
        }
    }
}

function validarCampoLogin(input) {
    let mensaje = '';
    const value = input.value.trim();
    const id = input.id;

    // 1. Requerido
    if (!value) {
        mensaje = 'Este campo es requerido.';
    } 
    // 2. Formato (Validación súper básica)
    else if (id === 'id_username' && value.includes(' ') && value.includes('@')) {
        // Asumimos que si tiene @ es un email, y los emails no tienen espacios
        mensaje = 'Correo inválido, no debe contener espacios.';
    } else if (id === 'id_username' && !value.includes('@') && value.includes(' ')) {
        // Asumimos que es un username, y los usernames no tienen espacios
        mensaje = 'Usuario inválido, no debe contener espacios.';
    }

    showLoginFieldError(input, mensaje);
    return mensaje === ''; // Devuelve true si es válido (sin mensaje)
}

/**
 * Valida el formulario de login completo ANTES de enviarlo.
 * @returns {boolean} - true si todo el formulario es válido, false si no.
 */
function validarFormularioLoginCompleto() {
    if (!formSimpleLogin) return false;
    // Selecciona solo los inputs requeridos
    const inputs = formSimpleLogin.querySelectorAll('.form-control[required]'); 
    let formValid = true;

    // Oculta alertas generales al iniciar validación
    if (alertErrorDivLog) alertErrorDivLog.style.display = 'none';
    if (errorMessageSpanLog) errorMessageSpanLog.textContent = '';

    inputs.forEach(input => {
        if (!validarCampoLogin(input)) {
            formValid = false; // Si CUALQUIER campo falla, el form no es válido
        }
    });

    if (!formValid) {
         if (errorMessageSpanLog && alertErrorDivLog) {
             errorMessageSpanLog.textContent = 'Por favor, corrige los errores marcados.';
             alertErrorDivLog.style.display = 'block'; // Muestra la alerta general
         }
        // Opcional: Hacer scroll al primer error
        const firstError = formSimpleLogin.querySelector('.error-field');
        if(firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center'});
    }

    return formValid; // true si OK, false si hubo error frontend
}


if (formSimpleLogin && alertSuccessDivLog && alertErrorDivLog && errorMessageSpanLog) {
    formSimpleLogin.addEventListener('submit', function(event) {
        event.preventDefault();

        const isFrontendValid = validarFormularioLoginCompleto();
        
        if (!isFrontendValid) {
            console.log("Validación Frontend (Login) falló. Envío a Django cancelado.");
            return; // Detiene la función si hay errores locales (ej. campos vacíos)
        }
        console.log("Validación Frontend (Login) OK. Enviando a Django...");

        // Oculta alertas (por si la validación las mostró y se corrigió rápido)
        alertSuccessDivLog.style.display = 'none';
        alertErrorDivLog.style.display = 'none';

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
                successMessageSpanLog.textContent = data.message || '¡Inicio de sesión exitoso!';
                alertSuccessDivLog.style.display = 'block'; // Muestra alerta verde
                // Redirige después del login exitoso
                //window.location.href = data.redirect_url || '/'; // Redirige a la URL (home)
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/';
                }, 2000);
            } else if (data.status === 'info') {
                 // Caso: Ya estaba logueado
                successMessageSpanLog.textContent = data.message || 'Ya has iniciado sesión.';
                alertSuccessDivLog.style.display = 'block';
                setTimeout(() => { window.location.href = data.redirect_url || '/'; }, 1500);
            } else {
                 // Respuesta 200 pero con status != 'success' (raro)
                errorMessageSpanLog.textContent = data.message || 'Ocurrió un error inesperado.';
                 alertErrorDivLog.style.display = 'block'; // Muestra alerta roja
            }
        })
        .catch(error => {
            console.error('Error en el inicio de sesión (Respuesta Django):', error.data || error.message || error);
            let generalErrorMessage = 'Ocurrió un error inesperado.';
            if (error.status === 403 && error.data && error.data.message) {
                // Error 403: Email no verificado
                generalErrorMessage = error.data.message; // "Debes verificar tu correo..."
            
            } else if (error.status === 400 && error.data && error.data.errors) {
                // Error 400: Validación de Django falló (ej. credenciales incorrectas)
                if (error.data.errors.__all__) { // Error general de AuthenticationForm
                    generalErrorMessage = error.data.errors.__all__[0].message || error.data.errors.__all__[0];
                
                } else { // Errores por campo (raro en login, pero por si acaso)
                     generalErrorMessage = 'Por favor, revisa los campos.';
                     // Muestra errores específicos bajo los campos
                     for (const fieldName in error.data.errors) {
                         const input = formSimpleLogin.querySelector(`#id_${fieldName}`);
                         if (input) {
                            showLoginFieldError(input, error.data.errors[fieldName][0]);
                         }
                     }
                }
            } else if (error.data && error.data.message) {
                generalErrorMessage = error.data.message;
            } else {
                 generalErrorMessage = 'Error de conexión o credenciales incorrectas.';
            }

            // Muestra el mensaje de error general en la alerta roja
            errorMessageSpanLog.textContent = generalErrorMessage;
            alertErrorDivLog.style.display = 'block';
        });
    });
} else {
    if (!formSimpleLogin) console.error("Formulario con ID 'form-simple-login' no encontrado.");
    if (!mensajeSimpleLoginDiv) console.error("Div con ID 'mensaje-login' no encontrado.");
}