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

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs de autenticación (allauth)
    path('accounts/', include('allauth.urls')),

    # Include las URLs de las aplicaciones
    path('api/', include('apps.users.urls')),
    # Montamos las API de itineraries bajo /api/
    path('api/', include('apps.itineraries.api_urls')),
    path('api/messaging/', include('apps.messaging.urls')),
    path('api/posts/', include('apps.posts.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('register/', user_views.simple_register_view, name='simple_register'),
    path('login/', user_views.simple_login_view, name='simple_login'),
    path('logout/', user_views.simple_logout_view, name='simple_logout'),
    path('home/', itinerary_views.home_view, name='home'),

    # Rutas web de la app itineraries (p.ej. /itineraries/create/)
    path('', include('apps.itineraries.urls')),

    # Pagina principal
    # path('', include('apps.itineraries.urls_home')),  # Asumiendo que la app itineraries maneja la home
]
