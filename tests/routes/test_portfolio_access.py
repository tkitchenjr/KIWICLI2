import app.auth.auth as auth
import app.routes.portfolio_routes as portfolio_routes
import app.routes.trade_routes as trade_routes
from app import create_app
from app.config import TestConfig


class DummyPortfolio:
    def __init__(self, owner):
        self.owner = owner


def _client_with_claims(monkeypatch, claims):
    app = create_app(TestConfig)
    monkeypatch.setattr(auth, 'validate_token', lambda _token: claims)
    return app.test_client()


def test_owner_can_create_delete_and_trade(monkeypatch):
    client = _client_with_claims(monkeypatch, {'username': 'owner1', 'role': 'owner'})

    monkeypatch.setattr(portfolio_routes.user_service, 'get_user_by_username', lambda _u: object())
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'create_portfolio', lambda **_kwargs: 1)
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'get_portfolio_by_id', lambda _pid: DummyPortfolio('owner1'))
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'delete_portfolio', lambda _pid: None)

    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: DummyPortfolio('owner1'))
    monkeypatch.setattr(trade_routes.trade_service, 'execute_purchase_order', lambda **_kwargs: None)

    assert client.post('/portfolios/', headers={'Authorization': 'Bearer owner'}, json={'name': 'P1', 'description': 'Main', 'username': 'owner1'}).status_code == 201
    assert client.delete('/portfolios/1', headers={'Authorization': 'Bearer owner'}).status_code == 200
    assert client.post('/trades/buy', headers={'Authorization': 'Bearer owner'}, json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1}).status_code == 201


def test_viewer_cannot_execute_trades(monkeypatch):
    client = _client_with_claims(monkeypatch, {'username': 'viewer1', 'role': 'viewer'})
    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: DummyPortfolio('owner1'))

    response = client.post('/trades/buy', headers={'Authorization': 'Bearer viewer'}, json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1})

    assert response.status_code == 403


def test_manager_can_trade_but_cannot_create_or_delete_portfolios(monkeypatch):
    client = _client_with_claims(monkeypatch, {'username': 'manager1', 'role': 'manager'})

    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: DummyPortfolio('owner1'))
    monkeypatch.setattr(trade_routes.trade_service, 'execute_purchase_order', lambda **_kwargs: None)
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'get_portfolio_by_id', lambda _pid: DummyPortfolio('owner1'))

    buy_response = client.post('/trades/buy', headers={'Authorization': 'Bearer manager'}, json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1})
    create_response = client.post('/portfolios/', headers={'Authorization': 'Bearer manager'}, json={'name': 'P1', 'description': 'Main', 'username': 'manager1'})
    delete_response = client.delete('/portfolios/1', headers={'Authorization': 'Bearer manager'})

    assert buy_response.status_code == 201
    assert create_response.status_code == 403
    assert delete_response.status_code == 403


def test_no_access_user_gets_403(monkeypatch):
    client = _client_with_claims(monkeypatch, {'username': 'blocked1', 'role': 'none'})
    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: DummyPortfolio('owner1'))

    buy_response = client.post('/trades/buy', headers={'Authorization': 'Bearer blocked'}, json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1})
    create_response = client.post('/portfolios/', headers={'Authorization': 'Bearer blocked'}, json={'name': 'P1', 'description': 'Main', 'username': 'blocked1'})

    assert buy_response.status_code == 403
    assert create_response.status_code == 403
