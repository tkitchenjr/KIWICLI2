import app.auth.auth as auth
from app import create_app
from app.config import TestConfig


def test_create_app_registers_blueprints():
    app = create_app(TestConfig)

    assert app is not None
    assert 'user' in app.blueprints
    assert 'portfolio' in app.blueprints
    assert 'security' in app.blueprints
    assert 'trade' in app.blueprints


def test_validation_error_handler_returns_422(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(auth, 'validate_token', lambda _token: {'username': 'admin'})

    client = app.test_client()
    response = client.post(
        '/trades/buy',
        headers={'Authorization': 'Bearer valid'},
        json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 0},
    )

    assert response.status_code == 422
    body = response.get_json()
    assert body['error'] == 'Validation Error'
    assert 'quantity' in body['detail']
