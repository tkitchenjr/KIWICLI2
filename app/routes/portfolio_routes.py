from flask import Blueprint, jsonify, request, g

import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
from app.db import db
from app.auth.auth import requires_auth

from app.routes.domain.request import CreatePortfolioRequest
from app.routes.domain.response import ErrorResponse

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/', methods=['GET'])
@requires_auth
def get_all_portfolios():
    # Only return portfolios owned by the authenticated user
    authenticated_username = g.current_user.get('username')
    user = user_service.get_user_by_username(authenticated_username)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    
    portfolios = portfolio_service.get_portfolios_by_user(user)
    return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@requires_auth
def get_portfolio(portfolio_id):
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'No portfolio exists with ID {portfolio_id}').model_dump()), 404
    
    # Verify user owns this portfolio
    authenticated_username = g.current_user.get('username')
    if portfolio.owner != authenticated_username:
        return jsonify({'error': 'Access denied - you can only view your own portfolios'}), 403
    
    return jsonify(portfolio.__to_dict__()), 200


@portfolio_bp.route('/user/<username>', methods=['GET'])
@requires_auth
def get_portfolios_by_user(username):
    # Verify user can only access their own portfolios
    authenticated_username = g.current_user.get('username')
    if username != authenticated_username:
        return jsonify({'error': 'Access denied - you can only view your own portfolios'}), 403
    
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'User {username} does not exist').model_dump()), 404
    portfolios = portfolio_service.get_portfolios_by_user(user)
    return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200


@portfolio_bp.route('/', methods=['POST'])
@requires_auth
def create_portfolio():
    # Use authenticated user's username instead of trusting request data
    authenticated_username = g.current_user.get('username')
    
    create_portfolio_request = CreatePortfolioRequest(**request.get_json())
    
    # Security: Only allow creating portfolios for the authenticated user
    if create_portfolio_request.username != authenticated_username:
        return jsonify({'error': 'Access denied - you can only create portfolios for yourself'}), 403
    
    user = user_service.get_user_by_username(authenticated_username)
    if user is None:
        error = ErrorResponse(error='Not found', detail=f'User {authenticated_username} does not exist')
        return jsonify(error.model_dump()), 404        
    portfolio_id = portfolio_service.create_portfolio(
        name=create_portfolio_request.name,
        description=create_portfolio_request.description,
        username=authenticated_username)  # Use authenticated username
    db.session.commit()
    return jsonify({'message': 'Portfolio created successfully', 'portfolio_id': portfolio_id}), 201


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@requires_auth
def delete_portfolio(portfolio_id):
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'No portfolio exists with ID {portfolio_id}').model_dump()), 404
    
    # Verify user owns this portfolio before allowing deletion
    authenticated_username = g.current_user.get('username')
    if portfolio.owner != authenticated_username:
        return jsonify({'error': 'Access denied - you can only delete your own portfolios'}), 403
    
    portfolio_service.delete_portfolio(portfolio_id)
    db.session.commit()
    return jsonify({'message': 'Portfolio deleted successfully'}), 200

@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@requires_auth
def get_portfolio_transactions(portfolio_id):
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'No portfolio exists with ID {portfolio_id}').model_dump()), 404
    
    # Verify user owns this portfolio before showing transactions
    authenticated_username = g.current_user.get('username')
    if portfolio.owner != authenticated_username:
        return jsonify({'error': 'Access denied - you can only view transactions for your own portfolios'}), 403
    
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200
