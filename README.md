# Flask Chatbot with Gemini and Weather Integration

A Flask-based chatbot that uses Google's Gemini AI for conversations and OpenWeather API for weather information. It also supports file uploads and querying document contents.

## Features

- Chat with Gemini AI
- Get weather information for any city
- Upload and query documents (supports PDF, TXT, MD, PY, CSV)
- Web interface with multiple themes

## Setup

1. Clone the repository
```bash
git clone <your-repo-url>
cd CHATBOT
```

2. Create a virtual environment and activate it
```bash
python -m venv env
# On Windows
env\Scripts\activate
# On Unix or MacOS
source env/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
   - Copy `.env.example` to `.env`
   - Add your API keys:
     - Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
     - Get an OpenWeather API key from [OpenWeather](https://openweathermap.org/api)

5. Run the application
```bash
python chatbot_flask.py
```

The application will be available at `http://localhost:5000`

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_KEY=your_openweather_api_key_here
```

## Project Structure

- `chatbot_flask.py`: Main Flask application
- `static/`: Static files (images, styles)
- `templates/`: HTML templates
- `uploaded_files/`: Directory for uploaded documents
- `requirements.txt`: Project dependencies
