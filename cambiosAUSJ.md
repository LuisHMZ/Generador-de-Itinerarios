# Cambios 21/10/25

## Creación de la Página de Inicio (/)

Se implementó la vista, URL y plantilla para una pág. home provisional, para corroborar funcionalidades

* **Vista (apps/itineraries/views.py):** Se creó la función home_view para renderizar la página. Se eligió la app itineraries.

* **URL (config/urls.py):** Se añadió una nueva ruta path('home/', ...,(name='home')) que apunta a la home_view

* **Plantilla (templates/itineraries/provisional_home.html):** Se creó el archivo HTML para la página de inicio provisional. La plantilla muestra contenido diferente si el usuario ha iniciado sesión o no.

## Cambio en la redirección de app/users

* **Login (apps/users/views.py):** Se  utiliza reverse('home') para obtener la URL real del provisional_home.html

* **Logout (apps/users/views.py):**Ahora, tras cerrar sesión, el usuario es redirigido a la página de login (simple_login) en lugar de a la raíz.