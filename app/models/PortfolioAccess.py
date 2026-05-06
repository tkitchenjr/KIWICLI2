from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db

if TYPE_CHECKING:
    # imports that are used only for type checking to avoid circular dependencies
    from app.models import Portfolio, User


class PortfolioAccess(db.Model):
    __tablename__ = 'portfolio_access'

    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey('portfolio.id'), primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String(30), ForeignKey('user.username'), primary_key=True, nullable=False)
    role: Mapped[str] = mapped_column(Enum('viewer', 'manager', name='portfolio_role_enum'), nullable=False)

    # Relationships
    portfolio: Mapped['Portfolio'] = relationship('Portfolio', back_populates='access_grants', lazy='selectin')
    user: Mapped['User'] = relationship('User', back_populates='access_grants', lazy='selectin')

    # this is needed because PyLance cannot infer the constructor signature from SQLAlchemy's Mapped class
    if TYPE_CHECKING:
        def __init__(
            self,
            *,
            portfolio_id: int,
            username: str,
            role: str,
        ) -> None: ...

    def __str__(self):
        return f"<PortfolioAccess: portfolio_id={self.portfolio_id}; username='{self.username}'; role='{self.role}'>"

    def __to_dict__(self):
        return {
            'portfolio_id': self.portfolio_id,
            'username': self.username,
            'role': self.role,
        }