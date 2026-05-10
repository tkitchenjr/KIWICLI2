import app.auth.auth as auth
import app.routes.trade_routes as trade_routes
from app import create_app
from app.config import TestConfig


class DummyPortfolio:
    def __init__(self, owner='admin'):
        self.owner = owner


def _client(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(auth, 'validate_token', lambda _token: {'username': 'admin'})
    return app.test_client()


def test_buy_success_commits(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}
    called = {'count': 0}

    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: DummyPortfolio('admin'))
    monkeypatch.setattr(
        trade_routes.trade_service,
        'execute_purchase_order',
        lambda **_kwargs: called.__setitem__('count', called['count'] + 1),
    )
    monkeypatch.setattr(
        trade_routes.db.session,
        'commit',
        lambda: committed.__setitem__('count', committed['count'] + 1),
    )

    response = client.post(
        '/trades/buy',
        headers={'Authorization': 'Bearer valid'},
        json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 2},
    )

    assert response.status_code == 201
    assert called['count'] == 1
    assert committed['count'] == 1


def test_buy_portfolio_not_found_no_commit(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}

    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: None)
    monkeypatch.setattr(
        trade_routes.db.session,
        'commit',
        lambda: committed.__setitem__('count', committed['count'] + 1),
    )

    response = client.post(
        '/trades/buy',
        headers={'Authorization': 'Bearer valid'},
        json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 2},
    )

    assert response.status_code == 404
    assert committed['count'] == 0


def test_buy_forbidden_no_commit(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}

    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: DummyPortfolio('other-user'))
    monkeypatch.setattr(
        trade_routes.db.session,
        'commit',
        lambda: committed.__setitem__('count', committed['count'] + 1),
    )

    response = client.post(
        '/trades/buy',
        headers={'Authorization': 'Bearer valid'},
        json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 2},
    )

    assert response.status_code == 403
    assert committed['count'] == 0


def test_sell_success_commits(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}
    called = {'count': 0}

    monkeypatch.setattr('app.service.portfolio_service.get_portfolio_by_id', lambda _pid: DummyPortfolio('admin'))
    monkeypatch.setattr(
        trade_routes.trade_service,
        'liquidate_investment',
        lambda **_kwargs: called.__setitem__('count', called['count'] + 1),
    )
    monkeypatch.setattr(
        trade_routes.db.session,
        'commit',
        lambda: committed.__setitem__('count', committed['count'] + 1),
    )

    response = client.post(
        '/trades/sell',
        headers={'Authorization': 'Bearer valid'},
        json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1, 'sale_price': 150.0},
    )

    assert response.status_code == 200
    assert called['count'] == 1
    assert committed['count'] == 1


def test_sell_validation_error_422(monkeypatch):
    client = _client(monkeypatch)

    response = client.post(
        '/trades/sell',
        headers={'Authorization': 'Bearer valid'},
        json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 0, 'sale_price': 150.0},
    )

    assert response.status_code == 422
