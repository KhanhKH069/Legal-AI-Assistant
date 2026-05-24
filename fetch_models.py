import os
import requests

api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyDEcL9ftbWeeG18B-Kli-wsblUbMBo_CMk")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)
if response.status_code == 200:
    models = response.json().get("models", [])
    for model in models:
        print(model.get("name"))
else:
    print("Error:", response.status_code, response.text)
