from django.contrib import admin
from .models import Profile, UserConnection, Notification, PasswordHistory

# Register your models here.
admin.site.site_header = "MexTur Administración"
admin.site.site_title = "MexTur Admin"
admin.site.index_title = "Panel de Administración de MexTur"

admin.site.register(Profile)
admin.site.register(UserConnection)
admin.site.register(Notification)
admin.site.register(PasswordHistory)