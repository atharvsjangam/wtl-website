from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = "871da2a6732da40a3868e0d7a5a0348f"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

def get_weather(city):
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(WEATHER_URL, params=params)
    data = response.json()

    if response.status_code == 200:
        return {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "description": data["weather"][0]["description"]
        }
    else:
        return None

def get_forecast(city):
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(FORECAST_URL, params=params)
    data = response.json()

    if response.status_code == 200:
        forecast_list = data["list"][:5] 
        return [
            {"date": item["dt_txt"], "temp": item["main"]["temp"], "desc": item["weather"][0]["description"]}
            for item in forecast_list
        ]
    else:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city = request.form["city"]
        weather = get_weather(city)
        if weather:
            return render_template("weather.html", weather=weather, city=city)
        else:
            return render_template("weather.html", error="City not found")

    return render_template("weather.html")

@app.route("/forecast", methods=["POST"])
def forecast():
    city = request.form["city"]
    forecast_data = get_forecast(city)
    
    if forecast_data:
        return render_template("forecast.html", forecast=forecast_data, city=city)
    else:
        return render_template("forecast.html", error="City not found")

from flask import Flask, render_template, request, redirect

@app.route("/info")
def info():
    return redirect("https://www.pmaccelerator.io/")


from flask_sqlalchemy import SQLAlchemy 
from datetime import date


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Rickc137@127.0.0.1:3306/weather_app_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.Date, default=date.today, nullable=False)

    def __repr__(self):
        return f'<WeatherData {self.city} {self.start_date} to {self.end_date}>'


from flask import jsonify
from datetime import datetime

# CREATE - Add a new weather data record
@app.route("/weather_data", methods=["POST"])
def create_weather_data():
    data = request.get_json()
    required_fields = ["city", "start_date", "end_date", "temperature"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format."}), 400

    if start_date > end_date:
        return jsonify({"error": "Start date cannot be after end date."}), 400

    weather_entry = WeatherData(
        city=data["city"],
        start_date=start_date,
        end_date=end_date,
        temperature=data["temperature"]
    )
    db.session.add(weather_entry)
    db.session.commit()
    return jsonify({"message": "Weather data record created", "id": weather_entry.id}), 201

# READ - Retrieve all weather data records
@app.route("/weather_data", methods=["GET"])
def read_weather_data():
    records = WeatherData.query.all()
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "city": r.city,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "temperature": r.temperature,
            "created_at": r.created_at.isoformat()
        })
    return jsonify(result), 200

# UPDATE - Update a weather data record by ID
@app.route("/weather_data/<int:record_id>", methods=["PUT"])
def update_weather_data(record_id):
    data = request.get_json()
    record = WeatherData.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    if "city" in data:
        record.city = data["city"]
    if "start_date" in data:
        try:
            record.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "start_date must be in YYYY-MM-DD format"}), 400
    if "end_date" in data:
        try:
            record.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "end_date must be in YYYY-MM-DD format"}), 400
    if "temperature" in data:
        record.temperature = data["temperature"]

    if record.start_date > record.end_date:
        return jsonify({"error": "Start date cannot be after end date"}), 400

    db.session.commit()
    return jsonify({"message": "Weather data record updated"}), 200

# DELETE - Delete a weather data record by ID
@app.route("/weather_data/<int:record_id>", methods=["DELETE"])
def delete_weather_data(record_id):
    record = WeatherData.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Weather data record deleted"}), 200

# ---------------------------
# End of CRUD Endpoints
# ---------------------------


from flask import redirect
from datetime import datetime

# UI Route: Create Weather Data Record (Form)
@app.route("/weather_data/create", methods=["GET", "POST"])
def create_weather_data_ui():
    if request.method == "POST":
        city = request.form["city"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        temperature = request.form["temperature"]

        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD.", 400

        if sd > ed:
            return "Start date cannot be after end date.", 400

        weather_entry = WeatherData(
            city=city,
            start_date=sd,
            end_date=ed,
            temperature=float(temperature)
        )
        db.session.add(weather_entry)
        db.session.commit()
        return redirect("/weather_data/list")
    return render_template("weather_data_create.html")

# UI Route: List All Weather Data Records
@app.route("/weather_data/list", methods=["GET"])
def list_weather_data_ui():
    records = WeatherData.query.all()
    return render_template("weather_data_list.html", records=records)

# UI Route: Update Weather Data Record (Form)
@app.route("/weather_data/update/<int:record_id>", methods=["GET", "POST"])
def update_weather_data_ui(record_id):
    record = WeatherData.query.get(record_id)
    if not record:
        return "Record not found", 404
    if request.method == "POST":
        record.city = request.form["city"]
        try:
            record.start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
            record.end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD.", 400
        if record.start_date > record.end_date:
            return "Start date cannot be after end date.", 400
        record.temperature = float(request.form["temperature"])
        db.session.commit()
        return redirect("/weather_data/list")
    return render_template("weather_data_update.html", record=record)

# UI Route: Delete Weather Data Record (Confirmation)
@app.route("/weather_data/delete/<int:record_id>", methods=["GET", "POST"])
def delete_weather_data_ui(record_id):
    record = WeatherData.query.get(record_id)
    if not record:
        return "Record not found", 404
    if request.method == "POST":
        db.session.delete(record)
        db.session.commit()
        return redirect("/weather_data/list")
    return """
    <h1>Are you sure you want to delete this record?</h1>
    <form method="post">
      <button type="submit">Yes, Delete</button>
    </form>
    <a href="/weather_data/list">Cancel</a>
    """


if __name__ == "__main__":
    app.run(debug=True)
