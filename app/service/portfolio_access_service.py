from typing import List, Optional

from app.db import db
from app.models.PortfolioAccess import PortfolioAccess
from app.models.Portfolio import Portfolio
from app.models.User import User


class PortfolioAccessError(Exception):
    pass

def grant_access(portfolio_id: int, username: str, role: str) -> None:
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    
    if not portfolio:
        raise PortfolioAccessError(f'Portfolio with id {portfolio_id} does not exist')
    
    user = db.session.query(User).filter_by(username=username).one_or_none()

    if not user:
        raise PortfolioAccessError(f'User with username {username} does not exist')
    
    try:
        existing_access = db.session.query(PortfolioAccess).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
        
        if existing_access:
            existing_access.role = role
        else:
            access = PortfolioAccess(portfolio_id=portfolio_id, username=username, role=role)
            db.session.add(access)
        db.session.flush()
        
    except Exception as e:
        raise PortfolioAccessError(f'Failed to grant {role} access to user {username} for portfolio {portfolio_id}: {str(e)}')


def revoke_access(portfolio_id: int, username: str) -> None:
    try:
        access = db.session.query(PortfolioAccess).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
        
        if not access:
            raise PortfolioAccessError(f'No access found for user {username} on portfolio {portfolio_id}')
        
        db.session.delete(access)
        db.session.flush()
        
    except PortfolioAccessError:
        raise
    except Exception as e:
        raise PortfolioAccessError(f'Failed to revoke access for user {username} on portfolio {portfolio_id}: {str(e)}')


def check_user_access(portfolio_id: int, username: str) -> Optional[str]:
    try:
        access = db.session.query(PortfolioAccess).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
        
        return access.role if access else None
        
    except Exception as e:
        raise PortfolioAccessError(f'Failed to check access for user {username} on portfolio {portfolio_id}: {str(e)}')


def get_access(portfolio_id: int) -> List[dict]:
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise PortfolioAccessError(f'Portfolio with id {portfolio_id} does not exist')
    
    try:
        access_list = db.session.query(PortfolioAccess).filter_by(portfolio_id=portfolio_id).all()
        
        return [access.__to_dict__() for access in access_list]
        
    except Exception as e:
        raise PortfolioAccessError(f'Failed to get access list for portfolio {portfolio_id}: {str(e)}')