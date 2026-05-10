import app.service.alpha_vantage_client as av


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_get_company_name_success(monkeypatch):
    monkeypatch.setattr(av.cache, 'get', lambda _key: None)
    monkeypatch.setattr(av.cache, 'set', lambda _key, _value: None)
    monkeypatch.setattr(av, 'get_api_key', lambda: 'fake-key')
    monkeypatch.setattr(av.requests, 'get', lambda _url: DummyResponse({'Name': 'Apple Inc.'}))

    assert av.get_company_name('AAPL') == 'Apple Inc.'


def test_get_company_name_returns_none_for_empty_or_unexpected(monkeypatch):
    monkeypatch.setattr(av.cache, 'get', lambda _key: None)
    monkeypatch.setattr(av.cache, 'set', lambda _key, _value: None)
    monkeypatch.setattr(av, 'get_api_key', lambda: 'fake-key')

    monkeypatch.setattr(av.requests, 'get', lambda _url: DummyResponse({}))
    assert av.get_company_name('AAPL') is None

    monkeypatch.setattr(av.requests, 'get', lambda _url: DummyResponse({'Symbol': 'AAPL'}))
    assert av.get_company_name('AAPL') is None


def test_get_price_data_success(monkeypatch):
    payload = {'Time Series (5min)': {'2026-01-01 10:00:00': {'4. close': '150.00'}}}
    monkeypatch.setattr(av.cache, 'get', lambda _key: None)
    monkeypatch.setattr(av.cache, 'set', lambda _key, _value: None)
    monkeypatch.setattr(av, 'get_api_key', lambda: 'fake-key')
    monkeypatch.setattr(av.requests, 'get', lambda _url: DummyResponse(payload))

    assert av.get_price_data('AAPL') == {'date': '2026-01-01 10:00:00', 'close': 150.0}


def test_get_price_data_returns_none_for_empty_or_unexpected(monkeypatch):
    monkeypatch.setattr(av.cache, 'get', lambda _key: None)
    monkeypatch.setattr(av.cache, 'set', lambda _key, _value: None)
    monkeypatch.setattr(av, 'get_api_key', lambda: 'fake-key')

    monkeypatch.setattr(av.requests, 'get', lambda _url: DummyResponse({}))
    assert av.get_price_data('AAPL') is None

    monkeypatch.setattr(av.requests, 'get', lambda _url: DummyResponse({'Note': 'Rate limit'}))
    assert av.get_price_data('AAPL') is None


def test_cache_hit_skips_api_and_cache_miss_invokes_api_for_company_name(monkeypatch):
    calls = {'count': 0}

    def fake_get(_url):
        calls['count'] += 1
        return DummyResponse({'Name': 'Apple Inc.'})

    monkeypatch.setattr(av, 'get_api_key', lambda: 'fake-key')

    monkeypatch.setattr(av.cache, 'get', lambda _key: 'Cached Co')
    monkeypatch.setattr(av.requests, 'get', fake_get)
    assert av.get_company_name('AAPL') == 'Cached Co'
    assert calls['count'] == 0

    store = {'value': None}
    monkeypatch.setattr(av.cache, 'get', lambda _key: None)
    monkeypatch.setattr(av.cache, 'set', lambda _key, value: store.__setitem__('value', value))
    assert av.get_company_name('AAPL') == 'Apple Inc.'
    assert calls['count'] == 1
    assert store['value'] == 'Apple Inc.'


def test_cache_hit_skips_api_and_cache_miss_invokes_api_for_price_data(monkeypatch):
    calls = {'count': 0}
    payload = {'Time Series (5min)': {'2026-01-01 10:00:00': {'4. close': '150.00'}}}

    def fake_get(_url):
        calls['count'] += 1
        return DummyResponse(payload)

    monkeypatch.setattr(av, 'get_api_key', lambda: 'fake-key')

    cached = {'date': '2026-01-01 10:00:00', 'close': 150.0}
    monkeypatch.setattr(av.cache, 'get', lambda _key: cached)
    monkeypatch.setattr(av.requests, 'get', fake_get)
    assert av.get_price_data('AAPL') == cached
    assert calls['count'] == 0

    store = {'value': None}
    monkeypatch.setattr(av.cache, 'get', lambda _key: None)
    monkeypatch.setattr(av.cache, 'set', lambda _key, value: store.__setitem__('value', value))
    assert av.get_price_data('AAPL') == cached
    assert calls['count'] == 1
    assert store['value'] == cached
