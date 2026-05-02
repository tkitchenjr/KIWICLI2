from dataclasses import asdict
from flask import Blueprint, jsonify

import app.service.security_service as security_service
import app.service.transaction_service as transaction_service
from app.routes.domain.response import ErrorResponse

security_bp = Blueprint('security', __name__)


@security_bp.route('/<ticker>', methods=['GET'])
def get_security(ticker):
    security = security_service.get_security_by_ticker(ticker)
    if security is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'Security {ticker} not found').model_dump()), 404
    return jsonify(asdict(security)), 200


@security_bp.route('/<ticker>/transactions', methods=['GET'])
def get_security_transactions(ticker):
    transactions = transaction_service.get_transactions_by_ticker(ticker)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200
