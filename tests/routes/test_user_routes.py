import app.auth.auth as auth
import app.routes.user_routes as user_routes
from app import create_app
from app.config import TestConfig


class DummyUser:
    def __init__(self, username='admin'):
        self.username = username

    def __to_dict__(self):
        return {
            'username': self.username,
            'firstname': 'Admin',
            'lastname': 'User',
            'balance': 1000.0,
        }


def _client(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(auth, 'validate_token', lambda _token: {'username': 'admin'})
    return app.test_client()


def test_get_users_success(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(user_routes.user_service, 'get_user_by_username', lambda _username: DummyUser('admin'))

    response = client.get('/users/', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 200
    assert response.get_json()[0]['username'] == 'admin'


def test_get_user_forbidden(monkeypatch):
    client = _client(monkeypatch)

    response = client.get('/users/someone-else', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 403
    assert response.get_json()['error'].startswith('Access denied')


def test_create_user_commits(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}

    monkeypatch.setattr(user_routes.user_service, 'create_user', lambda **_kwargs: None)
    monkeypatch.setattr(user_routes.db.session, 'commit', lambda: committed.__setitem__('count', committed['count'] + 1))

    response = client.post(
        '/users/',
        json={
            'username': 'newuser',
            'password': 'secret',
            'firstname': 'New',
            'lastname': 'User',
            'balance': 100.0,
        },
    )

    assert response.status_code == 201
    assert response.get_json()['message'] == 'User created successfully'
    assert committed['count'] == 1


def test_update_balance_forbidden_does_not_commit(monkeypatch):
    client = _client(monkeypatch)
    committed = {'count': 0}

    monkeypatch.setattr(user_routes.db.session, 'commit', lambda: committed.__setitem__('count', committed['count'] + 1))

    response = client.put(
        '/users/update-balance',
        headers={'Authorization': 'Bearer valid'},
        json={'username': 'other-user', 'new_balance': 500.0},
    )

    assert response.status_code == 403
    assert committed['count'] == 0


def test_delete_user_not_found(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(user_routes.user_service, 'get_user_by_username', lambda _username: None)

    response = client.delete('/users/missing', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 404
    assert response.get_json()['error'] == 'Not found'
