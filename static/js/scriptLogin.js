document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('login-form');
    const alertSuccess = document.getElementById('alert-success');
    const alertError = document.getElementById('alert-error');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');

    // === Función para mostrar alertas ===
    function showAlert(alertElement, message) {
        alertElement.style.display = 'block';
        if (alertElement === alertSuccess) {
            successMessage.textContent = message;
        } else {
            errorMessage.textContent = message;
        }
        setTimeout(() => alertElement.style.display = 'none', 5000);
    }

    // === Mostrar errores debajo de campos ===
    function showFieldError(input, message) {
        const errorMsg = input.parentElement.querySelector('.error-msg');
        if (message) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            errorMsg.textContent = message;
            errorMsg.style.display = 'block';
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            errorMsg.textContent = '';
            errorMsg.style.display = 'none';
        }
    }

    // === Validaciones ===
    function validateEmail(input) {
        const value = input.value.trim();
        if (!value) return 'El correo es obligatorio.';
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Ingresa un correo válido.';
        return '';
    }

    function validatePassword(input) {
        if (!input.value) return 'La contraseña es obligatoria.';
        if (input.value.length < 6) return 'Debe tener al menos 6 caracteres.';
        return '';
    }

    // === Validar campo individual ===
    function validarCampo(input) {
        let mensaje = '';
        if (input.id === 'correo-input') mensaje = validateEmail(input);
        else if (input.id === 'contraseña-input') mensaje = validatePassword(input);
        showFieldError(input, mensaje);
    }

    // === Escuchar cambios en los inputs ===
    const inputs = form.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('input', () => validarCampo(input));
        input.addEventListener('blur', () => validarCampo(input));
    });

    // === Envío del formulario ===
    form.addEventListener('submit', function(e) {
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

        showAlert(alertSuccess, '¡Inicio de sesión exitoso! Bienvenido de nuevo a MexTur.');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 2000);
    });

    // === Mostrar / Ocultar contraseña ===
    const togglePassword = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('contraseña-input');

    togglePassword.addEventListener('click', function() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    });
});
