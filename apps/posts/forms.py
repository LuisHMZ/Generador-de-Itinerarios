from django import forms
from .models import Post, Comment
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
    # Campo extra para la imagen (se guarda en PostPicture)
    image = forms.ImageField(
        required=False, 
        label="Foto",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Post
        # AGREGAMOS 'visibility' AQUI ▼
        fields = ['title', 'text', 'visibility', 'itinerary'] 
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control mb-2', 
                'placeholder': 'Título (Opcional)'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control mb-2', 
                'rows': 3, 
                'placeholder': '¿Qué estás pensando?'
            }),
            # WIDGET PARA VISIBILIDAD (NUEVO) ▼
            'visibility': forms.Select(attrs={
                'class': 'form-select mb-2'
            }),
            'itinerary': forms.Select(attrs={
                'class': 'form-select mb-2'
            })
        }
        labels = {
            'itinerary': 'Vincular a un Itinerario',
            'visibility': 'Quién puede ver esto', # Etiqueta amigable
            'image': 'Agregar Foto'
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtramos para mostrar solo TUS itinerarios
        if user:
            self.fields['itinerary'].queryset = Itinerary.objects.filter(user=user)
            self.fields['itinerary'].empty_label = "Sin itinerario (Opcional)"
            self.fields['itinerary'].required = False