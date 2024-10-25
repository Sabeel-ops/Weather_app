# app.py
from flask import Flask, render_template, jsonify, request, make_response
import requests
from datetime import datetime, date
import time
from threading import Thread
import json
import sqlite3
from collections import Counter
from statistics import mean
import logging
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = "7b4f8deeaf3eb4c16eb89ccc96b9c4cb"  # Replace with your API key
CITIES = {
    'Delhi': 1273294,
    'Mumbai': 1275339,
    'Chennai': 1264527,
    'Bangalore': 1277333,
    'Kolkata': 1275004,
    'Hyderabad': 1269843
}
UPDATE_INTERVAL = 300  # 5 minutes in seconds
DB_PATH = 'weather_data.db'

def init_db():
    """Initialize the SQLite database with required tables."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Table for raw weather readings
        c.execute('''
            CREATE TABLE IF NOT EXISTS weather_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                temperature REAL,
                condition TEXT,
                timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for daily summaries
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                date DATE,
                avg_temp REAL,
                max_temp REAL,
                min_temp REAL,
                dominant_condition TEXT,
                condition_frequency INTEGER,
                total_readings INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(city, date)
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
        
    finally:
        conn.close()

def store_weather_reading(city, temperature, condition, timestamp):
    """Store individual weather readings in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO weather_readings (city, temperature, condition, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (city, temperature, condition, timestamp))
        conn.commit()
        logger.debug(f"Stored weather reading for {city}: {temperature}°C, {condition}")
        
    except Exception as e:
        logger.error(f"Failed to store weather reading: {str(e)}")
        conn.rollback()
        
    finally:
        conn.close()

def calculate_dominant_condition(conditions):
    """Calculate the dominant weather condition using a weighted approach."""
    # Count raw frequencies
    condition_counts = Counter(conditions)
    
    # Weather condition weights (higher weight = more significant)
    condition_weights = {
        'Thunderstorm': 3.0,
        'Snow': 2.5,
        'Rain': 2.0,
        'Drizzle': 1.5,
        'Clear': 1.0,
        'Clouds': 1.0,
        'Mist': 1.2,
        'Fog': 1.3,
        'Haze': 1.1
    }
    
    # Calculate weighted frequencies
    weighted_counts = {
        condition: count * condition_weights.get(condition, 1.0)
        for condition, count in condition_counts.items()
    }
    
    # Get condition with highest weighted frequency
    dominant_condition = max(weighted_counts.items(), key=lambda x: x[1])[0]
    raw_frequency = condition_counts[dominant_condition]
    total_readings = sum(condition_counts.values())
    
    return dominant_condition, raw_frequency, total_readings

def generate_daily_summary(city, date_to_summarize):
    """Generate summary for a specific city and date with deletion of previous entries."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Check if there are any readings for this date
        readings = c.execute('''
            SELECT temperature, condition
            FROM weather_readings
            WHERE city = ? AND date(timestamp) = ?
        ''', (city, date_to_summarize)).fetchall()

        if not readings:
            logger.warning(f"No readings found for {city} on {date_to_summarize}")
            return None

        # Process the readings to calculate statistics
        temperatures = [r[0] for r in readings]
        conditions = [r[1] for r in readings]

        avg_temp = mean(temperatures)
        max_temp = max(temperatures)
        min_temp = min(temperatures)

        dominant_condition, condition_freq, total_readings = calculate_dominant_condition(conditions)

        # Delete any existing summary for the same city and date
        c.execute('''
            DELETE FROM daily_summaries
            WHERE city = ? AND date = ?
        ''', (city, date_to_summarize))

        # Insert the new summary
        c.execute('''
            INSERT INTO daily_summaries 
            (city, date, avg_temp, max_temp, min_temp, dominant_condition,
             condition_frequency, total_readings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (city, date_to_summarize, avg_temp, max_temp, min_temp,
              dominant_condition, condition_freq, total_readings))

        conn.commit()
        logger.info(f"Successfully generated and inserted new summary for {city} on {date_to_summarize}")

        return {
            'city': city,
            'date': date_to_summarize,
            'avg_temp': avg_temp,
            'max_temp': max_temp,
            'min_temp': min_temp,
            'dominant_condition': dominant_condition,
            'condition_frequency': condition_freq,
            'total_readings': total_readings
        }

    except Exception as e:
        logger.error(f"Error generating summary for {city} on {date_to_summarize}: {str(e)}")
        conn.rollback()
        return None

    finally:
        conn.close()


def kelvin_to_celsius(kelvin):
    """Convert Kelvin to Celsius."""
    return round(kelvin - 273.15, 2)

def kelvin_to_fahrenheit(kelvin):
    """Convert Kelvin to Fahrenheit."""
    return round((kelvin - 273.15) * 9/5 + 32, 2)

def fetch_weather_data(city_id):
    """Fetch weather data from OpenWeatherMap API."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            temp_c = kelvin_to_celsius(data['main']['temp'])
            condition = data['weather'][0]['main']
            timestamp = datetime.fromtimestamp(data['dt'])
            
            processed_data = {
                'main_condition': condition,
                'temperature_c': temp_c,
                'temperature_f': kelvin_to_fahrenheit(data['main']['temp']),
                'feels_like_c': kelvin_to_celsius(data['main']['feels_like']),
                'feels_like_f': kelvin_to_fahrenheit(data['main']['feels_like']),
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed']
            }
            
            city_name = list(CITIES.keys())[list(CITIES.values()).index(city_id)]
            store_weather_reading(
                city=city_name,
                temperature=temp_c,
                condition=condition,
                timestamp=timestamp
            )
            
            return processed_data
            
        logger.error(f"API request failed with status code: {response.status_code}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return None

def update_weather_data():
    """Background task to update weather data and generate summaries."""
    while True:
        try:
            current_date = date.today()
            for city, city_id in CITIES.items():
                data = fetch_weather_data(city_id)
                if data:
                    weather_data[city] = data
                    # Generate summary after each update
                    generate_daily_summary(city, current_date)
                    
        except Exception as e:
            logger.error(f"Error in update task: {str(e)}")
            
        finally:
            time.sleep(UPDATE_INTERVAL)

@app.route('/')
def index():
    """Render the main page."""
    preferred_unit = request.cookies.get('temp_unit', 'celsius')
    return render_template('index.html', preferred_unit=preferred_unit)

@app.route('/api/weather')
def get_weather():
    """Get current weather data for all cities."""
    return jsonify(weather_data)

@app.route('/api/daily-summaries')
def get_daily_summaries():
    """Get daily weather summaries."""
    days = request.args.get('days', '7')
    try:
        days = int(days)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        summaries = {}
        for city in CITIES:
            c.execute('''
                SELECT date, avg_temp, max_temp, min_temp, 
                       dominant_condition, condition_frequency, total_readings
                FROM daily_summaries
                WHERE city = ?
                ORDER BY date DESC
                LIMIT ?
            ''', (city, days))
            
            city_summaries = []
            for row in c.fetchall():
                city_summaries.append({
                    'date': row[0],
                    'avg_temp': row[1],
                    'max_temp': row[2],
                    'min_temp': row[3],
                    'dominant_condition': row[4],
                    'condition_frequency': row[5],
                    'total_readings': row[6]
                })
            summaries[city] = city_summaries
            
        conn.close()
        return jsonify(summaries)
        
    except Exception as e:
        logger.error(f"Error fetching summaries: {str(e)}")
        return jsonify({'error': 'Failed to fetch summaries'}), 500

@app.route('/api/set-unit/<unit>')
def set_unit(unit):
    """Set temperature unit preference."""
    if unit not in ['celsius', 'fahrenheit']:
        return jsonify({'error': 'Invalid unit'}), 400
    
    response = make_response(jsonify({'status': 'success'}))
    response.set_cookie('temp_unit', unit)
    return response

def verify_database():
    """Verify database tables and data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {table[0] for table in c.fetchall()}
        required_tables = {'weather_readings', 'daily_summaries'}
        
        if not required_tables.issubset(tables):
            missing_tables = required_tables - tables
            raise Exception(f"Missing required tables: {missing_tables}")
        
        # Check data
        c.execute("SELECT COUNT(*) FROM weather_readings")
        readings_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM daily_summaries")
        summaries_count = c.fetchone()[0]
        
        logger.info(f"Database verification complete: {readings_count} readings, {summaries_count} summaries")
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return False
        
    finally:
        conn.close()

def start_background_task():
    """Initialize database and start background task with verification."""
    try:
        init_db()
        
        if not verify_database():
            raise Exception("Database verification failed")
        
        thread = Thread(target=update_weather_data)
        thread.daemon = True
        thread.start()
        
        logger.info("Background task started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start background task: {str(e)}")
        raise

if __name__ == '__main__':
    weather_data = {}
    start_background_task()
    app.run(debug=True)