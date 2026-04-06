from flask import Blueprint, jsonify, request, g

from app.db import db
from app.service import trade_service
from app.auth.auth import requires_auth

from app.routes.domain.request import ExecutePurchaseOrderRequest, LiquidateInvestmentRequest

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
@requires_auth
def execute_purchase_order():
    authenticated_username = g.current_user.get('username')
    
    execute_purchase_order_request = ExecutePurchaseOrderRequest(**request.get_json())
    
    # Verify user owns the portfolio they're trying to trade in
    from app.service import portfolio_service
    portfolio = portfolio_service.get_portfolio_by_id(execute_purchase_order_request.portfolio_id)
    if portfolio is None:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    if portfolio.owner != authenticated_username:
        return jsonify({'error': 'Access denied - you can only trade in your own portfolios'}), 403
    
    trade_service.execute_purchase_order(
        portfolio_id=execute_purchase_order_request.portfolio_id,
        ticker=execute_purchase_order_request.ticker,
        quantity=execute_purchase_order_request.quantity,
    )
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201


@trade_bp.route('/sell', methods=['POST'])
@requires_auth
def liquidate_investment():
    authenticated_username = g.current_user.get('username')
    
    liquidate_investment_request = LiquidateInvestmentRequest(**request.get_json())
    
    # Verify user owns the portfolio they're trying to sell from
    from app.service import portfolio_service
    portfolio = portfolio_service.get_portfolio_by_id(liquidate_investment_request.portfolio_id)
    if portfolio is None:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    if portfolio.owner != authenticated_username:
        return jsonify({'error': 'Access denied - you can only trade in your own portfolios'}), 403
    
    trade_service.liquidate_investment(
        portfolio_id=liquidate_investment_request.portfolio_id,
        ticker=liquidate_investment_request.ticker,
        quantity=liquidate_investment_request.quantity,
        sale_price=liquidate_investment_request.sale_price,
    )
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200
   