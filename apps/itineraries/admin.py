from django.contrib import admin
from .models import Category, TouristicPlace, Itinerary, ItineraryStop, Review

# Register your models here.
admin.site.register(Category)
admin.site.register(TouristicPlace)
admin.site.register(Itinerary)
admin.site.register(ItineraryStop)
admin.site.register(Review)
