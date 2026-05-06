from flask import Blueprint, jsonify, request, g

from app.db import db
from app.service import trade_service
from app.auth.auth import requires_auth
import app.service.portfolio_access_service as portfolio_access_service
import app.service.portfolio_service as portfolio_service
from app.service.portfolio_access_service import PortfolioAccessError

from app.routes.domain.request import ExecutePurchaseOrderRequest, LiquidateInvestmentRequest

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
@requires_auth
def execute_purchase_order():
    authenticated_username = g.current_user.get('username')
    
    try:
        execute_purchase_order_request = ExecutePurchaseOrderRequest(**request.get_json())
        
        portfolio = portfolio_service.get_portfolio_by_id(execute_purchase_order_request.portfolio_id)
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Check authorization (manager level required for trading)
        if portfolio.owner == authenticated_username:
            # Owner has full access
            pass
        else:
            # Check granted access - must be manager to trade
            user_role = portfolio_access_service.check_user_access(execute_purchase_order_request.portfolio_id, authenticated_username)
            if user_role != 'manager':
                return jsonify({'error': 'Access denied - manager access required for trading'}), 403
        
        trade_service.execute_purchase_order(
            portfolio_id=execute_purchase_order_request.portfolio_id,
            ticker=execute_purchase_order_request.ticker,
            quantity=execute_purchase_order_request.quantity,
        )
        db.session.commit()
        return jsonify({'message': 'Purchase order executed successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


@trade_bp.route('/sell', methods=['POST'])
@requires_auth
def liquidate_investment():
    authenticated_username = g.current_user.get('username')
    
    try:
        liquidate_investment_request = LiquidateInvestmentRequest(**request.get_json())
        
        portfolio = portfolio_service.get_portfolio_by_id(liquidate_investment_request.portfolio_id)
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Check authorization (manager level required for trading)
        if portfolio.owner == authenticated_username:
            # Owner has full access
            pass
        else:
            # Check granted access - must be manager to trade
            user_role = portfolio_access_service.check_user_access(liquidate_investment_request.portfolio_id, authenticated_username)
            if user_role != 'manager':
                return jsonify({'error': 'Access denied - manager access required for trading'}), 403
        
        trade_service.liquidate_investment(
            portfolio_id=liquidate_investment_request.portfolio_id,
            ticker=liquidate_investment_request.ticker,
            quantity=liquidate_investment_request.quantity,
            sale_price=liquidate_investment_request.sale_price,
        )
        db.session.commit()
        return jsonify({'message': 'Investment liquidated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500
   