from typing import List

from app.db import db
from app.models import Portfolio, User


class UnsupportedPortfolioOperationError(Exception):
    pass


class PortfolioOperationError(Exception):
    pass


def create_portfolio(name: str, description: str, username: str) -> int:
    if not name or not description or not username:
        raise UnsupportedPortfolioOperationError(
            f'Invalid input[name:{name}, description: {description}, username: {username}]. Please try again.'
        )
    user = db.session.query(User).filter_by(username=username).one_or_none()
    if not user:
        raise UnsupportedPortfolioOperationError(f'User with username {username} does not exist')
    portfolio = Portfolio(name=name, description=description, user=user)
    try:
        db.session.add(portfolio)
        db.session.flush()
        return portfolio.id
    except Exception as e:
        raise PortfolioOperationError(f'Failed to create portfolio due to error: {str(e)}')


def get_portfolios_by_user(user: User) -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).filter_by(owner=user.username).all()
        return portfolios
    except Exception as e:
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}')


def get_all_portfolios() -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).all()
        return portfolios
    except Exception as e:
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}')


def get_portfolio_by_id(portfolio_id: int) -> Portfolio | None:
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        return portfolio
    except Exception as e:
        raise PortfolioOperationError(f'Failed to retrieve portfolio due to error: {str(e)}')


def delete_portfolio(portfolio_id: int):
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        if not portfolio:
            raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist')
        db.session.delete(portfolio)
        db.session.flush()
    except Exception as e:
        raise e
