import datetime

import pytest

from app.models import Portfolio, User
from app.service import transaction_service
import app.service.trade_service as trade_service


@pytest.fixture()
def trade_setup(db_session):
    user = User(username='owner1', password='secret', firstname='Owner', lastname='One', balance=1000.0)
    db_session.add(user)
    db_session.commit()

    portfolio = Portfolio(name='Main', description='Trading', user=user)
    db_session.add(portfolio)
    db_session.commit()

    return {'user': user, 'portfolio': portfolio}


def test_execute_purchase_order_valid_creates_transaction(monkeypatch, db_session, trade_setup):
    monkeypatch.setattr(
        trade_service,
        'get_quote',
        lambda _ticker: type('Q', (), {'price': 150.0, 'ticker': 'AAPL', 'issuer': 'Apple', 'date': '2026-01-01'})(),
    )

    trade_service.execute_purchase_order(trade_setup['portfolio'].id, 'AAPL', 2)
    transactions = transaction_service.get_transactions_by_portfolio_id(trade_setup['portfolio'].id)

    assert len(transactions) == 1
    assert transactions[0].transaction_type == 'BUY'
    assert transactions[0].quantity == 2


def test_execute_purchase_order_invalid_ticker(monkeypatch, trade_setup):
    monkeypatch.setattr(trade_service, 'get_quote', lambda _ticker: None)

    with pytest.raises(trade_service.TradeExecutionException) as e:
        trade_service.execute_purchase_order(trade_setup['portfolio'].id, 'INVALID', 1)
    assert 'does not exist' in str(e.value)


def test_liquidate_investment_insufficient_holdings(monkeypatch, trade_setup):
    monkeypatch.setattr(
        trade_service,
        'get_quote',
        lambda _ticker: type('Q', (), {'price': 100.0, 'ticker': 'AAPL', 'issuer': 'Apple', 'date': '2026-01-01'})(),
    )
    trade_service.execute_purchase_order(trade_setup['portfolio'].id, 'AAPL', 1)

    with pytest.raises(trade_service.TradeExecutionException) as e:
        trade_service.liquidate_investment(trade_setup['portfolio'].id, 'AAPL', 5, 120.0)
    assert 'Only 1 shares available' in str(e.value)


def test_liquidate_investment_valid_creates_sell_transaction(monkeypatch, trade_setup):
    monkeypatch.setattr(
        trade_service,
        'get_quote',
        lambda _ticker: type('Q', (), {'price': 100.0, 'ticker': 'AAPL', 'issuer': 'Apple', 'date': '2026-01-01'})(),
    )
    trade_service.execute_purchase_order(trade_setup['portfolio'].id, 'AAPL', 3)

    trade_service.liquidate_investment(trade_setup['portfolio'].id, 'AAPL', 2, 120.0)
    transactions = transaction_service.get_transactions_by_portfolio_id(trade_setup['portfolio'].id)

    assert len(transactions) == 2
    assert transactions[-1].transaction_type == 'SELL'
    assert transactions[-1].quantity == 2
