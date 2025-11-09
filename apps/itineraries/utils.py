# apps/itineraries/utils.py
import math

# --- Utilidades para la App `itineraries` ---

# Cálculo de la distancia entre dos puntos geográficos usando la fórmula del haversine
def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos (lat, long)
    usando la fórmula de Haversine.
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0

    # Convertir decimales a radianes
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

    # Diferencias
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    a = min(1.0, max(0.0, a))  # evita errores numéricos fuera de [0,1]
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance