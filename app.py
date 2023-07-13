import requests
from flask import Flask, render_template
import random
from dotenv import load_dotenv
import os

load_dotenv() 
# enviroment variables

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")

# Идентификация
@app.route('/')
def get_tracks():

    api_key = API_KEY
    api_url = "https://api.jamendo.com/v3.0"

    endpoint = "/tracks"
    params = {
        "client_id": api_key,
        "format": "json",
        "limit": 200
    }

    response = requests.get(api_url + endpoint, params=params)
    data = response.json()

    # Обработка полученных данных и размешивание
    if "results" in data:
        tracks = random.sample(data["results"], 10)
        return render_template('tracks.html', tracks=tracks)
    else:
        return "Ошибка получения данных"

if __name__ == '__main__':
    app.run()