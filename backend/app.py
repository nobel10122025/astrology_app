from flask import Flask
from flask_cors import CORS
from blueprints.ai import ai_bp
from blueprints.home import home_bp
from blueprints.health import health_bp
from blueprints.calculate import calculate_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(ai_bp)
app.register_blueprint(home_bp)
app.register_blueprint(health_bp)
app.register_blueprint(calculate_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
