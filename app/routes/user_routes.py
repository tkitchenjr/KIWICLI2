from flask import Blueprint, jsonify, request, g

import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
from app.auth.auth import requires_auth
from app.db import db

from app.routes.domain.request import CreateUserRequest, UpdateBalanceRequest
from app.routes.domain.response import ErrorResponse

user_bp = Blueprint('user', __name__)


@user_bp.route('/', methods=['GET'])
def get_users():
    users = user_service.get_all_users()
    return jsonify([user.__to_dict__() for user in users]), 200


@user_bp.route('/<username>', methods=['GET'])
def get_user(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'User {username} does not exist').model_dump()), 404
    return jsonify(user.__to_dict__()), 200


@user_bp.route('/', methods=['POST'])
def create_user():
    create_user_request = CreateUserRequest(**request.get_json())
    user_service.create_user(
        username = create_user_request.username,
        password = create_user_request.password,
        firstname = create_user_request.firstname,
        lastname = create_user_request.lastname,
        balance = create_user_request.balance)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201


@user_bp.route('/update-balance', methods=['PUT'])
def update_balance():
    update_balance_request = UpdateBalanceRequest(**request.get_json())
    user = user_service.get_user_by_username(update_balance_request.username)
    if user is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'User {update_balance_request.username} does not exist').model_dump()), 404
    user_service.update_user_balance(
        username = update_balance_request.username,
        new_balance = update_balance_request.new_balance)
    db.session.commit()
    return jsonify({'message': 'User balance updated successfully'}), 200

@user_bp.route('/<username>', methods=['DELETE'])
@requires_auth
def delete_user(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'User {username} does not exist').model_dump()), 404
    user_service.delete_user(username)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@user_bp.route('/<username>/transactions', methods=['GET'])
@requires_auth 
def get_user_transactions(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'User {username} does not exist').model_dump()), 404
    transactions = transaction_service.get_transactions_by_user(username)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200


@user_bp.route('/me/ensure', methods=['POST'])
@requires_auth
def ensure_current_user():
    """Create or retrieve the current authenticated user based on JWT claims."""
    claims = g.get('current_user', {})
    
    # Extract username and profile info from Cognito JWT
    username = claims.get('cognito:username') or claims.get('username') or claims.get('email')
    email = claims.get('email', '')
    name = claims.get('name', 'User')
    
    if not username:
        return jsonify(ErrorResponse(error='Invalid token', detail='No username in token').model_dump()), 400
    
    # Parse name into first and last name
    name_parts = name.split(' ', 1) if name else ['Cognito', 'User']
    firstname = name_parts[0] or 'Cognito'
    lastname = name_parts[1] if len(name_parts) > 1 else 'User'
    
    try:
        # Check if user exists
        existing_user = user_service.get_user_by_username(username)
        if existing_user:
            return jsonify(existing_user.__to_dict__()), 200
        
        # Create new user with defaults for Cognito-authenticated users
        user_service.create_user(
            username=username,
            password='cognito_auth',  # Placeholder - auth is handled by Cognito
            firstname=firstname,
            lastname=lastname,
            balance=0.0
        )
        db.session.commit()
        
        new_user = user_service.get_user_by_username(username)
        return jsonify(new_user.__to_dict__()), 201
        
    except Exception as e:
        return jsonify(ErrorResponse(error='User creation failed', detail=str(e)).model_dump()), 500

