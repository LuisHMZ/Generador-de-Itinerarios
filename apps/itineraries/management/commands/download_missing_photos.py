"""
Comando de gestión para descargar fotos faltantes de lugares turísticos desde Google Places API.

Uso:
    python manage.py download_missing_photos [--limit N] [--force]

Opciones:
    --limit N : Limitar el número de lugares a procesar (por defecto: todos)
    --force   : Forzar descarga incluso si el lugar ya tiene foto local
"""

import requests
from io import BytesIO
from PIL import Image
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models import Q
from apps.itineraries.models import TouristicPlace


class Command(BaseCommand):
    help = 'Descarga fotos faltantes de lugares turísticos desde Google Places API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Número máximo de lugares a procesar',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar descarga incluso si el lugar ya tiene foto local',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']

        # Obtener API key desde settings
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            raise CommandError('GOOGLE_API_KEY no está configurado en settings')

        # Filtrar lugares según opciones
        if force:
            places = TouristicPlace.objects.all()
            self.stdout.write(self.style.WARNING(
                '⚠️  Modo --force activado: procesando TODOS los lugares'
            ))
        else:
            # Solo lugares sin foto local (nulos o cadena vacía)
            places = TouristicPlace.objects.filter(Q(photo__isnull=True) | Q(photo=''))
            self.stdout.write(
                f'📸 Buscando lugares sin foto local...'
            )

        if limit:
            places = places[:limit]

        total = places.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                '✅ ¡Todos los lugares ya tienen fotos!'
            ))
            return

        self.stdout.write(
            f'\n🔍 Encontrados {total} lugares para procesar\n'
        )

        success_count = 0
        skip_count = 0
        error_count = 0

        for index, place in enumerate(places, 1):
            progress = f'[{index}/{total}]'
            place_name = place.name[:50]  # Truncar nombre largo
            
            # Verificar que tenga external_api_id para poder consultar la foto
            if not place.external_api_id:
                self.stdout.write(
                    f'{progress} ⏭️  {place_name} - Sin external_api_id'
                )
                skip_count += 1
                continue

            # Si ya tiene foto y no es --force, saltar
            if place.photo and not force:
                self.stdout.write(
                    f'{progress} ✓ {place_name} - Ya tiene foto'
                )
                skip_count += 1
                continue

            # Intentar descargar la foto usando Places Details v1
            try:
                details_url = (
                    f"https://places.googleapis.com/v1/{place.external_api_id}"
                    f"?fields=photos&key={api_key}"
                )

                details_resp = requests.get(details_url, timeout=15)

                if details_resp.status_code != 200:
                    self.stdout.write(self.style.ERROR(
                        f" {progress} ❌ Details HTTP {details_resp.status_code}"
                    ))
                    error_count += 1
                    continue

                details_data = details_resp.json()
                photos = details_data.get('photos') or []

                if not photos:
                    self.stdout.write(
                        f'{progress} ⏭️  {place_name} - Sin fotos en Google'
                    )
                    skip_count += 1
                    continue

                photo_resource_name = photos[0].get('name')
                if not photo_resource_name:
                    self.stdout.write(
                        f'{progress} ⏭️  {place_name} - Foto sin resource name'
                    )
                    skip_count += 1
                    continue

                photo_url = (
                    f"https://places.googleapis.com/v1/{photo_resource_name}/media"
                    f"?maxHeightPx=800&maxWidthPx=800&key={api_key}"
                )

                self.stdout.write(
                    f'{progress} 📥 Descargando: {place_name}...',
                    ending=''
                )

                response = requests.get(photo_url, timeout=15)
                
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    if image.mode in ('RGBA', 'P'):
                        image = image.convert('RGB')

                    output = BytesIO()
                    image.save(output, format='JPEG', quality=85, optimize=True)
                    output.seek(0)

                    safe_name = "".join(
                        c if c.isalnum() or c in (' ', '-', '_') else '_' 
                        for c in place.name
                    )
                    safe_name = safe_name.replace(' ', '_')[:100]
                    filename = f"{safe_name}_{place.id}.jpg"

                    place.photo.save(
                        filename,
                        ContentFile(output.getvalue()),
                        save=True
                    )

                    self.stdout.write(self.style.SUCCESS(' ✅'))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR(
                        f' ❌ Error HTTP {response.status_code}'
                    ))
                    error_count += 1

            except requests.exceptions.Timeout:
                self.stdout.write(self.style.ERROR(' ❌ Timeout'))
                error_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f' ❌ {str(e)[:50]}'))
                error_count += 1

        # Resumen final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'\n📊 Resumen:\n'
            f'   ✅ Descargadas:  {success_count}\n'
            f'   ⏭️  Omitidas:     {skip_count}\n'
            f'   ❌ Errores:      {error_count}\n'
            f'   📝 Total:        {total}\n'
        ))
        
        if success_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f'🎉 ¡{success_count} fotos descargadas exitosamente!'
            ))
