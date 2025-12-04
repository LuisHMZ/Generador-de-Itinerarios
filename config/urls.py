"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.users import views as user_views
from apps.itineraries import views as itinerary_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs de autenticación (allauth)
    path('accounts/', include('allauth.urls')),
    

    # Include las URLs de las aplicaciones
    path('api/users/', include('apps.users.urls')),
    path('api/itineraries/', include('apps.itineraries.urls')),
    path('api/messaging/', include('apps.messaging.urls')),
    path('api/posts/', include('apps.posts.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('register/', user_views.simple_register_view, name='simple_register'),
    path('login/', user_views.simple_login_view, name='simple_login'),
    path('logout/', user_views.simple_logout_view, name='simple_logout'),
    path('home/', itinerary_views.home_view, name='home'),
    path('', itinerary_views.home_view, name='home'),
    path('panel/usuarios/', user_views.admin_users_view, name='admin_users'),
    path('panel/usuarios/toggle/<int:user_id>/', user_views.admin_toggle_user_status, name='admin_toggle_status'),
    path('panel/usuarios/eliminar/<int:user_id>/', user_views.delete_user, name='admin_delete_user'),
    path('account-suspended/', user_views.account_suspended_view, name='account_suspended'),
    path('panel/usuario/<int:user_id>/perfil/', user_views.admin_user_detail_view, name='admin_user_detail'),
    path('panel/logs/', user_views.admin_login_logs, name='admin_login_logs'),
    # Pagina principal
    # path('', include('apps.itineraries.urls_home')),  # Asumiendo que la app itineraries maneja la home
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
