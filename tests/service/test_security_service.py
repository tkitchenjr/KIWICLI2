import pytest
from app.models import User, Portfolio
from app.service.portfolio_service import create_portfolio
from app.service.trade_service import TradeExecutionException, InsufficientFundsError, execute_purchase_order
from app.service.security_service import SecurityException, get_security_by_ticker
from app.service import transaction_service
from app.service.user_service import create_user
import app.service.alpha_vantage_client as alpha_client
from app.service.alpha_vantage_client import get_quote, get_company_name, get_price_data, get_api_key

@pytest.fixture()
def setup(db_session):
    create_user(username="user", password="secret", firstname="Firstname", lastname="Lastname", balance=1000.00)
    user = db_session.query(User).filter_by(username="user").one()
    assert user is not None
    create_portfolio("Test Portfolio", "Test Portfolio Description", user)
    portfolio = db_session.query(Portfolio).filter_by(name="Test Portfolio").one()
    assert portfolio is not None
    return {
        "user": user,
        "portfolio": portfolio
    }

def test_get_security_by_ticker(monkeypatch):
    import app.service.security_service as security_svc
    monkeypatch.setattr(security_svc, 'get_company_name', lambda ticker: 'Apple Inc.')
    
    security = get_security_by_ticker('AAPL')
    assert security is not None

def test_get_security_by_ticker_exception(monkeypatch):
    import app.service.security_service as security_svc
    monkeypatch.setattr(security_svc, 'get_company_name', lambda _: (_ for _ in ()).throw(Exception('API error')))
    with pytest.raises(SecurityException) as e:
        get_security_by_ticker('AAPL')
    assert 'Failed to retrieve security due to error: API error' in str(e.value)

def test_execute_purchase_order(setup, db_session, monkeypatch):
    monkeypatch.setattr(
        'app.service.trade_service.get_quote',
        lambda _ticker: alpha_client.SecurityQuote(ticker='AAPL', date='2026-01-01', price=150.0, issuer='Apple Inc.'),
    )

    portfolio = setup["portfolio"]
    user = db_session.query(User).filter_by(username="user").one()
    assert user.balance == 1000.00
    assert len(transaction_service.get_transactions_by_portfolio_id(portfolio.id)) == 0
    
    execute_purchase_order(portfolio.id, "AAPL", 2)
    
    user = db_session.query(User).filter_by(username="user").one()
    assert user.balance == 700.00
    assert len(user.portfolios[0].investments) == 1
    assert user.portfolios[0].investments[0].ticker == "AAPL"
    assert user.portfolios[0].investments[0].quantity == 2
    
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio.id)
    assert len(transactions) == 1
    assert transactions[0].ticker == "AAPL" and transactions[0].quantity == 2
    assert transactions[0].price == 150.00 and transactions[0].transaction_type == "BUY"

def test_execute_purchase_order_insufficient_funds(setup, db_session, monkeypatch):
    monkeypatch.setattr(
        'app.service.trade_service.get_quote',
        lambda _ticker: alpha_client.SecurityQuote(ticker='GOOGL', date='2026-01-01', price=2800.0, issuer='Alphabet Inc.'),
    )

    portfolio = setup["portfolio"]
    with pytest.raises(InsufficientFundsError) as e:
        execute_purchase_order(portfolio.id, "GOOGL", 1)
    assert str(e.value) == "Insufficient funds to complete the purchase."

def test_execute_order_for_nonexistent_portfolio(db_session):
    with pytest.raises(TradeExecutionException) as e:
        execute_purchase_order(999, "AAPL", 1)
    assert "Portfolio with id 999 does not exist." in str(e.value)

def test_execute_order_for_nonexistent_security(setup, db_session, monkeypatch):
    monkeypatch.setattr('app.service.trade_service.get_quote', lambda _ticker: None)

    portfolio = setup["portfolio"]
    with pytest.raises(TradeExecutionException) as e:
        execute_purchase_order(portfolio.id, "INVALID", 1)
    assert "Security with ticker INVALID does not exist." in str(e.value)

# ---------------------------------------------------------------------------
# get_company_name cache tests
# ---------------------------------------------------------------------------

def test_get_company_name_cache_miss_hits_api(monkeypatch):
    monkeypatch.setattr(alpha_client.cache, 'get', lambda _key: None)
    monkeypatch.setattr(alpha_client.cache, 'set', lambda _key, _val: None)
    monkeypatch.setattr(alpha_client, 'get_api_key', lambda: 'fake-key')
    monkeypatch.setattr(alpha_client.requests, 'get', lambda _url: type('R', (), {'raise_for_status': lambda s: None, 'json': lambda s: {'Name': 'Apple Inc.'}})())

    assert get_company_name('AAPL') == 'Apple Inc.'


def test_get_company_name_cache_hit_skips_api(monkeypatch):
    monkeypatch.setattr(alpha_client.cache, 'get', lambda _key: 'Apple Inc.')
    monkeypatch.setattr(alpha_client.requests, 'get', lambda _url: (_ for _ in ()).throw(AssertionError('API should not be called')))

    assert get_company_name('AAPL') == 'Apple Inc.'


def test_get_company_name_api_returns_no_name(monkeypatch):
    monkeypatch.setattr(alpha_client.cache, 'get', lambda _key: None)
    monkeypatch.setattr(alpha_client.cache, 'set', lambda _key, _val: None)
    monkeypatch.setattr(alpha_client, 'get_api_key', lambda: 'fake-key')
    monkeypatch.setattr(alpha_client.requests, 'get', lambda _url: type('R', (), {'raise_for_status': lambda s: None, 'json': lambda s: {'Symbol': 'AAPL'}})())

    assert get_company_name('AAPL') is None


# ---------------------------------------------------------------------------
# get_price_data cache tests
# ---------------------------------------------------------------------------

_FAKE_PRICE_RESPONSE = {'Time Series (5min)': {'2026-01-01 09:35:00': {'4. close': '150.00'}}}
_CACHED_PRICE = {'date': '2026-01-01 09:35:00', 'close': 150.0}


def test_get_price_data_cache_miss_hits_api(monkeypatch):
    monkeypatch.setattr(alpha_client.cache, 'get', lambda _key: None)
    monkeypatch.setattr(alpha_client.cache, 'set', lambda _key, _val: None)
    monkeypatch.setattr(alpha_client, 'get_api_key', lambda: 'fake-key')
    monkeypatch.setattr(alpha_client.requests, 'get', lambda _url: type('R', (), {'raise_for_status': lambda s: None, 'json': lambda s: _FAKE_PRICE_RESPONSE})())

    assert get_price_data('AAPL') == _CACHED_PRICE


def test_get_price_data_cache_hit_skips_api(monkeypatch):
    monkeypatch.setattr(alpha_client.cache, 'get', lambda _key: _CACHED_PRICE)
    monkeypatch.setattr(alpha_client.requests, 'get', lambda _url: (_ for _ in ()).throw(AssertionError('API should not be called')))

    assert get_price_data('AAPL') == _CACHED_PRICE


def test_get_price_data_api_returns_no_time_series(monkeypatch):
    monkeypatch.setattr(alpha_client.cache, 'get', lambda _key: None)
    monkeypatch.setattr(alpha_client.cache, 'set', lambda _key, _val: None)
    monkeypatch.setattr(alpha_client, 'get_api_key', lambda: 'fake-key')
    monkeypatch.setattr(alpha_client.requests, 'get', lambda _url: type('R', (), {'raise_for_status': lambda s: None, 'json': lambda s: {'Note': 'API rate limit reached'}})())

    assert get_price_data('AAPL') is None

