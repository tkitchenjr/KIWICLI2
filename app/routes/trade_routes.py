from flask import Blueprint, jsonify, request

from app.db import db
from app.service import trade_service

from app.routes.domain.request import ExecutePurchaseOrderRequest, LiquidateInvestmentRequest

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
def execute_purchase_order():
    execute_purchase_order_request = ExecutePurchaseOrderRequest(**request.get_json())
    trade_service.execute_purchase_order(
        portfolio_id=execute_purchase_order_request.portfolio_id,
        ticker=execute_purchase_order_request.ticker,
        quantity=execute_purchase_order_request.quantity,
    )
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201


@trade_bp.route('/sell', methods=['POST'])
def liquidate_investment():
    liquidate_investment_request = LiquidateInvestmentRequest(**request.get_json())
    trade_service.liquidate_investment(
        portfolio_id=liquidate_investment_request.portfolio_id,
        ticker=liquidate_investment_request.ticker,
        quantity=liquidate_investment_request.quantity,
        sale_price=liquidate_investment_request.sale_price,
    )
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200
   