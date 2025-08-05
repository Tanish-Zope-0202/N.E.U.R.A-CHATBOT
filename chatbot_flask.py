from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import re
import fitz  # PyMuPDF

# --- LOAD ENV ---
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- CONFIG ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
UPLOAD_FOLDER = 'uploaded_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

chat_history = []
uploaded_files_data = {}

# --- PDF TEXT EXTRACTION ---
def extract_text_from_pdf(filepath):
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"[PDF Extract Error] {e}")
        return ""

# --- LOAD EXISTING FILES ---
def load_uploaded_files_data():
    for fname in os.listdir(UPLOAD_FOLDER):
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        ext = os.path.splitext(fname)[1].lower()
        text = ""
        if ext == '.pdf':
            text = extract_text_from_pdf(fpath)
        else:
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    text = f.read()
            except:
                pass
        uploaded_files_data[fname] = text
load_uploaded_files_data()

# --- ROUTES ---
@app.route('/')
def index():
    return send_from_directory('templates', 'index_blue.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def is_weather_query(message):
    return re.search(r'weather in ([a-zA-Z\s]+)', message.lower())

def get_weather(city):
    try:
        params = {"q": city.strip(), "appid": OPENWEATHER_KEY, "units": "metric"}
        response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return (
            f"🌤️ Weather in {data['name']}:\n"
            f"🌡️ Temperature: {data['main']['temp']}°C (Feels like: {data['main']['feels_like']}°C)\n"
            f"💧 Humidity: {data['main']['humidity']}%\n"
            f"🌬️ Wind Speed: {data['wind']['speed']} m/s\n"
            f"☁️ Sky: {data['weather'][0]['description'].capitalize()}"
        )
    except Exception as e:
        print("[Weather Error]", e)
        return "❌ Unable to fetch weather right now."

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message is empty."}), 400

        if (match := is_weather_query(user_message)):
            return jsonify({"response": get_weather(match.group(1))})

        chat_history.append({"role": "user", "parts": [{"text": user_message}]})
        headers = {"Content-Type": "application/json"}
        payload = {"contents": chat_history}

        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=15)
        result = response.json()

        candidates = result.get("candidates", [])
        if candidates and candidates[0]["content"]["parts"]:
            reply = candidates[0]["content"]["parts"][0]["text"]
            chat_history.append({"role": "model", "parts": [{"text": reply}]})
            return jsonify({"response": reply})
        else:
            return jsonify({"response": "😶 AI didn't return a proper response."})
    except Exception as e:
        print("[Chat Error]", e)
        return jsonify({"error": "Something went wrong with chat."}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    ext = os.path.splitext(file.filename)[1].lower()
    content = ""

    if ext == '.pdf':
        content = extract_text_from_pdf(file_path)
    elif ext in ['.txt', '.md', '.py', '.csv']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[Read Error] {e}")

    uploaded_files_data[file.filename] = content or ""

    
    return jsonify({
        'response': '✅ File uploaded successfully.',
        'filename': file.filename
    })

@app.route('/ask-file', methods=['POST'])
def ask_about_file():
    try:
        data = request.get_json()
        filename = data.get("filename")
        question = data.get("question", "").strip()

        if not filename or not question:
            return jsonify({'error': 'Missing filename or question.'}), 400

        if filename not in uploaded_files_data:
            fpath = os.path.join(UPLOAD_FOLDER, filename)
            ext = os.path.splitext(filename)[1].lower()
            if os.path.exists(fpath):
                if ext == '.pdf':
                    uploaded_files_data[filename] = extract_text_from_pdf(fpath)
                else:
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            uploaded_files_data[filename] = f.read()
                    except:
                        uploaded_files_data[filename] = ""
            else:
                return jsonify({'error': 'File not found on server.'}), 404

        content = uploaded_files_data[filename]
        if not content.strip():
            return jsonify({'response': '❌ No readable text found in the uploaded file.'})

        short_content = content[:3000]
        prompt = f"The user uploaded this document:\n\n{short_content}\n\nQuestion: {question}"

        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=15)
        result = response.json()

        candidates = result.get("candidates", [])
        if candidates and candidates[0]["content"]["parts"]:
            return jsonify({"response": candidates[0]["content"]["parts"][0]["text"]})
        else:
            return jsonify({'response': "🤖 AI returned no answer."})
    except Exception as e:
        print("[Ask Error]", e)
        return jsonify({'error': 'Failed to get answer from AI.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
