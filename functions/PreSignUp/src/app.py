from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def lambda_handler(event, context):

    user_attributes = event['request']['userAttributes']
    raw_city = user_attributes.get('custom:City')

    if not raw_city or len(raw_city.strip()) == 0:
        raise Exception('Preferred City is required.')

    if len(raw_city) > 50:
        raise Exception('City name is too long. Please use under 50 characters.')

    geolocator = Nominatim(user_agent="weather_lambda_app")
    try:
        location = geolocator.geocode(raw_city.strip())
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        # Geocoding service is unavailable — fail open so we don't block all signups
        print(f"Geocoding service error (allowing signup): {e}")
        return event

    if not location:
        raise Exception(f'Could not find the city "{raw_city}". Please check your spelling.')

    return event
