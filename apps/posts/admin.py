# En: apps/posts/admin.py
from django.contrib import admin
from .models import Post, PostPicture, Comment, CommentPicture
# (Ya no se importa 'Post' dos veces)

# Registra los otros modelos (¡esto está perfecto!)
admin.site.register(PostPicture)
admin.site.register(Comment)
admin.site.register(CommentPicture)

# Registra 'Post' usando el decorador (así solo está una vez)
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    search_fields = ('title', 'text', 'user__username')