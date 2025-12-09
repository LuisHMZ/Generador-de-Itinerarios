# Sincronización de Categorías

## Resumen de Cambios

Se ha implementado el guardado automático de categorías cuando se registran lugares turísticos desde la API de Google Places.

### ✅ Cambios Implementados

1. **Mapeo de Tipos de Google a Categorías**
   - Agregado `GOOGLE_TYPE_TO_CATEGORY` en `views.py` (líneas 69-102)
   - Mapea 29 tipos de Google Places a las 20 categorías principales del sistema
   - Basado en `categorias.csv` y alineado con `ALLOWED_GOOGLE_TYPES`

2. **Guardado Automático de Categorías**
   - Modificado `search_places_api_view()`: Guarda categorías al crear lugares desde búsqueda
   - Modificado `nearby_places_api_view()`: Guarda categorías al obtener lugares cercanos
   - Solo asigna categorías si el lugar es nuevo o no tiene categorías previas

3. **Validación Robusta**
   - Solo guarda tipos de Google que existen en `GOOGLE_TYPE_TO_CATEGORY`
   - Usa `get_or_create` para evitar duplicados de categorías
   - Relación many-to-many permite múltiples categorías por lugar

### 📋 Comando para Sincronizar Categorías

Para poblar/actualizar las categorías desde el CSV:

```bash
python manage.py seed_categories
```

Este comando:
- Lee `apps/itineraries/categorias.csv`
- Crea o actualiza las 20 categorías principales
- Es idempotente (puede ejecutarse múltiples veces sin problemas)

### 🔄 Flujo Completo

1. **Usuario busca un lugar** → `search_places_api_view()`
2. **Se busca en BD local** → Verifica si ya existe
3. **Si no existe, consulta Google API** → Place Details
4. **Se filtra por tipos permitidos** → `ALLOWED_GOOGLE_TYPES`
5. **Se guarda el lugar** → `update_or_create`
6. **Se mapean y guardan categorías** → `GOOGLE_TYPE_TO_CATEGORY`
7. **Se descarga la foto** (si no tiene)

### 📊 Mapeo de Categorías

| Tipo de Google | Categoría del Sistema |
|----------------|----------------------|
| museum | Museos |
| art_gallery | Galerías de Arte |
| landmark, point_of_interest | Puntos de Interés |
| tourist_attraction, shopping_mall | Atracciones Turísticas |
| historical_place, historical_landmark, cultural_landmark | Sitios Históricos |
| church, hindu_temple, mosque, synagogue, place_of_worship | Iglesias y Templos |
| performing_arts_theater | Teatros |
| amusement_park | Parques de Diversiones |
| zoo | Zoológicos |
| aquarium | Acuarios |
| stadium | Estadios |
| movie_theater | Cines |
| night_club, bar, casino | Vida Nocturna |
| park | Parques y Plazas |
| natural_feature | Maravillas Naturales |
| campground | Zonas de Acampar |
| restaurant | Restaurantes |
| cafe | Cafeterías |
| bakery | Panaderías |

### 🧪 Testing

Para verificar que funciona:

1. Ejecutar `python manage.py seed_categories`
2. Buscar un lugar nuevo (ej: "Museo Frida Kahlo")
3. Verificar en Django Admin que el lugar tiene categorías asignadas
4. Revisar logs de debug para ver mensajes como:
   ```
   --- [DEBUG] Categorías asignadas a 'Museo Frida Kahlo': {'Museos', 'Atracciones Turísticas'}
   ```

### 📝 Notas Importantes

- Un lugar puede tener múltiples categorías (ej: un museo puede ser también atracción turística)
- Las categorías se asignan solo si el lugar es nuevo o no tiene categorías previas
- El sistema es resiliente: si no encuentra mapeo para un tipo de Google, simplemente lo omite
- Las categorías se crean automáticamente si no existen en la BD
