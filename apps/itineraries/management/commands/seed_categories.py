import csv
import codecs  # Para asegurar la codificación UTF-8
from django.core.management.base import BaseCommand
from django.conf import settings  # Para obtener la ruta base del proyecto (BASE_DIR)
from apps.itineraries.models import Category  # Importa tu modelo

# Define la ruta al archivo CSV
# Asume que BASE_DIR está en la raíz del proyecto (donde está manage.py)
# y tu archivo está en apps/itineraries/categorias.csv
CSV_FILE_PATH = settings.BASE_DIR / 'apps' / 'itineraries' / 'categorias.csv'


class Command(BaseCommand):
    help = 'Puebla la tabla Category (Categorías) desde el archivo categorias.csv'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando el sembrado de categorías...'))

        # Usamos codecs.open para forzar la lectura en UTF-8
        with codecs.open(CSV_FILE_PATH, 'r', 'utf-8') as f:
            reader = csv.reader(f)
            
            # Omitir la fila de encabezado (header)
            next(reader) 

            count_created = 0
            count_updated = 0

            for row in reader:
                if not row:  # Omitir filas vacías
                    continue
                
                # Leemos las columnas que nos interesan
                # row[0] es 'google_place_type', que no guardamos en este modelo
                category_name = row[1]
                category_desc = row[2]

                if not category_name: # Si la fila no tiene nombre, la saltamos
                    continue

                # Usamos update_or_create para ser "idempotentes"
                # Si la categoría ya existe por su nombre, actualiza su descripción.
                # Si no existe, la crea.
                category, created = Category.objects.update_or_create(
                    name=category_name,
                    defaults={
                        'description': category_desc
                    }
                )

                if created:
                    count_created += 1
                else:
                    count_updated += 1

        self.stdout.write(self.style.SUCCESS(f'¡Sembrado completado!'))
        self.stdout.write(f'Categorías creadas: {count_created}')
        self.stdout.write(f'Categorías actualizadas: {count_updated}')