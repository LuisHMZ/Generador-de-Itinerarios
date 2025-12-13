from django import forms
from .models import Post, Comment, PostPicture
from apps.itineraries.models import Itinerary 

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Escribe un comentario...',
                'style': 'resize: none;'
            })
        }

class CreatePostForm(forms.ModelForm):
    # Campo manual para la imagen
    image = forms.ImageField(required=False, label="Imagen")

    class Meta:
        model = Post
        fields = ['title', 'text', 'visibility'] 
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CreatePostForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        post = super(CreatePostForm, self).save(commit=False)
        if self.user:
            post.user = self.user
        
        if commit:
            post.save()
            
            # --- LÓGICA DE GUARDADO DE IMAGEN ---
            image_file = self.cleaned_data.get('image')
            if image_file:
                # Usamos PostPicture que es el modelo original de tu proyecto
                # Asumo que el campo de la imagen se llama 'pic_url' o 'image'. 
                # Si te da error, verifica en apps/posts/models.py cómo se llama el campo.
                PostPicture.objects.create(post=post, pic_url=image_file) 
                
        return post