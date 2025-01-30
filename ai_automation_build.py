from flask import Flask, request, jsonify, redirect, url_for
import requests
import os
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import base64
import json
import logging
from urllib.parse import quote as url_quote, unquote as url_decode, urlencode as url_encode
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_oauthlib.client import OAuth
from urllib.parse import quote as url_quote, unquote as url_decode, urlencode as url_encode

oauth = OAuth()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production
app.config['GMAIL_API_KEY'] = os.getenv("GMAIL_API_KEY")
app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")

google = oauth.remote_app(
    'google',
    consumer_key=app.config['GOOGLE_CLIENT_ID'],
    consumer_secret=app.config['GOOGLE_CLIENT_SECRET'],
    request_token_params={'scope': 'email'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth'
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.before_request
def log_request_info():
    logging.info(f"Request: {request.method} {request.url}")
    logging.info(f"Headers: {dict(request.headers)}")
    logging.info(f"Body: {request.get_json()}")

db = SQLAlchemy(app)
jwt = JWTManager(app)
scheduler = BackgroundScheduler()
scheduler.start()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/api/oauth/google', methods=['GET'])
def google_login():
    return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/api/oauth/google/authorized', methods=['GET'])
def authorized():
    response = google.authorized_response()
    if response is None or response.get('access_token') is None:
        return jsonify({"message": "OAuth authentication failed"}), 400
    return jsonify({"access_token": response['access_token']})

@app.route('/api/gmail/send', methods=['POST'])
@jwt_required()
def send_email():
    data = request.json
    recipient = data.get("recipient")
    subject = data.get("subject")
    body = data.get("body")
    
    headers = {"Authorization": f"Bearer {app.config['GMAIL_API_KEY']}"}
    payload = {
        "raw": base64.urlsafe_b64encode(f"To: {recipient}\nSubject: {subject}\n\n{body}".encode()).decode()
    }
    
    response = requests.post("https://www.googleapis.com/gmail/v1/users/me/messages/send", json=payload, headers=headers)
    return jsonify(response.json())

@app.route('/api/voice/generate', methods=['POST'])
@jwt_required()
def generate_voice():
    data = request.json
    text = data.get("text")
    user_api_key = data.get("api_key")
    
    headers = {"Authorization": f"Bearer {user_api_key}"}
    url = "https://api.openai.com/v1/audio/speech"
    payload = {"model": "tts-1", "input": text}
    
    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json())

@app.route('/api/webhooks/trigger', methods=['POST'])
@jwt_required()
def trigger_webhook():
    data = request.json
    webhook_url = data.get("url")
    payload = data.get("payload", {})
    
    response = requests.post(webhook_url, json=payload)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)












