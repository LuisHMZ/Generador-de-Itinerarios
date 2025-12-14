# apps/itineraries/serializers.py

from rest_framework import serializers
from .models import Itinerary, ItineraryStop, TouristicPlace, Category


# Campo flexible que acepta: PK (int/str), dict con 'id' o una instancia TouristicPlace
class FlexibleTouristicPlaceField(serializers.Field):
    def to_internal_value(self, data):
        # Si ya es una instancia del modelo, devolverla tal cual
        if isinstance(data, TouristicPlace):
            return data

        # Si vino un dict (por ejemplo el objeto nested desde el frontend), intentar extraer 'id'
        if isinstance(data, dict):
            pk = data.get('id') or data.get('pk')
            if pk is None:
                raise serializers.ValidationError('Se esperaba id dentro del objeto touristic_place.')
            data = pk

        # Si es cadena o número, convertir a int y recuperar la instancia
        try:
            pk_val = int(data)
        except Exception:
            raise serializers.ValidationError('Valor inválido para touristic_place. Se esperaba ID.')

        try:
            return TouristicPlace.objects.get(pk=pk_val)
        except TouristicPlace.DoesNotExist:
            raise serializers.ValidationError('TouristicPlace con id proporcionado no existe.')

    def to_representation(self, value):
        # Para representación en responses, devolvemos el ID
        try:
            return value.pk
        except Exception:
            return None

class ItineraryStopSerializer(serializers.ModelSerializer):
    # Podríamos mostrar más detalles del lugar si quisiéramos
    # place_name = serializers.CharField(source='touristic_place.name', read_only=True) 
    # Usamos el campo flexible para aceptar PK, dict o instancia
    touristic_place = FlexibleTouristicPlaceField()

    class Meta:
        model = ItineraryStop
        # Campos que esperamos recibir del frontend para CADA parada
        fields = ['touristic_place', 'day_number', 'placement'] 
        # 'itinerary' se asignará automáticamente en la vista

    def validate(self, data):
        # Validaciones básicas: day_number y placement deben ser enteros positivos
        day = data.get('day_number')
        placement = data.get('placement')
        errors = {}
        if day is None:
            errors['day_number'] = 'Este campo es obligatorio.'
        else:
            try:
                if int(day) < 1:
                    errors['day_number'] = 'El número de día debe ser >= 1.'
            except Exception:
                errors['day_number'] = 'Debe ser un número entero.'

        if placement is None:
            errors['placement'] = 'Este campo es obligatorio.'
        else:
            try:
                if int(placement) < 1:
                    errors['placement'] = 'La posición debe ser >= 1.'
            except Exception:
                errors['placement'] = 'Debe ser un número entero.'

        if errors:
            raise serializers.ValidationError(errors)

        return data

# serializers.py
class ItinerarySerializer(serializers.ModelSerializer):
    """ 
    ItinerarySerializer
    Serializador para el modelo Itinerary que soporta creación y actualización
    con manejo anidado de paradas (ItineraryStop). Proporciona validación
    personalizada para la lista de paradas y lógica para crear/rehacer las paradas
    asociadas cuando se crea o actualiza un itinerario.
    Campos (resumen)
    - id (read-only): identificador del itinerario.
    - user (read-only): relación al usuario propietario; no se escribe desde el serializer.
    - user_username (read-only): campo calculado que expone user.username.
    - title, description, start_date, end_date, category: campos del modelo, escribibles.
    - banner_pic: declarado como ImageField(required=False, allow_null=True) pero
        actualmente incluido en read_only_fields en Meta — por tanto, tal y como está
        el código, se tratará como read-only a menos que se ajuste Meta.read_only_fields.
    - creation_date (read-only): fecha de creación, gestionada por el modelo.
    - stops: campo anidado write_only (ItineraryStopSerializer, many=True, required=False).
        Se acepta en POST/PUT/PATCH para crear o reemplazar las paradas, pero no se
        devuelve en la representación por ser write_only.
    Comportamiento principal
    - create(validated_data):
        - Extrae 'stops' (si no viene, usa lista vacía).
        - Crea la instancia Itinerary con el resto de datos.
        - Crea una ItineraryStop por cada elemento de la lista de paradas asociándola
            al itinerary recién creado.
        - Retorna el itinerario creado.
    - validate_stops(value):
        - Permite None (no se valida) o una lista no vacía.
        - Requiere que el valor sea una lista; lanza ValidationError si no lo es.
        - Requiere que la lista no esté vacía; lanza ValidationError si lo está.
        - Valida cada elemento usando ItineraryStopSerializer; si algún elemento es
            inválido, lanza ValidationError con un detalle por índice: {'stops[i]': ...}.
    - update(instance, validated_data):
        - Extrae 'stops' si viene en la petición (si no viene, respeta las paradas actuales).
        - Actualiza los campos normales del itinerario usando super().update.
        - Si se recibieron datos de 'stops':
            - Valida la lista mediante validate_stops.
            - Borra todas las paradas actuales del itinerario y crea nuevas paradas a partir
                de los datos recibidos (comportamiento de "reemplazo completo").
        - Retorna la instancia actualizada.
    Errores y consideraciones
        - Si 'stops' no es lista o está vacía (cuando se proporciona), se lanza
            serializers.ValidationError con mensaje claro.
        - Si una parada individual falla la validación del serializer de parada,
            se devuelve un error estructurado por índice para facilitar la depuración.
        - La actualización de paradas se realiza borrando todas las existentes y creando
            las nuevas; no hace merging ni actualización por id. Si se requiere comportamiento
            distinto, hay que adaptar la lógica.
        - Si se pretende que banner_pic sea escribible, hay que eliminar 'banner_pic'
            de Meta.read_only_fields o ajustar la configuración para permitir carga.
        - Para muchas paradas se pueden considerar optimizaciones (bulk_create,
            transacción atómica, validación previa en bloque).
        Uso recomendado
        - Para incluir paradas en respuestas GET, añadir un campo read-only anidado
            separado o quitar write_only de 'stops' y adaptar la serialización de lectura.
        - En endpoints que manipulan paradas, envolver la creación/borrado en una
            transacción para asegurar atomicidad y consistencia. 
    """
    stops = ItineraryStopSerializer(many=True, write_only=True, required=False) # 'required=False' si puedes crear sin paradas
    user_username = serializers.CharField(source='user.username', read_only=True)
    # ¡Asegúrate de que banner_pic se pueda escribir!
    banner_pic = serializers.ImageField(required=False, allow_null=True) 

    class Meta:
        model = Itinerary
        # Añade los NUEVOS campos a la lista
        fields = [
            'id', 'user', 'user_username', 'title', 'description', 
            'banner_pic', 'created_at', 'stops',
            'start_date', 'end_date', 'category'
        ]
        # user y creation_date siguen siendo solo lectura
        read_only_fields = ['id', 'user', 'user_username', 'created_at'] 
    def create(self, validated_data):
        # Saca 'stops' si existe, si no, usa lista vacía
        stops_data = validated_data.pop('stops', []) 
        itinerary = Itinerary.objects.create(**validated_data)
        for stop_data in stops_data:
            ItineraryStop.objects.create(itinerary=itinerary, **stop_data)
        return itinerary

    def validate_stops(self, value):
        """
        Valida la lista de paradas entrante: debe ser una lista no vacía y cada
        elemento debe pasar la validación de ItineraryStopSerializer.
        """
        if value is None:
            return value

        if not isinstance(value, list):
            raise serializers.ValidationError('El campo stops debe ser una lista.')

        if len(value) == 0:
            raise serializers.ValidationError('La lista de paradas no puede estar vacía.')

        # Validar cada parada individualmente
        for idx, stop in enumerate(value):
            ser = ItineraryStopSerializer(data=stop)
            try:
                ser.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({f'stops[{idx}]': e.detail})

        return value

    def update(self, instance, validated_data):
        """
        Sobrescribe update para manejar las paradas (opcional pero recomendado).
        Si no lo haces, PUT/PATCH no podrán modificar las paradas.
        """
        # Saca 'stops' si viene en la petición
        stops_data = validated_data.pop('stops', None) 
        
        # Actualiza los campos normales del Itinerary
        instance = super().update(instance, validated_data)

        # Si se enviaron datos de 'stops', actualiza las paradas
        if stops_data is not None:
             # Validar las paradas usando el serializer de parada
             # Esto lanzará serializers.ValidationError si alguna es inválida
             self.validate_stops(stops_data)

             # Lógica para borrar paradas antiguas y crear las nuevas
             instance.itinerarystop_set.all().delete() # Borra todas las paradas existentes
             for stop_data in stops_data:
                 ItineraryStop.objects.create(itinerary=instance, **stop_data) # Crea las nuevas

        return instance

# Serializer para el modelo TouristicPlace
class CategorySerializer(serializers.ModelSerializer):
    """Serializer simple para mostrar nombres de categorías."""
    class Meta:
        model = Category
        fields = ['id', 'name']

class TouristicPlaceSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo TouristicPlace.
    Muestra los detalles de un lugar turístico.
    """
    # Para mostrar los nombres de las categorías en lugar de solo sus IDs
    categories = CategorySerializer(many=True, read_only=True) 
    # Devuelve la URL pública de la imagen si existe (compatible con lo que espera el JS)
    photo_url = serializers.SerializerMethodField()
    # Devuelve un array con los nombres de categorías como 'types' para compatibilidad con Google Places API
    types = serializers.SerializerMethodField()
    # Alias de external_api_rating para compatibilidad
    rating = serializers.DecimalField(source='external_api_rating', max_digits=2, decimal_places=1, read_only=True)

    class Meta:
        model = TouristicPlace
        # Define los campos que quieres que tu API devuelva
        fields = [
            'id', 
            'external_api_id', 
            'name', 
            'description', 
            'address', 
            'lat', 
            'long', 
            'website', 
            'phone_number', 
            'opening_hours',
            'external_api_rating',
            'rating',  # Alias para external_api_rating (compatibilidad)
            'categories', # Incluye la lista de categorías
            'photo',  # Incluye el campo de foto
            'photo_url', # URL pública de la foto (útil para el frontend)
            'types',  # Array de categorías como strings (formato Google Places API)
        ]
        # Hacemos algunos campos de solo lectura si no queremos que se creen/modifiquen vía API directamente
        read_only_fields = ['id', 'external_api_id', 'external_api_rating', 'rating', 'categories', 'photo', 'photo_url', 'types']

    def get_photo_url(self, obj):
        """
        Devuelve la URL pública de la foto del lugar.
        
        Funciona en dos escenarios:
        
        1. DESARROLLO LOCAL:
           - obj.photo.url devuelve: /media/place_photos/place_106.jpg
           - MEDIA_URL = /media/
           - Resultado: /media/place_photos/place_106.jpg (ya es URL completa relativa)
        
        2. PRODUCCIÓN (SUPABASE STORAGE):
           - obj.photo.url devuelve: place_photos/place_106.jpg (solo ruta relativa)
           - MEDIA_URL = https://project.supabase.co/storage/v1/object/public/media/
           - Resultado: https://project.supabase.co/storage/v1/object/public/media/place_photos/place_106.jpg
        """
        try:
            if obj.photo and hasattr(obj.photo, 'url'):
                url = obj.photo.url
                
                # Si la URL ya es absoluta (comienza con http), devolverla tal cual
                if url and url.startswith('http'):
                    return url
                
                # Si es relativa, combinarla con MEDIA_URL
                if url:
                    from django.conf import settings
                    if hasattr(settings, 'MEDIA_URL'):
                        media_url = settings.MEDIA_URL
                        # Evitar duplicar MEDIA_URL si ya está prefijado
                        if not url.startswith(media_url):
                            return media_url + url
                    return url
                    
        except Exception as e:
            print(f"!!! [ERROR] get_photo_url para {obj.name}: {e}")
        return None
    
    def get_types(self, obj):
        """
        Devuelve un array de nombres de categorías en formato string,
        compatible con el formato 'types' de Google Places API.
        Esto permite que el frontend use determinarCategoriaPrincipal().
        """
        try:
            # Convertir nombres de categorías a lowercase con underscores
            # para simular el formato de Google Places
            types = []
            for cat in obj.categories.all():
                # Convertir "Museos" -> "museum", "Parques y Plazas" -> "park", etc.
                cat_name = cat.name.lower().replace(' ', '_')
                types.append(cat_name)
            return types if types else ['point_of_interest']  # Fallback
        except Exception:
            return ['point_of_interest']


class ItineraryStopDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para devolver una parada incluyendo los datos completos
    del `TouristicPlace` anidado junto con `day_number` y `placement`.
    """
    touristic_place = TouristicPlaceSerializer(read_only=True)

    # Exponer lat/long/photo desde el TouristicPlace anidado pero mantener
    # la respuesta "plana" para compatibilidad con el frontend.
    lat = serializers.FloatField(source='touristic_place.lat', read_only=True)
    long = serializers.FloatField(source='touristic_place.long', read_only=True)
    photo = serializers.SerializerMethodField()

    class Meta:
        model = ItineraryStop
        fields = ['touristic_place', 'day_number', 'placement', 'lat', 'long', 'photo']

    def get_photo(self, obj):
        """Devuelve la URL de la foto del `touristic_place` si existe."""
        tp = getattr(obj, 'touristic_place', None)
        if not tp:
            return None
        try:
            if hasattr(tp, 'photo') and tp.photo and hasattr(tp.photo, 'url'):
                return tp.photo.url
        except Exception:
            pass
        return None