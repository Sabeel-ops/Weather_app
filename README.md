Weather Monitoring Application
A Flask-based weather monitoring system that tracks and analyzes weather conditions across major Indian cities. The application fetches real-time weather data from OpenWeatherMap API, stores historical data, and provides daily weather summaries.
Features

Real-time weather monitoring for 6 major Indian cities
Automatic data collection every 5 minutes
Historical weather data storage and analysis
Daily weather summaries with statistical analysis
Temperature unit conversion (Celsius/Fahrenheit)
Comprehensive logging system
RESTful API endpoints for data access
Web interface for data visualization

Dependencies
Python Version

Python 3.7 or higher

Python Packages
CopyFlask==2.0.1
requests==2.26.0
sqlite3 (comes with Python)
Install dependencies using:
bashCopypip install -r requirements.txt
Configuration

OpenWeatherMap API Key

Sign up at OpenWeatherMap
Replace API_KEY in app.py with your API key:
pythonCopyAPI_KEY = "your_api_key_here"



Cities Configuration

Default cities are set in the CITIES dictionary:

Delhi
Mumbai
Chennai
Bangalore
Kolkata
Hyderabad


To modify cities, update the CITIES dictionary with city IDs from OpenWeatherMap



Installation & Setup

Clone the repository:
bashCopygit clone <repository-url>
cd weather-monitoring-app

Create a virtual environment:
bashCopypython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
bashCopypip install -r requirements.txt

Set up the database:

The application will automatically create the SQLite database on first run
Default database file: weather_data.db



Running the Application

Start the application:
bashCopypython app.py

Access the web interface:

Open a browser and navigate to http://localhost:5000



Project Structure
Copyweather-monitoring-app/
├── app.py              # Main application file
├── weather_data.db     # SQLite database
├── weather_app.log     # Application logs
├── requirements.txt    # Dependencies
└── templates/          # HTML templates
    └── index.html      # Main web interface
Design Choices
Database Schema

Weather Readings Table

Stores raw weather data
Fields: id, city, temperature, condition, timestamp, created_at
Enables historical data analysis


Daily Summaries Table

Aggregated daily weather statistics
Fields: city, date, avg_temp, max_temp, min_temp, dominant_condition
Optimizes performance for historical queries



Background Processing

Uses Python's threading to handle periodic data updates
Updates occur every 5 minutes (configurable via UPDATE_INTERVAL)
Daemon thread ensures clean application shutdown

Error Handling

Comprehensive error logging system
Graceful handling of API failures
Database transaction management
Error recovery mechanisms

Data Analysis

Weighted condition analysis for accurate weather pattern detection
Statistical aggregation for daily summaries
Temperature unit conversion utilities

API Endpoints

/api/weather

Returns current weather data for all cities
Method: GET


/api/daily-summaries

Returns historical weather summaries
Method: GET
Query Parameters:

days: Number of days to retrieve (default: 7)




/api/set-unit/<unit>

Sets temperature unit preference
Method: GET
Units: celsius, fahrenheit



Logging

Log file: weather_app.log
Logs both to file and console
Configurable log levels
Includes timestamps and log categories

Error Handling
The application implements comprehensive error handling:

API connection failures
Database errors
Data processing errors
Invalid user inputs

Future Improvements

Add user authentication
Implement caching for frequently accessed data
Add more statistical analysis features
Create data export functionality
Add weather alerts system
Implement unit tests
Add Docker support

Contributing

Fork the repository
Create your feature branch
Commit your changes
Push to the branch
Create a Pull Request