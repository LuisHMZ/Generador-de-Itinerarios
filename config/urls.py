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
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from apps.users import views as user_views
from apps.itineraries import views as itinerary_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs de autenticación (allauth)
    path('accounts/', include('allauth.urls')),
    

    # Include las URLs de las aplicaciones
    # --- Montamos las API de itineraries bajo /api/ --- #
        # Rutas de la API REST de usuarios (api/users/)
    path('api/', include('apps.users.api_urls')),
        # Rutas de la API REST de itineraries (api/itineraries/)
    path('api/', include('apps.itineraries.api_urls')),
    path('api/messaging/', include('apps.messaging.urls')),
    path('api/posts/', include('apps.posts.urls')),
    path('api/reports/', include('apps.reports.urls')),

    #Rutas WEB (HTML)
    # Rutas de la app de itineraries (HTML)
    path('', include('apps.itineraries.urls')),
    # Rutas de la app de usuarios (HTML)
    path('', include('apps.users.urls')),



    # Pagina principal
    # path('', include('apps.itineraries.urls_home')),  # Asumiendo que la app itineraries maneja la home
]

# Añade esto al final:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)