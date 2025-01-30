from flask import Flask, request, jsonify
import requests
import os
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import base64
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production

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
    return jsonify({"access_token": access_token})

@app.route('/api/web/scrape', methods=['POST'])
@jwt_required()
def scrape_website():
    """Scrapes a given website and extracts text."""
    data = request.json
    url = data.get("url")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    return jsonify({"text": text})

@app.route('/api/ai/generate_image', methods=['POST'])
@jwt_required()
def generate_image():
    """Generates an image using DALL·E API."""
    data = request.json
    prompt = data.get("prompt")
    user_api_key = data.get("api_key")
    
    headers = {"Authorization": f"Bearer {user_api_key}"}
    url = "https://api.openai.com/v1/images/generations"
    payload = {
        "model": "dall-e-2",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json())

@app.route('/api/schedule/task', methods=['POST'])
@jwt_required()
def schedule_task():
    """Schedules a task for later execution."""
    data = request.json
    task_time = data.get("time")
    task_url = data.get("url")
    
    scheduler.add_job(lambda: requests.get(task_url), 'date', run_date=task_time)
    return jsonify({"message": "Task scheduled successfully"})

@app.route('/api/ai/generate_text', methods=['POST'])
@jwt_required()
def generate_text():
    """Generates text using OpenAI API."""
    data = request.json
    prompt = data.get("prompt")
    user_api_key = data.get("api_key")
    
    headers = {"Authorization": f"Bearer {user_api_key}"}
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
        "max_tokens": 100
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)






