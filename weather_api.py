import datetime as dt
import json
import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
WEATHER_API_KEY = ""
BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

app = Flask(__name__)

def get_weather(location: str, date: str):
    url = f"{BASE_URL}/{location}/{date}?unitGroup=metric&include=current&key={WEATHER_API_KEY}&contentType=json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        weather_day = data.get("days", [{}])[0]  
        formatted_weather = {
            "temp_c": weather_day.get("temp", None),
            "wind_kph": weather_day.get("windspeed", None),
            "pressure_mb": weather_day.get("pressure", None),
            "humidity": weather_day.get("humidity", None),
        }
        return formatted_weather
    else:
        return {"error": f"Error {response.status_code}: {response.text}"}


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Weather API Service</h2></p>"


@app.route("/content/api/v1/integration/weather", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.utcnow()
    json_data = request.get_json()

    if json_data.get("token") != API_TOKEN:
        raise InvalidUsage("Invalid or missing API token", status_code=403)

    if not all(key in json_data for key in ["requester_name", "location", "date"]):
        raise InvalidUsage("Missing required fields: requester_name, location, date", status_code=400)

    requester_name = json_data["requester_name"]
    location = json_data["location"]
    date = json_data["date"]
    
    weather_data = get_weather(location, date)
    
    end_dt = dt.datetime.utcnow()

    result = {
        "requester_name": requester_name,
        "timestamp": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "date": date,
        "weather": weather_data,
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
