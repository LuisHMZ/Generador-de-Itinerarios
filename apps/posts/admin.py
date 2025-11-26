from django.contrib import admin
from .models import Post, PostPicture, Comment

# Configuración para las fotos dentro del Post en el Admin
class PostPictureInline(admin.TabularInline):
    model = PostPicture
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Campos que verás en la lista principal
    list_display = ('user', 'title', 'visibility', 'created_at')
    
    # Filtros laterales (muy útil para probar)
    list_filter = ('visibility', 'created_at')
    
    # Campos que puedes buscar
    search_fields = ('title', 'text', 'user__username')
    
    # Esto permite editar la visibilidad DIRECTAMENTE desde la lista sin entrar al post
    list_editable = ('visibility',)
    
    inlines = [PostPictureInline]

# Registro simple para Comentarios
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')