# MexTur
* Proyecto integrado con SonarCloud para análisis de calidad.

## Tecnologías Principales

* **Backend:** Python 3.12+, Django 5+
* **Base de Datos:** PostgreSQL
* **Frontend:** Plantillas de Django (HTML), CSS, JavaScript
* **Servidor de Desarrollo:** Windows / PowerShell

---

## Configuración Universal del Entorno

Sigue estos pasos para lograr ejecutar el servidor del proyecto.

### 1. Prerrequisitos

Asegúrate de tener instalado lo siguiente en tu sistema:
* [Git](https://git-scm.com/)
* [Python](https://www.python.org/downloads/windows/) (Asegúrate de marcar "Add Python to PATH" durante la instalación).
* [PostgreSQL y pgAdmin](https://www.postgresql.org/download/windows/) (El instalador de PostgreSQL ya incluye pgAdmin).

### 2. Configuración Inicial del Proyecto

1.  **Clona el Repositorio:** Abre una terminal (PowerShell o CMD) y clona el proyecto.
    ```bash
    git clone [Repo en github]
    cd [nombre del proyecto]
    ```

2.  **Crea y Activa el Entorno Virtual:** Esto aísla las dependencias de Python.
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
    Tu terminal ahora debe mostrar `(venv)` al principio de la línea.

3.  **Instala las Dependencias:** Instala todas las librerías de Python (Django, Pillow, etc.).
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuración de la Base de Datos Local

1.  **Abre pgAdmin 4**
2.  **Conéctate a tu servidor PostgreSQL local.** 
3.  Haz clic derecho en **"Databases"** → **"Create"** → **"Database..."**.
4.  Nombra la base de datos exactamente: **`MexTur`**. Si quieres usar otro nombre deberás modificarlo en el archivo config\settings\local.py
5.  Haz clic en **"Save"**.

### 4. Configuración de Variables de Entorno

1.  En la raíz del proyecto, busca un archivo llamado **`.env.example`**.
2.  **Crea una copia** de este archivo en la misma carpeta y renombra la copia a **`.env`**.
3.  **Abre tu nuevo archivo `.env`** y rellena tus credenciales locales.

    ```env
    # Clave secreta de Django
    SECRET_KEY='tu-clave-secreta-unica-aqui'
    
    # Configuración de la Base de Datos Local
    DB_NAME='MexTur' # o el nombre de la BD que creaste
    DB_USER='postgres'
    DB_PASSWORD='tu_contraseña_local_de_postgres'
    DB_HOST='localhost'
    DB_PORT='5432'
    ```
4. **Genera tu propia SECRET_KEY.** Esto lo harán una única vez por persona, pues genera una llave para sesiones y encriptaciones para su computadora. NO generen llave para producción, eso se reealizará una vez despleguemos el proyecto.
    ```bash
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```
Copien y peguen el resultado en la SECRET_KEY del archivo .env

### 5. Levantar la Base de Datos por Primera Vez

1.  **Ejecuta las Migraciones:** Este comando crea todas las tablas en la base de datos `MexTur` gracias a las credenciales configuradas anteriormente.
    ```bash
    python manage.py migrate
    ```

2.  **Crea un Superusuario Local:** Necesario para acceder al panel de administración.
    ```bash
    python manage.py createsuperuser
    ```

---

## Flujo de Trabajo para TODOS

Proceso para trabajar sobre el proyecto

1.  **Activa el Entorno Virtual en la consola:**
    ```bash
    .\venv\Scripts\activate
    ```

2.  **Ejecuta el Servidor de Desarrollo:**
    ```bash
    python manage.py runserver
    ```

3.  **Abre la Aplicación:**
    * Visita `http://127.0.0.1:8000/` en tu navegador para ver el sitio.
    * Visita `http://127.0.0.1:8000/admin/` para el panel de administración.

---

## ¿En qué carpetas trabajo?

Aquí se muestran la distribuciones de las carpetas

* **Equipo de Backend:**
    * `apps/` (`models.py`, `views.py`, `serializers.py`, etc.). Hasta ahora solo están las apps que representan las tablas de la base de datos
    * `config/` (para los `settings.py` y `urls.py` principales). El archivo settings.py se dividió en 3: un archivo base `base.py`, `local.py` y `production.py`. El archivo base pues es la base, y los otros dos tienen configuraciones distintas por su entorno de uso. Para trabajo local unicamente modificar el archivo `local.py`
    * Debe crearse una carpeta "media" para el desarrollo local, es a donde irán las fotos que suban los usuarios. Para producción se conectará con supabas storage

* **Equipo de Frontend:**
    * `templates/` (`.html`)
    * `static/` (`.css`, `.js` e imágenes)

## Consideración: El panel de administración.
Este panel no reemplaza al que desarrollaremos para MexTur, está más enfocado en administrar la base de datos: usuarios registrados, usuarios autenticades, sesiones, datos, etc. Pueden usarlo localmente para generar datos de prueba sin problema.

### 6. Scripts de configuración
El siguiente script carga las categorías elegidas por el equipo para los lugares turisticos.
    ```bash
    python manage.py seed_categories.py
    ```

El siguiente script descarga las imágenes de los lugares turisticos en la BD que pudieran no haber sido descargadas anteriormente:
    ```bash
    python manage.py download_missing_photos [--force] [--limit <int:limit>]
    ```