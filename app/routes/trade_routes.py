from flask import Blueprint, jsonify, request

from app.auth.auth import requires_auth
from app.db import db
from app.service import trade_service
from app.service.alpha_vantage_client import get_price_data

from app.routes.domain.request import ExecutePurchaseOrderRequest, LiquidateInvestmentRequest
from app.routes.domain.response import ErrorResponse

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
@requires_auth
def execute_purchase_order():
    try:
        execute_purchase_order_request = ExecutePurchaseOrderRequest(**request.get_json())
        trade_service.execute_purchase_order(
            portfolio_id=execute_purchase_order_request.portfolio_id,
            ticker=execute_purchase_order_request.ticker,
            quantity=execute_purchase_order_request.quantity,
        )
        db.session.commit()
        return jsonify({'message': 'Purchase order executed successfully'}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify(ErrorResponse(error='Trade failed', detail=str(error)).model_dump()), 400


@trade_bp.route('/sell', methods=['POST'])
@requires_auth
def liquidate_investment():
    try:
        liquidate_investment_request = LiquidateInvestmentRequest(**request.get_json())
        sale_price = liquidate_investment_request.sale_price
        if sale_price is None:
            price_data = get_price_data(liquidate_investment_request.ticker)
            if price_data is None:
                return jsonify(ErrorResponse(error='Not found', detail=f'Security {liquidate_investment_request.ticker} not found').model_dump()), 404
            sale_price = float(price_data['close'])

        trade_service.liquidate_investment(
            portfolio_id=liquidate_investment_request.portfolio_id,
            ticker=liquidate_investment_request.ticker,
            quantity=liquidate_investment_request.quantity,
            sale_price=sale_price,
        )
        db.session.commit()
        return jsonify({'message': 'Investment liquidated successfully'}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify(ErrorResponse(error='Trade failed', detail=str(error)).model_dump()), 400
   