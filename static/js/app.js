const form = document.querySelector('form');
const nombre_input = document.querySelector('#nombre-input');
const apellido_input = document.querySelector('#apellido-input');
const fecha_nacimiento_input = document.querySelector('#fecha-nacimiento-input');
const correo_input = document.querySelector('#correo-input');
const contraseña_input = document.querySelector('#contraseña-input');
const confirmar_contraseña_input = document.querySelector('#confirmar-contraseña-input');
const mensaje_errores = document.querySelector('#mensaje-errores');

form.addEventListener('submit', (e) => {
    let errores = []

    if(nombre_input) {
        errores = obtenerErroresSignup(nombre_input.value, apellido_input.value, fecha_nacimiento_input.value, correo_input.value, contraseña_input.value, confirmar_contraseña_input.value);
    } else {
        errores = obtenerErroresLogin(correo_input.value, contraseña_input.value);
    }

    if(errores.length > 0) {
        e.preventDefault();
        mensaje_errores.innerText = errores.join("\n");
    }
})


function obtenerErroresSignup(nombre, apellido, fechaNacimiento, correo, contraseña, confirmarContraseña) {
    let errores = []

    if(nombre === '' || nombre == null) {
        errores.push('Coloca un nombre')
        nombre_input.parentElement.classList.add('error')
    }
    if(apellido === '' || apellido == null) {
        errores.push('Coloca un apellido')
        apellido_input.parentElement.classList.add('error')
    }
    if(fechaNacimiento === '' || fechaNacimiento == null) {
        errores.push('Coloca una fecha de nacimiento')
        fecha_nacimiento_input.parentElement.classList.add('error')
    }
    if(correo === '' || correo == null) {
        errores.push('Coloca un correo')
        correo_input.parentElement.classList.add('error')
    }
    if(contraseña === '' || contraseña == null) {
        errores.push('Coloca una contraseña')
        contraseña_input.parentElement.classList.add('error')
    }
    if(confirmarContraseña !== contraseña) {
        errores.push('La constraseña no es la misma')
        contraseña_input.parentElement.classList.add('error')
        confirmar_contraseña_input.parentElement.classList.add('error')
    }

    return errores;
}

function obtenerErroresLogin(correo, contraseña) {
    let errores = []

    if(correo === '' || correo == null) {
        errores.push('Coloca un correo')
        correo_input.parentElement.classList.add('error')
    }
    if(contraseña === '' || contraseña == null) {
        errores.push('Coloca una contraseña')
        contraseña_input.parentElement.classList.add('error')

    return errores;
    }
}

const inputs = [nombre_input, apellido_input, fecha_nacimiento_input, correo_input, contraseña_input, confirmar_contraseña_input].filter(input => input != null)

inputs.forEach(input => {
    input.addEventListener('input', () => {
        if(input.parentElement.classList.contains('error')) {
            input.parentElement.classList.remove('error')
            mensaje_errores.innerText = ''
        }
    })
})