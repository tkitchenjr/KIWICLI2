from pydantic import BaseModel, Field
from typing import Optional

# Portfolio Request Schemas
class CreatePortfolioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Name of the portfolio")
    description: str = Field(min_length=1, max_length=255, description="Description of the portfolio")
    username: str = Field(min_length=1, max_length=30, description="Username of the portfolio owner")

# User Request Schemas
class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=30,description="Unique username for the user")
    password: str = Field(min_length=1, max_length=30, description="Password for the user")
    firstname: str = Field(min_length=1, max_length=30, description="First name of the user")
    lastname: str = Field(min_length=1, max_length=30, description="Last name of the user")
    balance: float = Field(ge=0, default=0.0, description="Initial balance for the user")

class UpdateBalanceRequest(BaseModel):
    username: str = Field(min_length=1, max_length=30, description="Username of the user to update balance for")
    new_balance: float = Field(ge=0, description="New balance for the user")

# Trade Request Schemas
class ExecutePurchaseOrderRequest(BaseModel):
    portfolio_id: int = Field(gt=0, description="iterative ID of the portfolio to execute the purchase order for")
    ticker: str = Field(min_length=1, max_length=100, description="Stock ticker symbol to purchase")
    quantity: int = Field(gt=0, description="Quantity of the stock to purchase")

class LiquidateInvestmentRequest(BaseModel):
    portfolio_id: int = Field(gt=0, description="iterative ID of the portfolio to liquidate the investment for")
    ticker: str = Field(min_length=1, max_length=100, description="Stock ticker symbol to liquidate")
    quantity: int = Field(gt=0, description="Quantity of the stock to liquidate")
    sale_price: Optional[float] = Field(default=None, gt=0, description="Sale price per unit for the stock being liquidated")