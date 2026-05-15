from flask import Blueprint, jsonify, request, g

import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
from app.auth.auth import requires_auth
from app.db import db

from app.routes.domain.request import CreatePortfolioRequest
from app.routes.domain.response import ErrorResponse

portfolio_bp = Blueprint('portfolio', __name__)


def _get_username_from_token():
	"""Extract username from the authenticated JWT token claims."""
	claims = g.get('current_user', {})
	# Cognito typically stores the username in 'cognito:username' or 'username'
	username = claims.get('cognito:username') or claims.get('username') or claims.get('sub')
	return username


@portfolio_bp.route('/', methods=['GET'])
def get_all_portfolios():
	portfolios = portfolio_service.get_all_portfolios()
	return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id):
	portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
	if portfolio is None:
		return jsonify(ErrorResponse(error='Not found', detail=f'No portfolio exists with ID {portfolio_id}').model_dump()), 404
	return jsonify(portfolio.__to_dict__()), 200


@portfolio_bp.route('/user/<username>', methods=['GET'])
def get_portfolios_by_user(username):
	user = user_service.get_user_by_username(username)
	if user is None:
		return jsonify(ErrorResponse(error='Not found', detail=f'User {username} does not exist').model_dump()), 404
	portfolios = portfolio_service.get_portfolios_by_user(user)
	return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200


@portfolio_bp.route('/', methods=['POST'])
@requires_auth
def create_portfolio():
	create_portfolio_request = CreatePortfolioRequest(**request.get_json())
	user = user_service.get_user_by_username(create_portfolio_request.username)
	if user is None:
		error = ErrorResponse(error='Not found', detail=f'User {create_portfolio_request.username} does not exist')
		return jsonify(error.model_dump()), 404        
	portfolio_id = portfolio_service.create_portfolio(
		name=create_portfolio_request.name,
		description=create_portfolio_request.description,
		username=create_portfolio_request.username)
	db.session.commit()
	return jsonify({'message': 'Portfolio created successfully', 'portfolio_id': portfolio_id}), 201


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@requires_auth
def delete_portfolio(portfolio_id):
	portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
	if portfolio is None:
		return jsonify(ErrorResponse(error='Not found', detail=f'No portfolio exists with ID {portfolio_id}').model_dump()), 404
	portfolio_service.delete_portfolio(portfolio_id)
	db.session.commit()
	return jsonify({'message': 'Portfolio deleted successfully'}), 200

@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
def get_portfolio_transactions(portfolio_id):
	if portfolio_service.get_portfolio_by_id(portfolio_id) is None:
		return jsonify(ErrorResponse(error='Not found', detail=f'No portfolio exists with ID {portfolio_id}').model_dump()), 404
	transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
	return jsonify([transaction.__to_dict__() for transaction in transactions]), 200
