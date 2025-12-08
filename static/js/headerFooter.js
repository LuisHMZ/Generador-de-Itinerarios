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
    // Este archivo ahora asume que el header/footer ya están renderizados por plantillas Django
    // Sólo añade comportamiento (títulos dinámicos, notificaciones) sobre los elementos existentes.

    const staticUrlBase = '/static/img/';
    const apiNotificationsUrl = '/api/alertas/';
    const apiUnreadCountUrl = '/api/alertas/unread-count/';
    const apiMarkReadUrl = '/api/alertas/mark-read/';

    // --- TÍTULO DEL HEADER ---
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
        'ver-itinerario-final.html': 'Mi Itinerario'
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
        els.forEach(el => el.textContent = text);
    }
    setHeaderTitle(computeHeaderTitle());
    const titleObserver = new MutationObserver(() => setHeaderTitle(computeHeaderTitle()));
    const titleEl = document.querySelector('title');
    if (titleEl) titleObserver.observe(titleEl, { childList: true });

    // --- NOTIFICACIONES ---
    const notificationsList = document.getElementById('notifications-list');
    const countElement = document.getElementById('notification-badge-count');
    const modalElement = document.getElementById('notificationsModal');
    const bellButton = document.getElementById('bell-button');

    if (modalElement && bellButton) {
        const notificationModal = new bootstrap.Modal(modalElement, {
            backdrop: false,
            keyboard: true,
        });

        bellButton.addEventListener('click', (e) => {
            e.preventDefault();
            if (countElement) countElement.style.display = 'none';
            loadNotifications(true);
            notificationModal.show();
        });

        // Cerrar modal al hacer clic fuera de él
        document.addEventListener('click', (e) => {
            if (modalElement.classList.contains('show') && 
                !modalElement.querySelector('.modal-content').contains(e.target) &&
                !bellButton.contains(e.target)) {
                notificationModal.hide();
            }
        });
    }

    function loadNotifications(markAsRead = false) {
        if (!notificationsList) return;
        notificationsList.innerHTML = '<p class="text-center text-muted p-3">Cargando...</p>';

        fetch(apiNotificationsUrl)
            .then(response => {
                if (!response.ok) throw new Error('Error al obtener notificaciones.');
                return response.json();
            })
            .then(notifications => {
                notificationsList.innerHTML = '';
                if (!notifications || notifications.length === 0) {
                    notificationsList.innerHTML = '<p class="text-center text-muted p-3">No tienes notificaciones.</p>';
                    return;
                }

                notifications.forEach(notif => {
                    const itemHtml = `
                        <a href="${notif.link}" class="list-group-item list-group-item-action notification-item" data-id="${notif.id}">
                            <div class="d-flex align-items-start gap-2">
                                <img src="${staticUrlBase}default-avatar.png" alt="avatar" style="width: 40px; height: 40px; border-radius: 50%;">
                                <div>
                                    <div class="small">${notif.message}</div>
                                    <div class="text-muted small">${notif.time}</div>
                                </div>
                            </div>
                        </a>
                    `;
                    notificationsList.innerHTML += itemHtml;
                });

                if (markAsRead) markNotificationsAsRead();
            })
            .catch(error => {
                console.error('Error en fetchNotifications:', error);
                notificationsList.innerHTML = '<p class="text-center text-danger p-3">Error al cargar notificaciones.</p>';
            });
    }

    function markNotificationsAsRead() {
        fetch(apiMarkReadUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }
        })
        .then(response => response.json())
        .then(data => { if (data.status !== 'success') console.error('Error al marcar notificaciones:', data.message); })
        .catch(error => console.error('Error en fetch markNotificationsAsRead:', error));
    }

    function checkNotificationCount() {
        if (!countElement) return;
        fetch(apiUnreadCountUrl)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const unreadCount = data.unread_count;
                    if (unreadCount > 0) {
                        countElement.textContent = unreadCount;
                        countElement.style.display = 'flex';
                    } else {
                        countElement.style.display = 'none';
                    }
                } else {
                    countElement.style.display = 'none';
                }
            })
            .catch(error => { console.warn('Error chequeando contador de notificaciones:', error); if (countElement) countElement.style.display = 'none'; });
    }

    checkNotificationCount();
});