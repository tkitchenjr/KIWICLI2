"""
End-to-End Verification Tests
Verifies backend and frontend logic without relying on test definitions.
Tests actual API flows: User sync → Portfolio CRUD → Trading → Transactions
"""

import pytest
import json
from app.models.User import User
from app.models.Portfolio import Portfolio
from app.models.Investment import Investment
from app.models.Transaction import Transaction
from app.service import user_service, portfolio_service, trade_service, transaction_service
from app.service.alpha_vantage_client import get_price_data
from app.db import db


class TestUserSync:
    """Verify user creation/sync logic."""
    
    def test_create_new_user_from_service(self, db_session):
        """Test user creation via service layer."""
        # Create user
        user_service.create_user('testuser1', 'password', 'Test', 'User', 10000.0)
        db_session.commit()
        
        # Retrieve and verify
        user = user_service.get_user_by_username('testuser1')
        assert user is not None
        assert user.username == 'testuser1'
        assert user.firstname == 'Test'
        assert user.lastname == 'User'
        assert user.balance == 10000.0
        print(f"✓ User created: {user}")

    def test_admin_user_protection(self, db_session):
        """Test that admin user cannot be deleted."""
        # Admin user should exist from fixtures
        admin = user_service.get_user_by_username('admin')
        assert admin is not None
        assert admin.balance == 1000.00
        
        # Attempt to delete should fail
        with pytest.raises(user_service.UnsupportedUserOperationError) as exc:
            user_service.delete_user('admin')
        assert "Cannot delete admin user" in str(exc.value)
        print("✓ Admin user protection works")


class TestPortfolioCRUD:
    """Verify portfolio creation, retrieval, and deletion."""
    
    def test_create_portfolio(self, db_session):
        """Test portfolio creation."""
        # Setup user
        user_service.create_user('portfoliouser', 'pwd', 'Portfolio', 'User', 5000.0)
        db_session.commit()
        user = user_service.get_user_by_username('portfoliouser')
        
        # Create portfolio
        portfolio = portfolio_service.create_portfolio(
            user_id=user.username,
            name='Test Portfolio',
            description='A test portfolio'
        )
        db_session.commit()
        
        assert portfolio.name == 'Test Portfolio'
        assert portfolio.description == 'A test portfolio'
        assert portfolio.user.username == 'portfoliouser'
        print(f"✓ Portfolio created: {portfolio.name}")

    def test_get_portfolios_by_user(self, db_session):
        """Test retrieving user's portfolios."""
        # Setup
        user_service.create_user('portfoliouser2', 'pwd', 'Portfolio', 'User2', 5000.0)
        db_session.commit()
        user = user_service.get_user_by_username('portfoliouser2')
        
        # Create multiple portfolios
        p1 = portfolio_service.create_portfolio(user.username, 'Portfolio 1', 'Desc 1')
        p2 = portfolio_service.create_portfolio(user.username, 'Portfolio 2', 'Desc 2')
        db_session.commit()
        
        # Retrieve
        portfolios = portfolio_service.get_portfolios_by_user(user)
        assert len(portfolios) == 2
        assert any(p.name == 'Portfolio 1' for p in portfolios)
        assert any(p.name == 'Portfolio 2' for p in portfolios)
        print(f"✓ Retrieved {len(portfolios)} portfolios for user")

    def test_delete_portfolio(self, db_session):
        """Test portfolio deletion."""
        # Setup
        user_service.create_user('portfoliouser3', 'pwd', 'Portfolio', 'User3', 5000.0)
        db_session.commit()
        user = user_service.get_user_by_username('portfoliouser3')
        
        # Create and delete
        portfolio = portfolio_service.create_portfolio(user.username, 'To Delete', 'Will delete')
        db_session.commit()
        portfolio_id = portfolio.id
        
        portfolio_service.delete_portfolio(portfolio_id)
        db_session.commit()
        
        # Verify deletion
        deleted = portfolio_service.get_portfolio_by_id(portfolio_id)
        assert deleted is None
        print("✓ Portfolio deleted successfully")


class TestTrading:
    """Verify buy/sell trading logic and transaction logging."""
    
    def test_buy_order_execution(self, db_session):
        """Test executing a buy order."""
        # Setup
        user_service.create_user('trader1', 'pwd', 'Trader', 'One', 10000.0)
        db_session.commit()
        user = user_service.get_user_by_username('trader1')
        
        portfolio = portfolio_service.create_portfolio(user.username, 'Trading Port', 'For trading')
        db_session.commit()
        
        initial_balance = user.balance
        
        # Execute buy order (AAPL, 10 shares)
        trade_service.execute_purchase_order(
            portfolio_id=portfolio.id,
            ticker='AAPL',
            quantity=10
        )
        db_session.commit()
        
        # Verify
        investments = portfolio.investments
        assert len(investments) == 1
        assert investments[0].ticker == 'AAPL'
        assert investments[0].quantity == 10
        
        # Check balance was deducted
        user_refreshed = user_service.get_user_by_username('trader1')
        assert user_refreshed.balance < initial_balance
        print(f"✓ Buy order executed: 10 AAPL @ {investments[0].purchase_price}")

    def test_sell_order_execution(self, db_session):
        """Test executing a sell order."""
        # Setup with buy first
        user_service.create_user('trader2', 'pwd', 'Trader', 'Two', 10000.0)
        db_session.commit()
        user = user_service.get_user_by_username('trader2')
        
        portfolio = portfolio_service.create_portfolio(user.username, 'Sell Port', 'For selling')
        db_session.commit()
        
        # Buy first
        trade_service.execute_purchase_order(portfolio.id, 'AAPL', 5)
        db_session.commit()
        
        balance_after_buy = user_service.get_user_by_username('trader2').balance
        
        # Sell
        trade_service.liquidate_investment(
            portfolio_id=portfolio.id,
            ticker='AAPL',
            quantity=3,
            sale_price=150.0
        )
        db_session.commit()
        
        # Verify
        portfolio_refreshed = portfolio_service.get_portfolio_by_id(portfolio.id)
        investments = portfolio_refreshed.investments
        assert investments[0].quantity == 2  # 5 - 3 = 2
        
        # Check balance was credited
        balance_after_sell = user_service.get_user_by_username('trader2').balance
        assert balance_after_sell > balance_after_buy
        print(f"✓ Sell order executed: 3 AAPL sold @ $150")

    def test_sell_validation_prevents_overselling(self, db_session):
        """Test that selling more than owned is prevented."""
        # Setup
        user_service.create_user('trader3', 'pwd', 'Trader', 'Three', 10000.0)
        db_session.commit()
        user = user_service.get_user_by_username('trader3')
        
        portfolio = portfolio_service.create_portfolio(user.username, 'Validation Port', 'Test validation')
        db_session.commit()
        
        # Buy 5 shares
        trade_service.execute_purchase_order(portfolio.id, 'AAPL', 5)
        db_session.commit()
        
        # Try to sell 10 (should fail)
        with pytest.raises(Exception) as exc:
            trade_service.liquidate_investment(
                portfolio_id=portfolio.id,
                ticker='AAPL',
                quantity=10,
                sale_price=150.0
            )
        print(f"✓ Oversell prevented: {exc.value}")

    def test_allow_negative_balance_on_buy(self, db_session):
        """Test that buy orders allow negative balance (margin-like behavior)."""
        # Setup with small balance
        user_service.create_user('trader4', 'pwd', 'Trader', 'Four', 100.0)
        db_session.commit()
        user = user_service.get_user_by_username('trader4')
        
        portfolio = portfolio_service.create_portfolio(user.username, 'Margin Port', 'Allow negative')
        db_session.commit()
        
        # Buy expensive stock (will go negative)
        trade_service.execute_purchase_order(portfolio.id, 'AAPL', 100)  # Expensive!
        db_session.commit()
        
        # Verify negative balance is allowed
        user_refreshed = user_service.get_user_by_username('trader4')
        assert user_refreshed.balance < 0
        print(f"✓ Negative balance allowed: ${user_refreshed.balance}")


class TestTransactions:
    """Verify transaction logging and retrieval."""
    
    def test_transaction_created_on_buy(self, db_session):
        """Test that BUY transaction is logged."""
        # Setup
        user_service.create_user('txnuser1', 'pwd', 'Txn', 'User1', 5000.0)
        db_session.commit()
        user = user_service.get_user_by_username('txnuser1')
        
        portfolio = portfolio_service.create_portfolio(user.username, 'Txn Port', 'For txns')
        db_session.commit()
        
        # Buy
        trade_service.execute_purchase_order(portfolio.id, 'AAPL', 5)
        db_session.commit()
        
        # Check transaction created
        transactions = transaction_service.get_transactions_by_portfolio_id(portfolio.id)
        assert len(transactions) == 1
        assert transactions[0].transaction_type == 'BUY'
        assert transactions[0].ticker == 'AAPL'
        assert transactions[0].quantity == 5
        print(f"✓ BUY transaction logged: {transactions[0].transaction_type}")

    def test_transaction_created_on_sell(self, db_session):
        """Test that SELL transaction is logged."""
        # Setup with buy
        user_service.create_user('txnuser2', 'pwd', 'Txn', 'User2', 5000.0)
        db_session.commit()
        user = user_service.get_user_by_username('txnuser2')
        
        portfolio = portfolio_service.create_portfolio(user.username, 'Txn Port 2', 'For txns')
        db_session.commit()
        
        # Buy then sell
        trade_service.execute_purchase_order(portfolio.id, 'AAPL', 5)
        db_session.commit()
        
        trade_service.liquidate_investment(portfolio.id, 'AAPL', 2, 150.0)
        db_session.commit()
        
        # Check both transactions
        transactions = transaction_service.get_transactions_by_portfolio_id(portfolio.id)
        assert len(transactions) == 2
        assert transactions[0].transaction_type == 'BUY'
        assert transactions[1].transaction_type == 'SELL'
        print(f"✓ SELL transaction logged: {transactions[1].transaction_type}")

    def test_get_transactions_by_user(self, db_session):
        """Test retrieving transactions for a user."""
        # Setup
        user_service.create_user('txnuser3', 'pwd', 'Txn', 'User3', 5000.0)
        db_session.commit()
        user = user_service.get_user_by_username('txnuser3')
        
        # Create 2 portfolios and trade
        p1 = portfolio_service.create_portfolio(user.username, 'Port 1', 'P1')
        p2 = portfolio_service.create_portfolio(user.username, 'Port 2', 'P2')
        db_session.commit()
        
        trade_service.execute_purchase_order(p1.id, 'AAPL', 3)
        trade_service.execute_purchase_order(p2.id, 'GOOGL', 2)
        db_session.commit()
        
        # Get user transactions
        transactions = transaction_service.get_transactions_by_user(user.username)
        assert len(transactions) == 2
        print(f"✓ Retrieved {len(transactions)} transactions across portfolios")


class TestDataPersistence:
    """Verify database persistence (SQLite stores data)."""
    
    def test_portfolio_data_persists(self, db_session):
        """Test that portfolio data survives session commits."""
        user_service.create_user('persistuser', 'pwd', 'Persist', 'User', 5000.0)
        db_session.commit()
        user = user_service.get_user_by_username('persistuser')
        
        portfolio = portfolio_service.create_portfolio(user.username, 'Persist Port', 'Test')
        db_session.commit()
        
        portfolio_id = portfolio.id
        
        # Retrieve in new query
        retrieved = portfolio_service.get_portfolio_by_id(portfolio_id)
        assert retrieved.name == 'Persist Port'
        print(f"✓ Portfolio persisted to database")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
