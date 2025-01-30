from flask import Flask, request, jsonify
import requests
import os
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import base64
import json

def deepseek_optimize(api_key, workflow_data):
    headers = {"Authorization": f"Bearer {api_key}"}
    url = "https://api.deepseek.com/optimize"  # Placeholder URL
    payload = {"workflow": workflow_data}
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

# Initialize DeepSeek AI (Placeholder, requires correct SDK)
@app.route('/api/workflow', methods=['POST'])
def create_workflow():
    """Endpoint to create a new automation workflow."""
    data = request.json
    workflow_id = save_workflow_to_db(data)
    return jsonify({"message": "Workflow created successfully", "workflow_id": workflow_id})

@app.route('/api/web/scrape', methods=['POST'])
def scrape_website():
    """Scrapes a given website and extracts text."""
    data = request.json
    url = data.get("url")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    return jsonify({"text": text})

@app.route('/api/ai/generate_image', methods=['POST'])
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
def schedule_task():
    """Schedules a task for later execution."""
    data = request.json
    task_time = data.get("time")
    task_url = data.get("url")
    
    scheduler.add_job(lambda: requests.get(task_url), 'date', run_date=task_time)
    return jsonify({"message": "Task scheduled successfully"})

@app.route('/api/execute', methods=['POST'])
def execute_workflow():
    """Executes a predefined workflow based on triggers."""
    data = request.json
    workflow_id = data.get("workflow_id")
    execute_automation(workflow_id)
    return jsonify({"message": "Workflow executed successfully"})

@app.route('/api/ai/generate_text', methods=['POST'])
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




