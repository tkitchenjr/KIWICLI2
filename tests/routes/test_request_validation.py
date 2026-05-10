import pytest
from pydantic import ValidationError

import app.auth.auth as auth
from app import create_app
from app.config import TestConfig
from app.routes.domain.request import (
    CreatePortfolioRequest,
    CreateUserRequest,
    ExecutePurchaseOrderRequest,
    LiquidateInvestmentRequest,
    UpdateBalanceRequest,
)


def test_create_user_request_valid():
    model = CreateUserRequest(
        username='user1',
        password='secret',
        firstname='First',
        lastname='Last',
        balance=100.0,
    )
    assert model.username == 'user1'


def test_create_user_request_invalid_missing_field():
    with pytest.raises(ValidationError):
        CreateUserRequest(username='user1', password='secret', firstname='First', balance=100.0)


def test_create_portfolio_request_invalid_missing_field():
    with pytest.raises(ValidationError):
        CreatePortfolioRequest(name='Main', description='Long term')


def test_update_balance_request_invalid_negative_balance():
    with pytest.raises(ValidationError):
        UpdateBalanceRequest(username='user1', new_balance=-1)


def test_execute_purchase_order_request_invalid_quantity():
    with pytest.raises(ValidationError):
        ExecutePurchaseOrderRequest(portfolio_id=1, ticker='AAPL', quantity=0)


def test_liquidate_investment_request_invalid_sale_price():
    with pytest.raises(ValidationError):
        LiquidateInvestmentRequest(portfolio_id=1, ticker='AAPL', quantity=1, sale_price=0)


def test_centralized_validation_handler_returns_expected_http_response(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(auth, 'validate_token', lambda _token: {'username': 'admin', 'role': 'owner'})
    client = app.test_client()

    response = client.post(
        '/trades/buy',
        headers={'Authorization': 'Bearer token'},
        json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 0},
    )

    assert response.status_code == 422
    body = response.get_json()
    assert body['error'] == 'Validation Error'
    assert 'quantity' in body['detail']
