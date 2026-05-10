import app.auth.auth as auth
import app.routes.portfolio_routes as portfolio_routes
from app import create_app
from app.config import TestConfig


class DummyUser:
    def __init__(self, username='admin'):
        self.username = username


class DummyPortfolio:
    def __init__(self, owner='admin', portfolio_id=1):
        self.owner = owner
        self.id = portfolio_id

    def __to_dict__(self):
        return {'id': self.id, 'owner': self.owner, 'name': 'Main', 'description': 'Portfolio'}


class DummyTransaction:
    def __to_dict__(self):
        return {'transaction_id': 1, 'ticker': 'AAPL'}


def _client(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(auth, 'validate_token', lambda _token: {'username': 'admin'})
    return app.test_client()


def test_get_all_portfolios_success(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(portfolio_routes.user_service, 'get_user_by_username', lambda _u: DummyUser('admin'))
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'get_portfolios_by_user', lambda _u: [DummyPortfolio('admin', 7)])

    response = client.get('/portfolios/', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 200
    assert response.get_json()[0]['id'] == 7


def test_get_portfolio_forbidden(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'get_portfolio_by_id', lambda _pid: DummyPortfolio('other-user', 3))

    response = client.get('/portfolios/3', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 403


def test_create_portfolio_commits(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}
    monkeypatch.setattr(portfolio_routes.user_service, 'get_user_by_username', lambda _u: DummyUser('admin'))
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'create_portfolio', lambda **_kwargs: 12)
    monkeypatch.setattr(
        portfolio_routes.db.session,
        'commit',
        lambda: committed.__setitem__('count', committed['count'] + 1),
    )

    response = client.post(
        '/portfolios/',
        headers={'Authorization': 'Bearer valid'},
        json={'name': 'Growth', 'description': 'Long term', 'username': 'admin'},
    )

    assert response.status_code == 201
    assert response.get_json()['portfolio_id'] == 12
    assert committed['count'] == 1


def test_create_portfolio_forbidden_no_commit(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}
    monkeypatch.setattr(
        portfolio_routes.db.session,
        'commit',
        lambda: committed.__setitem__('count', committed['count'] + 1),
    )

    response = client.post(
        '/portfolios/',
        headers={'Authorization': 'Bearer valid'},
        json={'name': 'Growth', 'description': 'Long term', 'username': 'someone-else'},
    )

    assert response.status_code == 403
    assert committed['count'] == 0


def test_get_portfolio_transactions_forbidden(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'get_portfolio_by_id', lambda _pid: DummyPortfolio('other-user', 9))

    response = client.get('/portfolios/9/transactions', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 403


def test_get_portfolio_transactions_success(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(portfolio_routes.portfolio_service, 'get_portfolio_by_id', lambda _pid: DummyPortfolio('admin', 9))
    monkeypatch.setattr(portfolio_routes.transaction_service, 'get_transactions_by_portfolio_id', lambda _pid: [DummyTransaction()])

    response = client.get('/portfolios/9/transactions', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 200
    assert response.get_json()[0]['ticker'] == 'AAPL'
