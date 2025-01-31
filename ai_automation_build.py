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
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash

oauth = OAuth()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production
app.config['GMAIL_API_KEY'] = os.getenv("GMAIL_API_KEY")
app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")

oauth.init_app(app)  # Ensure OAuth is initialized with the Flask app

google = oauth.register(
    'google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params={'scope': 'email'},
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    client_kwargs={'scope': 'email'},
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

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the AI Automation API"})

@app.route('/api/routes', methods=['GET'])
def get_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({"endpoint": rule.endpoint, "methods": list(rule.methods), "route": str(rule)})
    return jsonify({"routes": routes})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = generate_password_hash(data.get('password'))
    
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400
    
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=username)
    return jsonify({"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczODI5MDQwOCwianRpIjoiYTBiNTg2ZTgtZTBhNC00NmVkLWE3NDctMWViMmZkMjBiNjFhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InRlc3R1c2VyMiIsIm5iZiI6MTczODI5MDQwOCwiY3NyZiI6IjBiNjM5Y2M1LTkwMTItNDkwYy05Y2E0LWU3YWQwZTgyYTcyOSIsImV4cCI6MTczODI5MTMwOH0.PbWycfptZWD0RTRdbXTl7LUYwnUqMSjnZi2vugs-1_A"})

@app.route('/api/oauth/google', methods=['GET'])
def google_login():
    redirect_uri = url_for('authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/oauth/google/authorized', methods=['GET'])
def authorized():
    token = google.authorize_access_token()
    if not token:
        return jsonify({"message": "OAuth authentication failed"}), 400
    return jsonify({"access_token": token['access_token']})

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







