//static/js/headerFooter.js

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
const csrftoken = getCookie('csrftoken');


document.addEventListener('DOMContentLoaded', function () {
    
    // --- 1. LECTURA DE URLs DE DJANGO (Variables dinámicas) ---
    const logoutUrl = document.body.dataset.logoutUrl || '#';
    const homeUrl = '/home/'; 
    const profileUrl = 'perfil.html'; 
    const staticUrlBase = '/static/img/'; // Ruta base para imágenes
    const apiNotificationsUrl = '/api/alertas/'; // ¡URL de la API que creamos!
    // --- FIN LECTURA DE URLs ---

    const headerHtml = `
        <header class="header-global">
            <div class="header-contenido">
                <a href="${homeUrl}" class="logo-link"> 
                    <img src="${staticUrlBase}logo.png" alt="Logo MexTur" class="logo-img">
                    <div class="logo-texto"><span class="logo-mex">MEX</span><span class="logo-tur">TUR</span></div>
                </a>
                <div class="header-titulo"><h5 class="header-titulo-text"></h5></div>
                <div class="header-actions">
                    <a href="${profileUrl}" class="btn btn-profile" title="Mi Perfil">
                        <i class="bi bi-person-fill"></i>
                    </a>
                    <div class="notification-wrapper">
                        <button class="btn btn-notification" id="bell-button" type="button" title="Notificaciones">
                            <i class="bi bi-bell-fill"></i>
                            <span class="notification-count" id="notification-badge-count" style="display: none;">0</span>
                        </button>
                    </div>
                    <div class="dropdown">
                        <button class="btn btn-menu" type="button" id="dropdownMenuButton" data-bs-toggle="dropdown" aria-expanded="false" title="Menú">
                            <i class="bi bi-list"></i>
                        </button>
                        <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                            <li><a class="dropdown-item" href="${profileUrl}"><i class="bi bi-person me-2"></i>Mi Perfil</a></li>
                            <li><a class="dropdown-item" href="#"><i class="bi bi-geo-alt me-2"></i>Itinerario</a></li>
                            <li><a class="dropdown-item" href="#"><i class="bi bi-envelope me-2"></i>Mensajes</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="${logoutUrl}"><i class="bi bi-box-arrow-right me-2"></i>Cerrar sesión</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </header>
    `;

    const footerHtml = `
        <footer class="footer-global">
            <div class="footer-contenido">
                <div class="footer-seccion footer-logo-tagline">
                    <h3 class="footer-logo"><span class="footer-logo-mex">MEX</span><span class="footer-logo-tur">TUR</span></h3>
                    <p>Explora los destinos más increíbles de México con nosotros</p>
                </div>
                <div class="footer-seccion footer-enlaces">
                    <h3>Enlaces</h3>
                    <nav>
                        <a href="${homeUrl}">Inicio</a>
                        <a href="#">Destinos</a>
                        <a href="#">Paquetes</a>
                    </nav>
                </div>
                <div class="footer-seccion footer-contacto">
                    <h3>Contacto</h3>
                    <p>+525572345678</p>
                    <p>info@mextur.com</p>
                    <p>Ciudad de México</p>
                </div>
            </div>
            <div class="copyright">© 2025 MexTur. Todos los derechos reservados</div>
        </footer>
    `;

    // 2. Inyectamos el HTML
    const headerContainer = document.getElementById('site-header');
    const footerContainer = document.getElementById('site-footer');

    if (headerContainer) headerContainer.innerHTML = headerHtml;
    if (footerContainer) footerContainer.innerHTML = footerHtml;

    // --- (Tu JS de títulos original) ---
    const titleMap = {
        'index.html': 'Inicio',
        'feed.html': 'Feed inicio',
        'home': 'Feed Social',
        'perfil.html': 'Mi Perfil',
        'pagina-social.html': 'Mi espacio',
        'amigos.html': 'Mis Amigos',
        'solicitudes.html': 'Solicitudes de amistad',
        'registro.html': 'Registrarse',
        'Registro.html': 'Registrarse',
        'log.html': 'Iniciar sesión',
        'recuperar.html': 'Recuperar contraseña',
        'editar-itinerario.html': 'Editar Itinerario',
        'ver-itinerario-final.html': 'Mi Itinerario',
        'amigos.html': 'Mis Amigos'
    };
    function computeHeaderTitle() {
        const path = (location.pathname || '').split('/').filter(Boolean).pop() || 'home';
        if (path && titleMap[path]) return titleMap[path];
        const docTitle = (document.title || '').split(' - ')[0].trim();
        if (docTitle) return docTitle;
        return 'MexTur';
    }
    function setHeaderTitle(text) {
        const els = document.querySelectorAll('.header-titulo-text');
        els.forEach(el => {
            el.textContent = text;
        });
    }
    setHeaderTitle(computeHeaderTitle());
    const titleObserver = new MutationObserver(() => {
        setHeaderTitle(computeHeaderTitle());
    });
    const titleEl = document.querySelector('title');
    if (titleEl) {
        titleObserver.observe(titleEl, { childList: true });
    }
    // --- (Fin de JS de títulos) ---


    // ------------------------------------
    // --- LÓGICA DE NOTIFICACIONES REALES (CORREGIDA) ---
    // ------------------------------------
    
    // 3. Obtenemos los elementos DESPUÉS de inyectarlos
    const notificationsList = document.getElementById('notifications-list');
    const countElement = document.getElementById('notification-badge-count');
    const modalElement = document.getElementById('notificationsModal'); 
    const bellButton = document.getElementById('bell-button'); // El botón que inyectamos

    // 4. Creamos la instancia del Modal y asignamos el clic manualmente
    if (modalElement && bellButton) {
        const notificationModal = new bootstrap.Modal(modalElement); 
        
        // --- ▼▼▼ LÓGICA DE CLIC CON CONSOLE.LOGS ▼▼▼ ---
        bellButton.addEventListener('click', (e) => {
            e.preventDefault();
            console.log("--- CLIC EN CAMPANA ---"); // DEBUG

            // 1. Oculta el contador
            if (countElement) {
                console.log("1. Ocultando contador (JS)"); // DEBUG
                countElement.style.display = 'none'; 
            }
            
            // 2. Llama al cargador
            console.log("2. Llamando a loadNotifications(true)"); // DEBUG
            loadNotifications(true); 
            
            // 3. Muestra el modal
            console.log("3. Mostrando modal"); // DEBUG
            notificationModal.show();
        });
        // --- ▲▲▲ FIN DE LA LÓGICA DE CLIC ▲▲▲ ---
    }

    /**
     * Busca las notificaciones en la API de Django y actualiza el modal.
     */
    // --- ▼▼▼ LÓGICA DE CARGA CON CONSOLE.LOGS ▼▼▼ ---
    function loadNotifications(markAsRead = false) {
        if (!notificationsList) return;
        notificationsList.innerHTML = '<p class="text-center text-muted p-3">Cargando...</p>';
        console.log("4. loadNotifications: Empezando fetch a /api/alertas/"); // DEBUG

        // 1. Pide las notificaciones
        fetch(apiNotificationsUrl)
            .then(response => {
                if (!response.ok) { 
                    console.error("loadNotifications: ¡Error de red!", response); // DEBUG
                    throw new Error('Error al obtener notificaciones.'); 
                }
                return response.json();
            })
            .then(notifications => {
                console.log("5. loadNotifications: Éxito. Notificaciones recibidas:", notifications.length); // DEBUG
                
                // 2. Dibuja el HTML
                notificationsList.innerHTML = '';
                if (notifications.length === 0) {
                    notificationsList.innerHTML = '<p class="text-center text-muted p-3">No tienes notificaciones nuevas.</p>';
                    return; // No hay nada que marcar como leído
                }

                notifications.forEach(notif => {
                    const itemHtml = `
                        <a href="${notif.link}" class="notification-item" data-id="${notif.id}">
                            <div class="notification-avatar">
                                <img src="${staticUrlBase}default-avatar.png" alt="avatar" style="width: 40px; height: 40px; border-radius: 50%;">
                            </div>
                            <div class="notification-content">
                                <p class="notification-text">
                                    ${notif.message}
                                </p>
                                <p class="notification-time">${notif.time}</p> 
                            </div>
                        </a>
                    `;
                    notificationsList.innerHTML += itemHtml;
                });

                // 3. Llama a marcar como leído (SI ES NECESARIO)
                if (markAsRead && notifications.length > 0) {
                    console.log("6. loadNotifications: Llamando a markNotificationsAsRead()"); // DEBUG
                    markNotificationsAsRead();
                } else {
                    console.log("6. loadNotifications: No se marcará como leído (markAsRead=false o length=0)"); // DEBUG
                }
            })
            .catch(error => {
                console.error("Error en fetchNotifications:", error);
                notificationsList.innerHTML = '<p class="text-center text-danger p-3">Error al cargar notificaciones.</p>';
            });
    }
    // --- ▲▲▲ FIN DE LA LÓGICA DE CARGA ▲▲▲ ---


    /**
     * Envía una señal al backend para marcar todas las 
     * notificaciones del usuario como leídas.
     */
    // --- ▼▼▼ LÓGICA DE MARCAR CON CONSOLE.LOGS ▼▼▼ ---
    function markNotificationsAsRead() {
        const markReadUrl = '/api/alertas/mark-read/';
        console.log("7. markNotificationsAsRead: Empezando POST a /api/alertas/mark-read/"); // DEBUG

        fetch(markReadUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log("8. markNotificationsAsRead: Éxito. Marcadas como leídas."); // DEBUG
            } else {
                console.error("8. markNotificationsAsRead: Error del backend.", data.message); // DEBUG
            }
        })
        .catch(error => {
            console.error('Error en fetch markNotificationsAsRead:', error); // DEBUG
        });
    }
    // --- ▲▲▲ FIN DE LA LÓGICA DE MARCAR ▲▲▲ ---


    /**
     * Revisa el contador de notificaciones (para la campanita)
     */
    // --- ▼▼▼ LÓGICA DE CONTEO CON CONSOLE.LOGS ▼▼▼ ---
function checkNotificationCount() {
        if (!countElement) return;
        
        // 1. Definimos la NUEVA URL solo para el contador
        const countUrl = '/api/alertas/unread-count/';

        console.log("checkNotificationCount: Chequeando contador en NUEVA URL...");

        // 2. Hacemos fetch a la nueva URL
        fetch(countUrl)
            .then(response => response.json())
            .then(data => {
                // 3. Leemos la respuesta de la nueva vista
                if (data.status === 'success') {
                    const unreadCount = data.unread_count;
                    console.log("checkNotificationCount: Recibidas:", unreadCount);
                    if (unreadCount > 0) {
                        countElement.textContent = unreadCount;
                        countElement.style.display = 'flex';
                    } else {
                        countElement.style.display = 'none';
                    }
                } else {
                    console.warn("Error chequeando contador:", data.message);
                    countElement.style.display = 'none';
                }
            })
            .catch(error => {
                console.warn("Error fatal chequeando contador:", error);
                countElement.style.display = 'none';
            });
    }
    // --- ▲▲▲ FIN DE LA FUNCIÓN MODIFICADA ▲▲▲ ---

    // Chequear el contador de la campanita al cargar la página
    checkNotificationCount();
});