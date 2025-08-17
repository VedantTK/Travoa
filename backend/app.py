from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
import time
from functools import wraps
import psycopg2
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "http://35.224.187.121"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://tripadmin:securepassword123@db:5432/tripdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(100), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)

def retry_db_operation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        attempts = 5
        delay = 5  # seconds
        for i in range(attempts):
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if i < attempts - 1:
                    print(f"Database connection failed, retrying in {delay} seconds... ({i+1}/{attempts})")
                    time.sleep(delay)
                else:
                    raise e
    return wrapper

@app.route('/api/plan', methods=['POST'])
def plan_trip():
    data = request.get_json()
    destination = data.get('destination')
    travel_date = data.get('travel_date')

    if not destination or not travel_date:
        return jsonify({'error': 'Destination and travel date are required'}), 400

    # Fetch country info from REST Countries API
    country_info = {'name': 'Unknown', 'capital': 'Unknown', 'currency': 'Unknown'}
    try:
        response = requests.get(f'https://restcountries.com/v3.1/name/{destination}?fullText=true')
        if response.status_code == 200:
            country_data = response.json()[0]
            country_info['name'] = country_data['name']['common']
            country_info['capital'] = country_data['capital'][0] if country_data['capital'] else 'Unknown'
            country_info['currency'] = list(country_data['currencies'].keys())[0] if country_data['currencies'] else 'Unknown'
    except:
        pass

    # Fetch weather info from Open Weather API
    weather = {'description': 'Unknown', 'temperature': 'Unknown'}
    try:
        api_key = os.getenv('OPEN_WEATHER_API_KEY')
        response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={destination}&appid={api_key}&units=metric')
        if response.status_code == 200:
            weather_data = response.json()
            weather['description'] = weather_data['weather'][0]['description']
            weather['temperature'] = weather_data['main']['temp']
    except:
        pass

    # Fetch image from Unsplash API
    image_url = 'https://via.placeholder.com/300'
    try:
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        response = requests.get(f'https://api.unsplash.com/search/photos?query={destination}&client_id={unsplash_key}')
        if response.status_code == 200:
            image_data = response.json()
            if image_data['results']:
                image_url = image_data['results'][0]['urls']['regular']
    except:
        pass

    # Save trip to database
    try:
        new_trip = Trip(destination=destination, travel_date=travel_date)
        db.session.add(new_trip)
        db.session.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'destination': destination,
        'country_info': country_info,
        'weather': weather,
        'image_url': image_url
    })

@app.route('/api/trips', methods=['GET'])
def get_trips():
    trips = Trip.query.all()
    return jsonify([{
        'id': trip.id,
        'destination': trip.destination,
        'travel_date': trip.date.isoformat()
    } for trip in trips])

if __name__ == '__main__':
    with app.app_context():
        @retry_db_operation
        def init_db():
            db.create_all()
        init_db()
    app.run(host='0.0.0.0', port=5000)
