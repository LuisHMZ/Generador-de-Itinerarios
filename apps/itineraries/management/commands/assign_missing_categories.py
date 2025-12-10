"""
Asigna categorías a lugares turísticos que no tienen ninguna categoría.
Obtiene los tipos desde Google Places Details v1 usando external_api_id
 y aplica el mapeo GOOGLE_TYPE_TO_CATEGORY.

Uso:
    python manage.py assign_missing_categories [--limit N]

Opciones:
    --limit N : Limita la cantidad de lugares a procesar (por defecto: todos los que no tienen categorías)
"""

import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Count

from apps.itineraries.models import TouristicPlace, Category
from apps.itineraries.views import GOOGLE_TYPE_TO_CATEGORY


class Command(BaseCommand):
    help = 'Asigna categorías a lugares sin categorías usando Google Places Details v1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Número máximo de lugares a procesar'
        )

    def handle(self, *args, **options):
        limit = options['limit']

        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            raise CommandError('GOOGLE_API_KEY no está configurado en settings')

        qs = (
            TouristicPlace.objects
            .annotate(cat_count=Count('categories'))
            .filter(cat_count=0)
        )

        if limit:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay lugares sin categorías.'))
            return

        self.stdout.write(f'Procesando {total} lugares sin categorías...')

        added_places = 0
        skipped_no_id = 0
        skipped_no_types = 0
        errors = 0

        for idx, place in enumerate(qs, start=1):
            progress = f'[{idx}/{total}]'
            name = place.name[:60]

            if not place.external_api_id:
                self.stdout.write(f'{progress} ⏭️  {name} - sin external_api_id')
                skipped_no_id += 1
                continue

            details_url = f"https://places.googleapis.com/v1/{place.external_api_id}?fields=types&key={api_key}"

            try:
                resp = requests.get(details_url, timeout=12)
                if resp.status_code != 200:
                    self.stdout.write(self.style.ERROR(f'{progress} ❌ HTTP {resp.status_code} {name}'))
                    errors += 1
                    continue

                data = resp.json()
                types = data.get('types') or []
                categories_to_add = set()
                for g_type in types:
                    mapped = GOOGLE_TYPE_TO_CATEGORY.get(g_type)
                    if mapped:
                        categories_to_add.add(mapped)

                if not categories_to_add:
                    self.stdout.write(f'{progress} ⏭️  {name} - sin tipos mapeables')
                    skipped_no_types += 1
                    continue

                for cat_name in categories_to_add:
                    cat_obj, _ = Category.objects.get_or_create(
                        name=cat_name,
                        defaults={'description': f'Categoría: {cat_name}'}
                    )
                    place.categories.add(cat_obj)

                added_places += 1
                self.stdout.write(self.style.SUCCESS(f'{progress} ✅ {name} ({len(categories_to_add)} categorías)'))

            except requests.exceptions.Timeout:
                self.stdout.write(self.style.ERROR(f'{progress} ❌ Timeout {name}'))
                errors += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{progress} ❌ {name} - {str(exc)[:80]}'))
                errors += 1

        self.stdout.write('\nResumen:')
        self.stdout.write(f'  ✅ Lugares actualizados: {added_places}')
        self.stdout.write(f'  ⏭️  Sin external_api_id: {skipped_no_id}')
        self.stdout.write(f'  ⏭️  Sin tipos mapeables: {skipped_no_types}')
        self.stdout.write(f'  ❌ Errores: {errors}')
