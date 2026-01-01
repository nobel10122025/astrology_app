# Backend - Flask Application

This is the backend Flask application for Subathuvam Pavathuvam.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

Start the Flask development server:
```bash
python app.py
```

The API will be available at [http://localhost:5000](http://localhost:5000)

### API Endpoints

- `GET /` - Home endpoint with welcome message
- `GET /api/health` - Health check endpoint

### Running in Production

For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
