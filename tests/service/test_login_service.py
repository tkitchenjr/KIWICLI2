from __future__ import annotations

import pytest
from app.models import User
from app.auth.auth import _validate_auth_config, _get_jwks_url, _get_jwks, requires_auth


from flask import Flask, jsonify, g
import pytest

import app.auth.auth as auth


def _test_app() -> Flask:
    app = Flask(__name__)

    @app.route('/protected', methods=['GET'])
    @auth.requires_auth
    def protected():
        return jsonify({'ok': True, 'username': g.current_user.get('username')}), 200

    return app


def test_validate_auth_config_returns_expected_values(monkeypatch):
    monkeypatch.setattr(auth, 'COGNITO_REGION', 'us-east-1')
    monkeypatch.setattr(auth, 'COGNITO_POOL_ID', 'pool123')
    monkeypatch.setattr(auth, 'COGNITO_CLIENT_ID', 'client123')

    region, pool_id, client_id = auth._validate_auth_config()

    assert region == 'us-east-1'
    assert pool_id == 'pool123'
    assert client_id == 'client123'


def test_validate_auth_config_missing_region_raises(monkeypatch):
    monkeypatch.setattr(auth, 'COGNITO_REGION', None)
    monkeypatch.setattr(auth, 'COGNITO_POOL_ID', 'pool123')
    monkeypatch.setattr(auth, 'COGNITO_CLIENT_ID', 'client123')

    with pytest.raises(ValueError) as e:
        auth._validate_auth_config()

    assert 'COGNITO_REGION' in str(e.value)


def test_get_jwks_uses_cache(monkeypatch):
    calls = {'count': 0}

    class _FakeResponse:
        @staticmethod
        def json():
            return {'keys': [{'kid': 'kid-1', 'kty': 'RSA'}]}

    def _fake_get(_):
        calls['count'] += 1
        return _FakeResponse()

    monkeypatch.setattr(auth, '_jwks_cache', None)
    monkeypatch.setattr(auth, '_get_jwks_url', lambda: 'https://example.test/jwks.json')
    monkeypatch.setattr(auth.requests, 'get', _fake_get)

    jwks_first = auth._get_jwks()
    jwks_second = auth._get_jwks()

    assert calls['count'] == 1
    assert jwks_first == jwks_second
    assert jwks_first['kid-1']['kty'] == 'RSA'


def test_validate_token_success(monkeypatch):
    monkeypatch.setattr(auth.jwt, 'get_unverified_header', lambda _: {'kid': 'kid-1'})
    monkeypatch.setattr(auth, '_get_jwks', lambda: {'kid-1': {'kty': 'RSA'}})
    monkeypatch.setattr(auth.jwk, 'construct', lambda _: 'public-key')
    monkeypatch.setattr(auth, '_validate_auth_config', lambda: ('us-east-1', 'pool123', 'client123'))
    monkeypatch.setattr(
        auth.jwt,
        'decode',
        lambda *_args, **_kwargs: {'token_use': 'access', 'username': 'admin'},
    )

    claims = auth.validate_token('token-value')

    assert claims['username'] == 'admin'
    assert claims['token_use'] == 'access'


def test_validate_token_rejects_non_access_token(monkeypatch):
    monkeypatch.setattr(auth.jwt, 'get_unverified_header', lambda _: {'kid': 'kid-1'})
    monkeypatch.setattr(auth, '_get_jwks', lambda: {'kid-1': {'kty': 'RSA'}})
    monkeypatch.setattr(auth.jwk, 'construct', lambda _: 'public-key')
    monkeypatch.setattr(auth, '_validate_auth_config', lambda: ('us-east-1', 'pool123', 'client123'))
    monkeypatch.setattr(auth.jwt, 'decode', lambda *_args, **_kwargs: {'token_use': 'id', 'username': 'admin'})

    with pytest.raises(ValueError) as e:
        auth.validate_token('token-value')

    assert str(e.value) == 'Not an access token'


def test_requires_auth_missing_header_returns_403():
    app = _test_app()
    client = app.test_client()

    response = client.get('/protected')

    assert response.status_code == 403
    assert response.get_json() == {'error': 'Missing or invalid Authorization header'}


def test_requires_auth_invalid_token_returns_403(monkeypatch):
    app = _test_app()
    client = app.test_client()

    def _raise_invalid(_):
        raise ValueError('invalid token')

    monkeypatch.setattr(auth, 'validate_token', _raise_invalid)

    response = client.get('/protected', headers={'Authorization': 'Bearer bad-token'})

    assert response.status_code == 403
    assert response.get_json() == {'error': 'Invalid token'}


def test_requires_auth_valid_token_allows_request(monkeypatch):
    app = _test_app()
    client = app.test_client()

    monkeypatch.setattr(auth, 'validate_token', lambda _: {'username': 'admin', 'token_use': 'access'})

    response = client.get('/protected', headers={'Authorization': 'Bearer good-token'})

    assert response.status_code == 200
    assert response.get_json() == {'ok': True, 'username': 'admin'}
    