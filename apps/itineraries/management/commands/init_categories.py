# apps/itineraries/management/commands/init_categories.py

from django.core.management.base import BaseCommand
from apps.itineraries.models import Category 

class Command(BaseCommand):
    help = 'Puebla la tabla de categorías mapeando Tipos de Google -> Descripción en Español'

    def handle(self, *args, **kwargs):
        # Tupla: (name_tecnico, description_espanol)
        categories_list = [
            ('museum', 'Museos'),
            ('art_gallery', 'Galerías de Arte'),
            ('tourist_attraction', 'Atracciones Turísticas'),
            ('point_of_interest', 'Puntos de Interés'),
            ('historic_site', 'Sitios Históricos'),
            ('church', 'Iglesias y Templos'),
            ('place_of_worship', 'Lugares de Culto'),
            ('hindu_temple', 'Templos Hindúes'),
            ('synagogue', 'Sinagogas'),
            ('mosque', 'Mezquitas'),
            ('amusement_park', 'Parques de Diversiones'),
            ('aquarium', 'Acuarios'),
            ('zoo', 'Zoológicos'),
            ('park', 'Parques y Plazas'),
            ('stadium', 'Estadios'),
            ('movie_theater', 'Cines'),
            ('night_club', 'Vida Nocturna'),
            ('bar', 'Bares y Cantinas'),
            ('casino', 'Casinos'),
            ('natural_feature', 'Maravillas Naturales'),
            ('campground', 'Zonas de Acampar'),
            ('restaurant', 'Restaurantes'),
            ('cafe', 'Cafeterías'),
            ('bakery', 'Panaderías'),
            ('shopping_mall', 'Centros Comerciales'),
        ]

        self.stdout.write('Iniciando carga de categorías...')

        count = 0
        for google_type, spanish_desc in categories_list:
            
            # --- AQUÍ ESTÁ EL CAMBIO ---
            obj, created = Category.objects.update_or_create(
                # 1. Buscamos por el 'name' técnico (ej. 'museum')
                name=google_type, 
                
                # 2. Si existe (o se crea), asignamos el español al campo 'description'
                defaults={
                    'description': spanish_desc 
                }
            )
            
            action = "Creado" if created else "Actualizado"
            self.stdout.write(f'- {google_type} -> {spanish_desc}: {action}')
            count += 1

        self.stdout.write(self.style.SUCCESS(f'¡Listo! Se procesaron {count} categorías.'))