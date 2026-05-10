from flask import Blueprint, jsonify, request, g

import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
import app.service.portfolio_access_service as portfolio_access_service
from app.db import db
from app.auth.auth import requires_auth
from app.service.portfolio_access_service import PortfolioAccessError

from app.routes.domain.request import CreatePortfolioRequest, GrantAccessRequest
from app.routes.domain.response import ErrorResponse

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/', methods=['GET'])
@requires_auth
def get_all_portfolios():
    # Return all portfolios the user has access to (owned + granted access)
    authenticated_username = g.current_user.get('username')
    
    try:
        # Get portfolios the user owns
        user = user_service.get_user_by_username(authenticated_username)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        owned_portfolios = portfolio_service.get_portfolios_by_user(user)
        
        # Get portfolios the user has been granted access to
        from app.models.PortfolioAccess import PortfolioAccess
        access_grants = db.session.query(PortfolioAccess).filter_by(username=authenticated_username).all()
        
        result = []
        
        # Add owned portfolios with 'owner' role
        for portfolio in owned_portfolios:
            portfolio_dict = portfolio.__to_dict__()
            portfolio_dict['access_role'] = 'owner'
            result.append(portfolio_dict)
        
        # Add granted access portfolios
        for access in access_grants:
            portfolio_dict = access.portfolio.__to_dict__()
            portfolio_dict['access_role'] = access.role
            result.append(portfolio_dict)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve portfolios', 'detail': str(e)}), 500


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@requires_auth
def get_portfolio(portfolio_id):
    authenticated_username = g.current_user.get('username')
    
    try:
        portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Check authorization (viewer level required for read access)
        if portfolio.owner == authenticated_username:
            # Owner has full access
            return jsonify(portfolio.__to_dict__()), 200
        
        # Check granted access
        user_role = portfolio_access_service.check_user_access(portfolio_id, authenticated_username)
        if not user_role:
            return jsonify({'error': 'Access denied - you do not have access to this portfolio'}), 403
        
        # Viewer or manager can read
        return jsonify(portfolio.__to_dict__()), 200
        
    except PortfolioAccessError as e:
        return jsonify({'error': 'Portfolio not found', 'detail': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


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
    role = g.current_user.get('role', 'owner')

    if role != 'owner':
        return jsonify({'error': 'Access denied - only owners can create portfolios'}), 403
    
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
    role = g.current_user.get('role', 'owner')
    if role != 'owner':
        return jsonify({'error': 'Access denied - only owners can delete portfolios'}), 403

    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error='Not found', detail=f'No portfolio exists with ID {portfolio_id}').model_dump()), 404
    
    # Verify user owns this portfolio before allowing deletion
    authenticated_username = g.current_user.get('username')
    
    try:
        portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Only owners can delete portfolios
        if portfolio.owner != authenticated_username:
            return jsonify({'error': 'Access denied - only the portfolio owner can delete the portfolio'}), 403
        
        portfolio_service.delete_portfolio(portfolio_id)
        db.session.commit()
        return jsonify({'message': 'Portfolio deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@requires_auth
def get_portfolio_transactions(portfolio_id):
    authenticated_username = g.current_user.get('username')
    
    try:
        portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        # Check authorization (viewer level required for read access)
        if  portfolio.owner != authenticated_username:
            return jsonify({'error': 'Access denied - you do not have access to this portfolio'}), 403
        
        transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
        return jsonify([transaction.__to_dict__() for transaction in transactions]), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

@portfolio_bp.route('/<int:portfolio_id>/access', methods=['POST'])
@requires_auth
def grant_access(portfolio_id):
    authenticated_username = g.current_user.get('username')
    
    try:
        # Validate request data
        grant_request = GrantAccessRequest(**request.get_json())
        
        # Prevent self-granting (owner already has full access)
        if grant_request.username == authenticated_username:
            return jsonify({'error': 'You already own this portfolio'}), 400
        
        # Check ownership for authorization (service will validate portfolio exists)
        portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
        if portfolio and portfolio.owner != authenticated_username:
            return jsonify({'error': 'Access denied - only the portfolio owner can grant access'}), 403
        
        # Grant access via service (service validates portfolio & user existence)
        portfolio_access_service.grant_access(
            portfolio_id, 
            grant_request.username, 
            grant_request.role
        )
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully granted {grant_request.role} access to {grant_request.username}',
            'portfolio_id': portfolio_id,
            'username': grant_request.username,
            'role': grant_request.role
        }), 200
        
    except PortfolioAccessError as e:
        return jsonify({'error': 'Access management error', 'detail': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


@portfolio_bp.route('/<int:portfolio_id>/access/<username>', methods=['DELETE'])
@requires_auth
def revoke_access(portfolio_id, username):
    authenticated_username = g.current_user.get('username')
    
    try:
        # Check if portfolio exists and user owns it
        portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Only portfolio owner can revoke access
        if portfolio.owner != authenticated_username:
            return jsonify({'error': 'Access denied - only the portfolio owner can revoke access'}), 403
        
        # Prevent self-revoking (owner can't revoke their own access)
        if username == authenticated_username:
            return jsonify({'error': 'Cannot revoke access from portfolio owner'}), 400
        
        # Revoke access via service
        portfolio_access_service.revoke_access(portfolio_id, username)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully revoked access for {username}',
            'portfolio_id': portfolio_id,
            'username': username
        }), 200
        
    except PortfolioAccessError as e:
        return jsonify({'error': 'Access management error', 'detail': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


@portfolio_bp.route('/<int:portfolio_id>/access', methods=['GET'])
@requires_auth
def get_portfolio_access(portfolio_id):
    authenticated_username = g.current_user.get('username')
    
    try:
        # Check ownership for authorization (service will validate portfolio exists)
        portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
        if portfolio and portfolio.owner != authenticated_username:
            return jsonify({'error': 'Access denied - only the portfolio owner can view access list'}), 403
        
        # Get access list via service (service validates portfolio existence)
        access_list = portfolio_access_service.get_access(portfolio_id)
        
        # Add owner to the response (owner always has full access)
        result = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name if portfolio else 'Unknown',
            'owner': {
                'username': portfolio.owner if portfolio else authenticated_username,
                'role': 'owner'
            },
            'granted_access': access_list,
            'total_users_with_access': len(access_list) + 1  # +1 for owner
        }
        
        return jsonify(result), 200
        
    except PortfolioAccessError as e:
        return jsonify({'error': 'Access management error', 'detail': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500