import geopy
from geopy.geocoders import Nominatim

def lambda_handler(event, context):
    
    # 1. Access the custom attribute "City"
    user_attributes = event['request']['userAttributes']
    raw_city = user_attributes.get('custom:City')

    # 2. Basic Validation: Is it empty or insanely long?
    if not raw_city or len(raw_city.strip()) == 0:
        raise Exception('Preferred City is required.')
    
    if len(raw_city) > 50:
        raise Exception('City name is too long. Please use under 50 characters.')

    # 3. Advanced Validation: Does this city actually exist?
    geolocator = Nominatim(user_agent="weather_lambda_app")
    try:
        location = geolocator.geocode(raw_city.strip())
        if not location:
            # If Geopy can't find it, reject the signup!
            raise Exception(f'Could not find the city "{raw_city}". Please check your spelling.')
    except Exception as e:
        # If the Geopy API times out, we should probably let them through rather than block signups
        print(f"Geocoding validation error: {e}")

    # (OPTIONAL) Remove these for production so users have to verify their emails!
    # event['response']['autoConfirmUser'] = True
    # event['response']['autoVerifyEmail'] = True

    # Everything is OK — allow the sign-up
    return event