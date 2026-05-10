from dataclasses import dataclass

import app.auth.auth as auth
import app.routes.security_routes as security_routes
from app import create_app
from app.config import TestConfig


@dataclass
class DummyQuote:
    ticker: str
    date: str
    price: float
    issuer: str


class DummyTransaction:
    def __init__(self, owner=None, ticker='AAPL'):
        if owner is None:
            self.portfolio = None
        else:
            self.portfolio = type('P', (), {'owner': owner})()
        self.ticker = ticker

    def __to_dict__(self):
        return {'ticker': self.ticker}


def _client(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(auth, 'validate_token', lambda _token: {'username': 'admin'})
    return app.test_client()


def test_get_security_success(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(
        security_routes.security_service,
        'get_security_by_ticker',
        lambda _ticker: DummyQuote(ticker='AAPL', date='2026-01-01', price=150.0, issuer='Apple Inc.'),
    )

    response = client.get('/securities/AAPL')

    assert response.status_code == 200
    assert response.get_json()['ticker'] == 'AAPL'


def test_get_security_not_found(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(security_routes.security_service, 'get_security_by_ticker', lambda _ticker: None)

    response = client.get('/securities/NOPE')

    assert response.status_code == 404


def test_get_security_transactions_filters_by_owner(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(
        security_routes.transaction_service,
        'get_transactions_by_ticker',
        lambda _ticker: [DummyTransaction(owner='admin', ticker='AAPL'), DummyTransaction(owner='other', ticker='AAPL'), DummyTransaction(owner=None, ticker='AAPL')],
    )

    response = client.get('/securities/AAPL/transactions', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['ticker'] == 'AAPL'
