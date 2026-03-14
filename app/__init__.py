from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError

from app.db import db
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp


def create_app(config):
    try:
        app = Flask(__name__)
        app.config.from_object(config)

        # register extensions
        db.init_app(app)

        # register blueprints
        app.register_blueprint(user_bp, url_prefix='/users')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolios')
        app.register_blueprint(security_bp, url_prefix='/securities')
        app.register_blueprint(trade_bp, url_prefix='/trades')

        # Global Exception Handler for Pydantic
        @app.errorhandler(ValueError)
        def handle_value_error(error):
            db.session.rollback()  # Explicit rollback
            return jsonify({'error': str(error)}), 400
        
        @app.errorhandler(HTTPException)
        def handle_http_exception(error):
            db.session.rollback()  # Rollback on HTTP exceptions
            return jsonify({'error': error.description}), error.code

        @app.errorhandler(Exception)
        def handle_generic_error(error):
            db.session.rollback()  # Rollback on any unhandled exception
            return jsonify({'error': 'An internal error occurred'}), 500
        
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            # Extract first error message for simplicity
            first_error = error.errors()[0]
            error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
            return jsonify({'error': error_message, 'code': 400}), 400
        return app
    except Exception as e:
        print(f'Error creating app: {e}')
        raise