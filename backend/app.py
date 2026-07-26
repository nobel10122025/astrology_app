from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load backend/.env (supports the `export KEY=value` format used there) so keys
# like PPLX_API_KEY / ANTHROPIC_API_KEY are available without manually sourcing.
load_dotenv()

from blueprints.ai import ai_bp
from blueprints.home import home_bp
from blueprints.health import health_bp
from blueprints.calculate import calculate_bp
from blueprints.narrative import narrative_bp
from blueprints.predict import predict_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(ai_bp)
app.register_blueprint(home_bp)
app.register_blueprint(health_bp)
app.register_blueprint(calculate_bp)
app.register_blueprint(narrative_bp)
app.register_blueprint(predict_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
