// static/js/headerFooter.js

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
    // Leemos el username del body para el enlace de perfil
    const currentUsername = document.body.dataset.username || '';
    const profileUrl = currentUsername ? `/perfil/${currentUsername}/` : '#';
    
    const staticUrlBase = '/static/img/'; 
    const apiNotificationsUrl = '/api/alertas/';
    const apiMarkReadUrl = '/api/alertas/mark-read/';
    // (Nota: apiUnreadCountUrl eliminada porque HTMX se encarga ahora)
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
    
    <span id="notification-badge-wrapper"
      hx-get="/api/alertas/badge/"   
      hx-trigger="load, every 2s" 
      hx-swap="innerHTML">
</span>
</span>

</button>
                    </div>
                    <div class="dropdown">
                        <button class="btn btn-menu" type="button" id="dropdownMenuButton" data-bs-toggle="dropdown" aria-expanded="false" title="Menú">
                            <i class="bi bi-list"></i>
                        </button>
                        
                        <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                            <li><a class="dropdown-item" href="#"><i class="bi bi-gear me-2"></i>Configuración</a></li>
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

    if (headerContainer) {
        headerContainer.innerHTML = headerHtml;

        if (typeof htmx !== 'undefined') {
            console.log("✅ HTMX detectado. Procesando nuevo contenido..."); // <--- AGREGA ESTO
            htmx.process(headerContainer);
        } else {
            console.error("❌ ERROR: HTMX no está definido. ¿Falta el <script> en el HTML?"); // <--- AGREGA ESTO
        }
    }
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
    // --- LÓGICA DE NOTIFICACIONES (MODAL) ---
    // ------------------------------------
    
    const notificationsList = document.getElementById('notifications-list');
    const modalElement = document.getElementById('notificationsModal'); 
    const bellButton = document.getElementById('bell-button');

    // Inicializamos el modal si existe
    if (modalElement && bellButton) {
        // No crear una nueva instancia si ya existe
        let notificationModal = bootstrap.Modal.getInstance(modalElement);
        if (!notificationModal) {
            notificationModal = new bootstrap.Modal(modalElement, {
                backdrop: false,  // Permite backdrop pero no estático
                keyboard: true    // Permite cerrar con ESC
            });
        }
        
        bellButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            // Opcional: Ocultar visualmente el badge al instante al abrir
            const badge = document.getElementById('notification-badge-count');
            if (badge) badge.style.display = 'none';
            
            // 1. Carga el historial y marca como leídas en backend
            loadNotifications(true); 
            
            // 2. Muestra el modal
            notificationModal.show();
        });
    }

    /**
     * Carga el HISTORIAL de notificaciones en el modal.
     * Si 'markAsRead' es true, también llama a la función para marcarlas.
     */
    function loadNotifications(markAsRead = false) {
        if (!notificationsList) return;
        notificationsList.innerHTML = '<p class="text-center text-muted p-3">Cargando...</p>';

        fetch(apiNotificationsUrl) // Pide el historial (leídas o no)
            .then(response => {
                if (!response.ok) { throw new Error('Error al obtener notificaciones.'); }
                return response.json();
            })
            .then(notifications => {
                notificationsList.innerHTML = '';
                if (notifications.length === 0) {
                    notificationsList.innerHTML = '<p class="text-center text-muted p-3">No tienes notificaciones.</p>';
                    return; 
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

                if (markAsRead) {
                    markNotificationsAsRead();
                }
            })
            .catch(error => {
                console.error("Error en fetchNotifications:", error);
                notificationsList.innerHTML = '<p class="text-center text-danger p-3">Error al cargar notificaciones.</p>';
            });
    }

    /**
     * Llama a la API para marcar todas como leídas.
     */
    function markNotificationsAsRead() {
        fetch(apiMarkReadUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                console.error("Error al marcar notificaciones:", data.message);
            }
        })
        .catch(error => {
            console.error('Error en fetch markNotificationsAsRead:', error);
        });
    }

    // Nota: Ya no llamamos a checkNotificationCount() porque HTMX lo hace automáticamente.
});