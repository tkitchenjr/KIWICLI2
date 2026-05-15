
from flask import Flask, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from app.routes.domain.response import ErrorResponse

from app.db import db
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp
import app.models


def create_app(config):
    try:
        app = Flask(__name__)
        app.config.from_object(config)

        # Enable CORS for all routes with explicit configuration
        CORS(
            app,
            resources={
                r"/*": {
                    "origins": ["http://localhost:5173", "http://localhost:3000", "*"],
                    "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization"],
                    "supports_credentials": True,
                    "max_age": 3600,
                }
            },
        )

        # register extensions
        db.init_app(app)

        with app.app_context():
            db.create_all()

        # register blueprints
        app.register_blueprint(user_bp, url_prefix='/users')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolios')
        app.register_blueprint(security_bp, url_prefix='/securities')
        app.register_blueprint(trade_bp, url_prefix='/trades')

        # Global Exception Handlers for Pydantic
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            first_error = error.errors()[0]
            error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
            return jsonify(ErrorResponse(error='Validation Error', detail=error_message).model_dump()), 422
        
        return app
    
    except Exception as e:
        print(f'Error creating app: {e}')
        raise