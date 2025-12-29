from sqlmodel import SQLModel, Field
from datetime import datetime


class CurrencyRate(SQLModel, table=True):
    __tablename__ = "currency_rates"

    id: int | None = Field(default=None, primary_key=True)
    code: str  # USD, EUR, JPY
    value: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)
