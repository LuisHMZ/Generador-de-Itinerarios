# Cambios 21/10/25

## Creación de la Página de Inicio (/)

Se implementó la vista, URL y plantilla para una pág. home provisional, para corroborar funcionalidades

* **Vista (apps/itineraries/views.py):** Se creó la función home_view para renderizar la página. Se eligió la app itineraries.

* **URL (config/urls.py):** Se añadió una nueva ruta path('home/', ...,(name='home')) que apunta a la home_view

* **Plantilla (templates/itineraries/provisional_home.html):** Se creó el archivo HTML para la página de inicio provisional. La plantilla muestra contenido diferente si el usuario ha iniciado sesión o no.

## Cambio en la redirección de app/users

* **Login (apps/users/views.py):** Se  utiliza reverse('home') para obtener la URL real del provisional_home.html

* **Logout (apps/users/views.py):**Ahora, tras cerrar sesión, el usuario es redirigido a la página de login (simple_login) en lugar de a la raíz.

# Cambios EMAIL

(config/settings/base.py):

# Configuración del Backend de Email (para desarrollo)
# Mostrará los emails en la consola en lugar de enviarlos realmente.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_BACKEND: Esta variable de configuración le dice a Django qué "motor" o sistema debe usar para manejar los correos electrónicos.

'django.core.mail.backends.console.EmailBackend': Al establecer este valor, le indicamos a Django que, en lugar de conectarse a un servidor SMTP (como Gmail o SendGrid), simplemente tome el contenido completo del correo (cabeceras, asunto, cuerpo) y lo imprima en la salida estándar (la terminal donde corre runserver).

# Cambios 18/11/25
Se ha integrado Google reCAPTCHA v2 en el formulario de registro para evitar bots. Para que el proyecto funcione en tu entorno local, debes seguir estos pasos:

1. Actualizar el Código y Dependencias

Baja los últimos cambios de la rama y actualiza tus librerías de Python (se añadió django-recaptcha).

git pull origin feature/email-verification-fix
pip install -r requirements.txt


2. Configurar las Variables de Entorno (.env)

El proyecto fallará si no tienes las claves de Google configuradas. Abre tu archivo .env local y añade estas claves de prueba de Google (son seguras y funcionan en localhost para todos):

# --- Claves de Google reCAPTCHA v2 (Entorno de Pruebas) ---
# Estas claves son genéricas de Google para desarrollo. 
# NO usar en producción.
RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
