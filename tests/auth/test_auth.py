from jose import JWTError
from flask import Flask, jsonify, g

import app.auth.auth as auth


def _build_app():
    app = Flask(__name__)

    @app.route('/protected')
    @auth.requires_auth
    def protected():
        return jsonify({'username': g.current_user.get('username')}), 200

    return app


def test_protected_route_no_token_returns_403():
    app = _build_app()
    client = app.test_client()

    response = client.get('/protected')

    assert response.status_code == 403


def test_protected_route_expired_token_returns_403(monkeypatch):
    app = _build_app()
    client = app.test_client()
    monkeypatch.setattr(auth, 'validate_token', lambda _token: (_ for _ in ()).throw(JWTError('Signature has expired')))

    response = client.get('/protected', headers={'Authorization': 'Bearer expired'})

    assert response.status_code == 403


def test_protected_route_invalid_signature_returns_403(monkeypatch):
    app = _build_app()
    client = app.test_client()
    monkeypatch.setattr(auth, 'validate_token', lambda _token: (_ for _ in ()).throw(JWTError('Signature verification failed')))

    response = client.get('/protected', headers={'Authorization': 'Bearer bad-signature'})

    assert response.status_code == 403


def test_protected_route_valid_token_allows_access(monkeypatch):
    app = _build_app()
    client = app.test_client()
    monkeypatch.setattr(auth, 'validate_token', lambda _token: {'username': 'owner1', 'role': 'owner'})

    response = client.get('/protected', headers={'Authorization': 'Bearer good'})

    assert response.status_code == 200
    assert response.get_json()['username'] == 'owner1'
