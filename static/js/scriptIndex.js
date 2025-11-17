document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('form-simple-register');
    const alertSuccess = document.getElementById('alert-success');
    const alertError = document.getElementById('alert-error');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    const passwordRequirements = document.querySelectorAll('#password-requirements li');
    const passwordInput = document.getElementById('id_password1');
    const confirmPasswordInput = document.getElementById('id_password2');

    // === FUNCIONES GENERALES ===
    function showAlert(alertElement, message) {
        alertElement.style.display = 'block';
        if (alertElement === alertSuccess) {
            successMessage.textContent = message;
        } else {
            errorMessage.textContent = message;
        }
        setTimeout(() => alertElement.style.display = 'none', 5000);
    }

    // === ACTIVAR / DESACTIVAR BOTÓN SEGÚN CHECKBOX ===
const consentCheckbox = document.getElementById('id_consent');
const submitBtn = document.getElementById('submit-btn');

consentCheckbox.addEventListener('change', function () {
    submitBtn.disabled = !this.checked;
});


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

    function validateName(input) {
    const value = input.value.trim();
    // Expresión regular similar a la de Python (simplificada sin acentos directos)
    // Permite letras Unicode, espacios, apóstrofes, guiones
    const nameRegex = /^[a-zA-Z\u00C0-\u017F\s'-]+$/;
    // Si el campo es requerido Y está vacío
    if (input.required && !value) {
        return 'Este campo es obligatorio.';
    }
    if (value && !nameRegex.test(value)) {
        return 'Solo letras, espacios y guiones.';
    }
    return ''; 
}
    function validateEmail(input) {
        const value = input.value.trim();
        if (!value) return 'El correo es obligatorio y debe contener un "@" y un dominio.';
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Ingresa un correo válido.';
        return '';
    }

    function validatePassword(input) {
        const value = input.value;
        if (!value) return 'La contraseña es obligatoria.';
        if (value.length < 8) return 'Debe tener al menos 8 caracteres.';
        if (!/[A-Z]/.test(value)) return 'Debe incluir al menos una letra mayúscula.';
        if (!/[a-z]/.test(value)) return 'Debe incluir al menos una letra minúscula.';
        if (!/[0-9]/.test(value)) return 'Debe incluir al menos un número.';
        if (!/[^A-Za-z0-9]/.test(value)) return 'Debe incluir al menos un símbolo especial (ej. !@#$%).';
        return '';
    }

    passwordInput.addEventListener('input', function() {
        const value = passwordInput.value;

        const conditions = [
            /.{8,}/.test(value),           // Longitud mínima
            /[A-Z]/.test(value),            // Mayúscula
            /[a-z]/.test(value),            // Minúscula
            /[0-9]/.test(value),            // Número
            /[^A-Za-z0-9]/.test(value)      // Símbolo especial
        ];

        passwordRequirements.forEach((item, index) => {
            const icon = item.querySelector('i');
            if (conditions[index]) {
                item.classList.add('valid');
                item.classList.remove('invalid');
                icon.classList.remove('fa-times', 'text-danger');
                icon.classList.add('fa-check', 'text-success');
            } else {
                item.classList.add('invalid');
                item.classList.remove('valid');
                icon.classList.remove('fa-check', 'text-success');
                icon.classList.add('fa-times', 'text-danger');
            }
        });
    });

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
        const id = input.id;
        let validatorFunction = '';

        if (input.id === 'id_email') mensaje = validateEmail(input);
        else if (input.id === 'id_password1') mensaje = validatePassword(input);
        else if (input.id === 'id_password2') mensaje = validateConfirmPassword(input);
        else if (input.id === 'id_birth_date') mensaje = validateAge(input);
        else if (input.id === 'id_first_name' || input.id === 'id_last_name') mensaje = validateName(input);
        else mensaje = validateRequired(input);

        showFieldError(input, mensaje);
    }

    // === ASIGNAR VALIDACIÓN EN TIEMPO REAL A TODOS LOS CAMPOS ===
    const inputs = form.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('input', () => validarCampo(input));
        input.addEventListener('blur', () => validarCampo(input)); // también al perder el foco
    });

    // === VALIDAR TODO AL ENVIAR ===
    /* form.addEventListener('submit', function(e) {
        e.preventDefault();
        alertSuccess.style.display = 'none';
        alertError.style.display = 'none';

        let formValid = true;
        inputs.forEach(input => {
            validarCampo(input);
            if (input.classList.contains('is-invalid')) formValid = false;
        });

        if (!formValid) {
            showAlert(alertError, 'Por favor, corrige los errores antes de continuar.');
            return;
        }

        showAlert(alertSuccess, '¡Registro exitoso! Bienvenido a MexTur.');
        setTimeout(() => form.reset(), 2000);
        form.querySelectorAll('.is-valid').forEach(i => i.classList.remove('is-valid'));
    }); */

    // === MOSTRAR / OCULTAR CONTRASEÑAS ===
    const togglePassword = document.getElementById('toggle-password');
    const toggleConfirmPassword = document.getElementById('toggle-confirm-password');

    togglePassword.addEventListener('click', function() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    });

    toggleConfirmPassword.addEventListener('click', function() {
        const type = confirmPasswordInput.type === 'password' ? 'text' : 'password';
        confirmPasswordInput.type = type;
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    });
});
document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('form-password-reset-key');
    if (!form) {
                console.log("Formulario 'form-password-reset-key' no encontrado. Script detenido.");
                return;
            }
            console.log("Formulario encontrado. Adjuntando listeners...");
    const alertSuccess = document.getElementById('alert-success-login');
    const alertError = document.getElementById('alert-error-login');
    const successMessage = document.getElementById('success-message-login');
    const errorMessage = document.getElementById('error-message-login');
    const passwordRequirements = document.querySelectorAll('#password-requirements li');
    const passwordInput = document.getElementById('id_password1');
    const confirmPasswordInput = document.getElementById('id_password2');


    // === FUNCIONES GENERALES ===
    function showAlert(alertElement, message) {
        alertElement.style.display = 'block';
        if (alertElement === alertSuccess) {
            successMessage.textContent = message;
        } else {
            errorMessage.textContent = message;
        }
        setTimeout(() => alertElement.style.display = 'none', 5000);
    }

    function showFieldError(input, message) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return; // Salir si no se encuentra el form-group
        
        const errorMsg = formGroup.querySelector('.error-msg');
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


     // --- VALIDAR CONTRASEÑA ---
    function validatePassword(input) {
        const value = input.value;
        if (!value) return 'La contraseña es obligatoria.';
        if (value.length < 8) return 'Debe tener al menos 8 caracteres.';
        if (!/[A-Z]/.test(value)) return 'Debe incluir al menos una letra mayúscula.';
        if (!/[a-z]/.test(value)) return 'Debe incluir al menos una letra minúscula.';
        if (!/[0-9]/.test(value)) return 'Debe incluir al menos un número.';
        if (!/[^A-Za-z0-9]/.test(value)) return 'Debe incluir al menos un símbolo especial (ej. !@#$%).';
        return '';
    }

    function validateConfirmPassword() {
        const pass = document.getElementById('id_password1').value;
        const confirm = document.getElementById('id_password2').value;
        if (!confirm) return 'Confirma tu contraseña.';
        if (pass !== confirm) return 'Las contraseñas no coinciden.';
        return '';
    }

    // === VALIDAR CAMPO EN TIEMPO REAL ===
    function validarCampo(input) {
        let mensaje = '';
        const id = input.id;
        let validatorFunction = '';

        if (input.id === 'id_email') mensaje = validateEmail(input);
        else if (input.id === 'id_password1') mensaje = validatePassword(input);
        else if (input.id === 'id_password2') mensaje = validateConfirmPassword(input);
        else if (input.id === 'id_birth_date') mensaje = validateAge(input);
        else if (input.id === 'id_first_name' || input.id === 'id_last_name') mensaje = validateName(input);
        else mensaje = validateRequired(input);

        showFieldError(input, mensaje);
    }

    // === ASIGNAR VALIDACIÓN EN TIEMPO REAL A TODOS LOS CAMPOS ===
    const inputs = form.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('input', () => validarCampo(input));
        input.addEventListener('blur', () => validarCampo(input)); // también al perder el foco
    });

    passwordInput.addEventListener('input', function() {
        const value = passwordInput.value;

        const conditions = [
            /.{8,}/.test(value),           // Longitud mínima
            /[A-Z]/.test(value),            // Mayúscula
            /[a-z]/.test(value),            // Minúscula
            /[0-9]/.test(value),            // Número
            /[^A-Za-z0-9]/.test(value)      // Símbolo especial
        ];

        passwordRequirements.forEach((item, index) => {
            const icon = item.querySelector('i');
            if (conditions[index]) {
                item.classList.add('valid');
                item.classList.remove('invalid');
                icon.classList.remove('fa-times', 'text-danger');
                icon.classList.add('fa-check', 'text-success');
            } else {
                item.classList.add('invalid');
                item.classList.remove('valid');
                icon.classList.remove('fa-check', 'text-success');
                icon.classList.add('fa-times', 'text-danger');
            }
        });
    });

    form.addEventListener('submit', function(e) {
                console.log("Evento submit capturado."); 
                
                // Oculta alertas de envíos anteriores
                if (alertError) alertError.style.display = 'none';
                if (errorMessage) errorMessage.textContent = '';
                
                // Revalida todo antes de enviar
                const passError = validatePassword(passwordInput);
                const confirmError = validateConfirmPassword();
                
                // Muestra los errores (si los hay)
                showFieldError(passwordInput, passError);
                showFieldError(confirmPasswordInput, confirmError);

                // Si hay algún error de frontend, DETIENE el envío
                if (passError || confirmError) {
                    console.log("Errores de frontend encontrados. Envío detenido."); // Log
                    e.preventDefault(); // ¡Detiene la recarga de la página!
                    
                    if (errorMessage) errorMessage.textContent = 'Por favor, corrige los errores marcados.';
                    if (alertError) alertError.style.display = 'block';
                }else{
                // Si no hay errores (passError y confirmError están vacíos),
                // el script termina, e.preventDefault() NO se llama,
                // y el formulario se envía al servidor (Django) para la validación final.
                console.log("Validación Frontend OK. Enviando a Django...");
                }
            });


});
// === CONTROL DEL FORMULARIO DE RECUPERAR CONTRASEÑA ===
document.addEventListener('DOMContentLoaded', function () {
    const formRecuperar = document.getElementById('form-recuperar');
    if (!formRecuperar) return;

    const alertSuccessModal = document.getElementById('alert-success-modal');
    const alertErrorModal = document.getElementById('alert-error-modal');
    const successMsgModal = document.getElementById('success-message-modal');
    const errorMsgModal = document.getElementById('error-message-modal');
    const emailInput = document.getElementById('recuperarEmail');

    function showAlertModal(alertElement, message) {
        alertElement.style.display = 'block';
        if (alertElement === alertSuccessModal) {
            successMsgModal.textContent = message;
        } else {
            errorMsgModal.textContent = message;
        }
        setTimeout(() => alertElement.style.display = 'none', 4000);
    }

    formRecuperar.addEventListener('submit', function (e) {
        e.preventDefault();

        const emailValue = emailInput.value.trim();
        if (!emailValue) {
            showAlertModal(alertErrorModal, 'Por favor, ingresa tu correo electrónico.');
            return;
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue)) {
            showAlertModal(alertErrorModal, 'El correo ingresado no es válido.');
            return;
        }

        // Simula envío exitoso
        showAlertModal(alertSuccessModal, 'Se ha enviado un enlace para restablecer tu contraseña.');
        formRecuperar.reset();
    });
});
// === CONTROL DEL FORMULARIO DE INICIO DE SESIÓN ===
document.addEventListener('DOMContentLoaded', function () {
    const formLogin = document.getElementById('form-login');
    if (!formLogin) return;

    const alertSuccess = document.getElementById('alert-success-login');
    const alertError = document.getElementById('alert-error-login');
    const successMsg = document.getElementById('success-message-login');
    const errorMsg = document.getElementById('error-message-login');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    function showAlert(alertElement, message) {
        alertElement.style.display = 'block';
        if (alertElement === alertSuccess) {
            successMsg.textContent = message;
        } else {
            errorMsg.textContent = message;
        }
        setTimeout(() => alertElement.style.display = 'none', 4000);
    }

    formLogin.addEventListener('submit', function (e) {
        e.preventDefault();

        const emailValue = emailInput.value.trim();
        const passwordValue = passwordInput.value.trim();

        // Validaciones básicas
        if (!emailValue || !passwordValue) {
            showAlert(alertError, 'Por favor, completa todos los campos.');
            return;
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue)) {
            showAlert(alertError, 'El correo ingresado no es válido.');
            return;
        }

    });
});
