from flask import Blueprint, jsonify, g

import app.service.security_service as security_service
import app.service.transaction_service as transaction_service
from app.auth.auth import requires_auth
from app.routes.domain.response import ErrorResponse

security_bp = Blueprint('security', __name__)


@security_bp.route('/<ticker>', methods=['GET'])
def get_security(ticker):
    security = security_service.get_security_by_ticker(ticker)
    if security is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'Security {ticker} not found').model_dump()), 404
    return jsonify({'name': security}), 200


@security_bp.route('/<ticker>/transactions', methods=['GET'])
@requires_auth
def get_security_transactions(ticker):
    # Return only transactions for portfolios owned by the authenticated user
    authenticated_username = g.current_user.get('username')
    
    # Get all transactions for this ticker
    transactions = transaction_service.get_transactions_by_ticker(ticker)
    
    # Filter to only include transactions from user's portfolios
    user_transactions = []
    for transaction in transactions:
        # Assuming the transaction has a portfolio relationship
        if hasattr(transaction, 'portfolio') and transaction.portfolio.owner == authenticated_username:
            user_transactions.append(transaction)
    
    return jsonify([transaction.__to_dict__() for transaction in user_transactions]), 200
